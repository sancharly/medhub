"""TASK-217: the bounded two-pass download that serves only verified bytes.

SR-013 AC 5 (no unverified byte is served, RISK-012) and AC 6, download half (memory does not
grow with the object, PRB-008, RISK-007); ADR-0021, CR-006 D-10. TC-007.13 in TS-007.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import tracemalloc
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.errors import AttachmentIntegrityError, ValidationProblem
from app.api.routers.attachments import _get_attachment_service
from app.attachments.service import AttachmentService
from app.audit.service import AuditService
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.attachment import Attachment
from app.db.repositories.session import get_db
from app.main import create_app
from tests.attachments.fake_object_store import FakeObjectStore

ORIGINAL = os.urandom(300_000)  # several 64 KiB chunks, not a multiple of the chunk size


def _actor() -> Account:
    acct = MagicMock(spec=Account)
    acct.id = uuid.uuid4()
    acct.user_type = UserType.DOCTOR
    acct.status = AccountStatus.ACTIVE
    return acct


def _attachment(data: bytes = ORIGINAL) -> Attachment:
    return Attachment(
        id=uuid.uuid4(),
        clinical_entry_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        filename="scan.pdf",
        content_type="application/pdf",
        size=len(data),
        storage_key="attachments/scan.pdf",
        checksum=hashlib.sha256(data).hexdigest(),
    )


def _service(attachment: Attachment, store, audit_repo=None) -> AttachmentService:
    repo = MagicMock()
    repo.get.return_value = attachment
    return AttachmentService(
        repo,
        MagicMock(),
        AuditService(audit_repo or MagicMock()),
        MagicMock(spec=AuthorizationService),
        store,
    )


def _outcomes(audit_repo) -> list[str]:
    rows = [c.args[0] for c in audit_repo.add.call_args_list]
    rows += [c.args[0] for c in audit_repo.add_independent.call_args_list]
    return [r.outcome.value for r in rows]


def _client(svc: AttachmentService, *, raise_server_exceptions: bool) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: _actor()
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[_get_attachment_service] = lambda: svc
    return TestClient(app, raise_server_exceptions=raise_server_exceptions)


@pytest.mark.parametrize("mib", [20, 60])
def test_download_memory_bounded(mib: int) -> None:
    """SR-013 AC 6 (TC-007.13): the peak allocation while consuming the download does not grow
    with the object; 20 MiB and 60 MiB both stay under 4 MiB."""
    data = bytes(mib << 20)
    attachment = _attachment(data)
    svc = _service(attachment, FakeObjectStore(data))

    tracemalloc.start()
    try:
        chunks, _, _, size = svc.open_stream(_actor(), attachment.id)
        served = 0
        for chunk in chunks:
            served += len(chunk)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert served == size == len(data)
    assert peak < 4 << 20


def test_download_serves_identical_bytes_and_success_row_once() -> None:
    """SR-013 AC 5: an unmodified object is served as is, with one SUCCESS row and no FAILURE."""
    attachment = _attachment()
    audit_repo = MagicMock()
    svc = _service(attachment, FakeObjectStore(ORIGINAL), audit_repo)

    chunks, content_type, filename, size = svc.open_stream(_actor(), attachment.id)

    assert b"".join(chunks) == ORIGINAL
    assert (content_type, filename, size) == ("application/pdf", "scan.pdf", len(ORIGINAL))
    assert _outcomes(audit_repo) == ["SUCCESS"]


def test_download_reads_object_twice_second_conditional() -> None:
    """SR-013 AC 5 (D-10): pass 2 carries IfMatch equal to the ETag pass 1 returned."""
    attachment = _attachment()
    store = FakeObjectStore(ORIGINAL)
    svc = _service(attachment, store)

    chunks, *_ = svc.open_stream(_actor(), attachment.id)
    b"".join(chunks)

    assert store.calls == [("get_object_stream", None), ("get_object_stream", store.etag)]


def test_download_object_replaced_between_passes_gives_502_and_failure_row() -> None:
    """SR-013 AC 5 (RISK-012): the object is replaced after pass 1; the store answers 412 on
    pass 2, so the response is the 502 problem with no content, one FAILURE row, no SUCCESS."""
    attachment = _attachment()
    audit_repo = MagicMock()
    store = FakeObjectStore(ORIGINAL, replace_after_read=b"planted" * 1000)
    client = _client(_service(attachment, store, audit_repo), raise_server_exceptions=False)

    resp = client.get(f"/api/v1/attachments/{attachment.id}")

    assert resp.status_code == 502
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.json()["type"].endswith("/attachment-integrity-failure")
    assert b"planted" not in resp.content
    assert ORIGINAL[:64] not in resp.content
    assert _outcomes(audit_repo) == ["FAILURE"]


def test_download_mismatch_in_first_pass_gives_502_without_second_read() -> None:
    """SR-013 AC 5: a substituted object is refused after pass 1; pass 2 is never opened."""
    attachment = _attachment()
    audit_repo = MagicMock()
    store = FakeObjectStore(b"planted" * 1000)
    client = _client(_service(attachment, store, audit_repo), raise_server_exceptions=False)

    resp = client.get(f"/api/v1/attachments/{attachment.id}")

    assert resp.status_code == 502
    assert len(store.calls) == 1
    assert _outcomes(audit_repo) == ["FAILURE"]


def test_download_mismatch_in_second_pass_aborts() -> None:
    """SR-013 AC 5: pass 2 yields different bytes. The transfer is aborted (the exception ends
    the response before it is completed) and a FAILURE row is recorded."""
    attachment = _attachment()
    audit_repo = MagicMock()
    changed = bytearray(ORIGINAL)
    changed[-1] ^= 1
    store = FakeObjectStore(ORIGINAL, second_read_bytes=bytes(changed))
    client = _client(_service(attachment, store, audit_repo), raise_server_exceptions=True)

    # The response had started, so the problem handler cannot answer: Starlette raises, which
    # makes the server drop the connection with the chunked body never completed.
    with pytest.raises(RuntimeError, match="response already started") as excinfo:
        client.get(f"/api/v1/attachments/{attachment.id}")

    assert isinstance(excinfo.value.__cause__, AttachmentIntegrityError)
    assert "FAILURE" in _outcomes(audit_repo)


async def _asgi_get(app, path: str) -> tuple[list[dict], BaseException | None]:
    """Drive ``app`` at ASGI level; return the messages the client would receive and any
    exception that ended the call (the server drops the connection on one)."""
    sent: list[dict] = []
    served = False
    never = asyncio.Event()

    async def receive():
        nonlocal served
        if not served:
            served = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await never.wait()  # the client stays connected
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "state": {},
    }
    try:
        await app(scope, receive, send)
    except BaseException as exc:  # noqa: BLE001
        return sent, exc
    return sent, None


def _received(sent: list[dict]) -> tuple[bytes, int, bool]:
    start = next(m for m in sent if m["type"] == "http.response.start")
    declared = int(dict(start["headers"])[b"content-length"])
    bodies = [m for m in sent if m["type"] == "http.response.body"]
    completed = any(not m.get("more_body", False) for m in bodies)
    return b"".join(m.get("body", b"") for m in bodies), declared, completed


def _asgi_app(svc: AttachmentService):
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: _actor()
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[_get_attachment_service] = lambda: svc
    return app


def _flip_last(data: bytes) -> bytes:
    return data[:-1] + bytes([data[-1] ^ 1])


_CHUNK = 65536
_MULTIPLE = os.urandom(4 * _CHUNK)  # stored size an exact multiple of the chunk size
_SINGLE = os.urandom(1000)  # one chunk
_ONE_CHUNK = os.urandom(_CHUNK)  # exactly one full chunk

# (id, stored bytes, what pass 2 returns). Pass 1 always returns the stored bytes.
TAMPER_CASES = [
    ("shorter_by_one_byte", ORIGINAL, ORIGINAL[:-1]),
    ("shorter_by_whole_chunks", ORIGINAL, ORIGINAL[: 2 * _CHUNK]),
    ("empty_instead_of_data", ORIGINAL, b""),
    ("same_length_last_byte_changed", ORIGINAL, _flip_last(ORIGINAL)),
    ("same_length_first_byte_changed", ORIGINAL, bytes([ORIGINAL[0] ^ 1]) + ORIGINAL[1:]),
    ("longer_by_a_few_bytes", ORIGINAL, ORIGINAL + b"extra"),
    ("longer_by_whole_chunks", ORIGINAL, ORIGINAL + os.urandom(2 * _CHUNK)),
    ("multiple_of_chunk_same_length_changed", _MULTIPLE, _flip_last(_MULTIPLE)),
    ("multiple_of_chunk_shorter", _MULTIPLE, _MULTIPLE[:-1]),
    ("multiple_of_chunk_longer_with_prefix", _MULTIPLE, _MULTIPLE + os.urandom(100_000)),
    ("multiple_of_chunk_longer_random", _MULTIPLE, os.urandom(len(_MULTIPLE) + 100_000)),
    ("single_chunk_changed", _SINGLE, _flip_last(_SINGLE)),
    ("single_chunk_longer", _SINGLE, _SINGLE + os.urandom(1000)),
    ("single_chunk_shorter", _SINGLE, _SINGLE[:-1]),
    ("exactly_one_full_chunk_changed", _ONE_CHUNK, _flip_last(_ONE_CHUNK)),
    ("exactly_one_full_chunk_longer", _ONE_CHUNK, _ONE_CHUNK + os.urandom(_CHUNK)),
    ("size_zero_gets_data", b"", b"x"),
    ("size_zero_gets_a_full_chunk", b"", os.urandom(_CHUNK)),
]
_CASE_PARAMS = [pytest.param(s, p, id=i) for i, s, p in TAMPER_CASES]
_CONTROL_PARAMS = [
    pytest.param(d, id=i)
    for i, d in [
        ("untouched", ORIGINAL),
        ("untouched_multiple_of_chunk", _MULTIPLE),
        ("untouched_single_chunk", _SINGLE),
        ("untouched_one_full_chunk", _ONE_CHUNK),
        ("untouched_size_zero", b""),
    ]
]


@pytest.mark.parametrize(("stored", "pass_two"), _CASE_PARAMS)
async def test_client_never_receives_a_complete_response_when_pass_two_is_tampered(
    stored: bytes, pass_two: bytes
) -> None:
    """SR-013 AC 5: what the client actually receives, for every tamper boundary (shorter, same
    length, longer, size 0, exact multiple of the chunk size, single chunk). The response is
    short of its Content-Length and ends in an error, whatever the stored size."""
    attachment = _attachment(stored)
    store = FakeObjectStore(stored, second_read_bytes=pass_two)
    audit_repo = MagicMock()
    app = _asgi_app(_service(attachment, store, audit_repo))

    sent, error = await _asgi_get(app, f"/api/v1/attachments/{attachment.id}")

    body, declared, _ = _received(sent)
    # "Completed" is not asserted: the BaseHTTPMiddleware layers close the ASGI stream with an
    # empty final message; the server then fails the declared Content-Length (see the uvicorn test).
    assert declared == len(stored)
    # Size 0: the true, empty content is complete and no byte was sent.
    assert len(body) < declared or declared == 0
    assert error is not None
    assert "FAILURE" in _outcomes(audit_repo)


@pytest.mark.parametrize("data", _CONTROL_PARAMS)
async def test_client_receives_the_whole_verified_object_when_pass_two_matches(data: bytes) -> None:
    """SR-013 AC 5: the same harness on an untouched object gets every byte and a completed body,
    at every size boundary."""
    attachment = _attachment(data)
    app = _asgi_app(_service(attachment, FakeObjectStore(data)))

    sent, error = await _asgi_get(app, f"/api/v1/attachments/{attachment.id}")

    body, declared, completed = _received(sent)
    assert error is None
    assert completed
    assert body == data
    assert declared == len(data)


def _serve(app):
    """Run ``app`` on a real uvicorn server in a thread; return (server, thread, port)."""
    import socket  # noqa: PLC0415
    import threading  # noqa: PLC0415
    import time  # noqa: PLC0415

    import uvicorn  # noqa: PLC0415

    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="critical", lifespan="off")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    return server, thread, port


def _get_over_http(app, attachment_id) -> tuple[bytes | None, Exception | None]:
    import httpx  # noqa: PLC0415

    server, thread, port = _serve(app)
    try:
        with httpx.Client(timeout=10) as client:
            try:
                resp = client.get(f"http://127.0.0.1:{port}/api/v1/attachments/{attachment_id}")
            except httpx.TransportError as exc:
                return None, exc
            return resp.content, None
    finally:
        server.should_exit = True
        thread.join(timeout=5)


@pytest.mark.parametrize(("stored", "pass_two"), _CASE_PARAMS)
def test_over_http_a_tampered_second_pass_is_a_failed_transfer_not_a_complete_200(
    stored: bytes, pass_two: bytes
) -> None:
    """SR-013 AC 5: through a real uvicorn server and an HTTP client, a second pass that differs
    (every boundary: shorter, same length, longer, size 0, exact multiple of the chunk size, single
    chunk) gives a transport error (short body against Content-Length), never a complete 200 whose
    body is not the stored object. For size 0 the empty body is the true content."""
    attachment = _attachment(stored)
    store = FakeObjectStore(stored, second_read_bytes=pass_two)
    app = _asgi_app(_service(attachment, store))

    content, error = _get_over_http(app, attachment.id)

    assert error is not None or content == stored
    if stored:
        assert content is None


@pytest.mark.parametrize("data", _CONTROL_PARAMS)
def test_over_http_an_untouched_object_downloads_completely(data: bytes) -> None:
    """SR-013 AC 5: the control for the test above, same server and client."""
    attachment = _attachment(data)
    app = _asgi_app(_service(attachment, FakeObjectStore(data)))

    content, error = _get_over_http(app, attachment.id)

    assert error is None
    assert content == data


def test_pass_two_stream_is_closed_when_the_client_goes_away() -> None:
    """The second-read stream is closed by the generator's own ``finally``, not by collection."""
    attachment = _attachment()
    closed = []

    class _Store(FakeObjectStore):
        def get_object_stream(self, key, if_match=None):
            chunks, etag = super().get_object_stream(key, if_match)
            if if_match is None:
                return chunks, etag

            def _watched():
                try:
                    yield from chunks
                finally:
                    closed.append(True)

            return _watched(), etag

    svc = _service(attachment, _Store(ORIGINAL))
    stream, *_ = svc.open_stream(_actor(), attachment.id)
    next(stream)
    stream.close()  # what a server does when the client disconnects

    assert closed == [True]


def test_download_sets_content_length_from_the_stored_size() -> None:
    """SR-013 AC 6: the response declares the size, so a short transfer is detectable."""
    attachment = _attachment()
    client = _client(_service(attachment, FakeObjectStore(ORIGINAL)), raise_server_exceptions=True)

    resp = client.get(f"/api/v1/attachments/{attachment.id}")

    assert resp.status_code == 200
    assert resp.headers["content-length"] == str(len(ORIGINAL))
    assert resp.content == ORIGINAL


def test_open_max_bytes_refuses_before_read() -> None:
    """SR-017 AC 6 (interface for TASK-218): an attachment stored larger than max_bytes is
    refused before any read of the object store."""
    attachment = _attachment()
    store = FakeObjectStore(ORIGINAL)
    svc = _service(attachment, store)

    with pytest.raises(ValidationProblem):
        svc.open(_actor(), attachment.id, max_bytes=len(ORIGINAL) - 1)

    assert store.calls == []


def test_open_max_bytes_at_the_bound_reads() -> None:
    attachment = _attachment()
    svc = _service(attachment, FakeObjectStore(ORIGINAL))

    data, *_ = svc.open(_actor(), attachment.id, max_bytes=len(ORIGINAL))

    assert data == ORIGINAL
