"""TASK-135: the upload body guard (SR-013 AC 6, ADR-0021).

Driven at the ASGI level so the test controls how the body arrives and counts the bytes the
application pulled: the guard must stop reading at the maximum plus one 64 KiB chunk.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routers.attachments import _get_attachment_service
from app.attachments.service import AttachmentService
from app.core.body_limit import MULTIPART_ALLOWANCE, AttachmentBodyLimitMiddleware
from app.db.repositories.session import get_db
from app.main import create_app

MAX = 1 << 20  # attachment_max_bytes override for these tests
CHUNK = 65536
UPLOAD = f"/api/v1/clinical-entries/{uuid.uuid4()}/attachments"


@pytest.fixture(autouse=True)
def _small_maximum(monkeypatch):
    monkeypatch.setenv("ATTACHMENT_MAX_BYTES", str(MAX))


async def _run(app, path, *, headers, chunks, method="POST"):
    """Call ``app`` with a body made of ``chunks``; return (messages sent, bytes pulled)."""
    sent: list[dict] = []
    pulled = 0
    queue = iter(chunks)

    async def receive():
        nonlocal pulled
        try:
            chunk = next(queue)
        except StopIteration:
            return {"type": "http.disconnect"}
        pulled += len(chunk)
        return {"type": "http.request", "body": chunk, "more_body": True}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": headers,
        "state": {},
    }
    await app(scope, receive, send)
    return sent, pulled


def _problem(sent):
    start = next(m for m in sent if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body")
    return start, json.loads(body)


async def _drain_app(scope, receive, send):
    """An application that reads the whole body, as a form parser would."""
    while (await receive())["type"] == "http.request":
        pass
    await send({"type": "http.response.start", "status": 201, "headers": []})
    await send({"type": "http.response.body", "body": b""})


async def test_upload_over_limit_refused_within_limit_plus_one_chunk():
    """SR-013 AC 6: a body of max + 10 MiB is refused after at most max + 64 KiB + one chunk."""
    guard = AttachmentBodyLimitMiddleware(_drain_app)
    chunks = (bytes(CHUNK) for _ in range((MAX + (10 << 20)) // CHUNK))
    sent, pulled = await _run(guard, UPLOAD, headers=[], chunks=chunks)

    start, body = _problem(sent)
    assert start["status"] == 400
    assert (b"content-type", b"application/problem+json") in start["headers"]
    assert body["type"].endswith("/validation-error")
    assert body["instance"] == UPLOAD
    assert pulled <= MAX + MULTIPART_ALLOWANCE + CHUNK


async def test_upload_content_length_over_limit_refused_before_body():
    """SR-013 AC 6: a declared length over the bound is refused without reading the body."""
    guard = AttachmentBodyLimitMiddleware(_drain_app)
    declared = str(MAX + MULTIPART_ALLOWANCE + 1).encode()
    sent, pulled = await _run(
        guard, UPLOAD, headers=[(b"content-length", declared)], chunks=iter([bytes(CHUNK)])
    )
    start, body = _problem(sent)
    assert start["status"] == 400
    assert body["type"].endswith("/validation-error")
    assert pulled == 0


async def test_upload_at_the_bound_passes_through():
    """A body of exactly the maximum plus the allowance reaches the application."""
    guard = AttachmentBodyLimitMiddleware(_drain_app)
    chunks = iter([bytes(CHUNK)] * ((MAX + MULTIPART_ALLOWANCE) // CHUNK))
    sent, _ = await _run(
        guard,
        UPLOAD,
        headers=[(b"content-length", str(MAX + MULTIPART_ALLOWANCE).encode())],
        chunks=chunks,
    )
    assert sent[0]["status"] == 201


async def test_other_routes_and_methods_are_not_limited():
    guard = AttachmentBodyLimitMiddleware(_drain_app)
    big = [bytes(CHUNK)] * ((MAX * 2) // CHUNK)
    sent, _ = await _run(guard, "/api/v1/clinical-entries", headers=[], chunks=iter(big))
    assert sent[0]["status"] == 201
    sent, _ = await _run(guard, UPLOAD, headers=[], chunks=iter(big), method="GET")
    assert sent[0]["status"] == 201


def test_full_app_answers_the_same_problem_for_an_over_limit_upload():
    """Through the real app: Content-Length over the bound gives today's 400 problem, with the
    security headers, and the service is never called."""
    app = create_app()
    svc = MagicMock(spec=AttachmentService)
    app.dependency_overrides[_get_attachment_service] = lambda: svc
    app.dependency_overrides[get_current_user] = lambda: MagicMock()
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        UPLOAD,
        files={"file": ("big.bin", bytes(MAX + 2 * MULTIPART_ALLOWANCE), "application/pdf")},
        headers={"X-CSRF-Token": "tok"},
        cookies={"medhub_csrf": "tok"},
    )
    assert resp.status_code == 400
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.json()["type"].endswith("/validation-error")
    svc.store.assert_not_called()


async def test_chunked_over_limit_upload_through_the_full_app_is_refused_by_the_count():
    """SR-013 AC 6: no Content-Length, so only the byte count can refuse; through the real app
    (form parsing and FastAPI's body handling included) the answer is the 400 problem, the service
    is never called, and the bytes pulled stay within maximum + allowance + one received chunk."""
    app = create_app()
    svc = MagicMock(spec=AttachmentService)
    app.dependency_overrides[_get_attachment_service] = lambda: svc
    app.dependency_overrides[get_current_user] = lambda: MagicMock()
    app.dependency_overrides[get_db] = lambda: MagicMock()

    boundary = b"b0undary"
    head = (
        b"--" + boundary + b"\r\n"
        b'Content-Disposition: form-data; name="file"; filename="big.bin"\r\n'
        b"Content-Type: application/octet-stream\r\n\r\n"
    )
    total = MAX + (5 << 20)
    chunks = [head] + [bytes(CHUNK)] * (total // CHUNK) + [b"\r\n--" + boundary + b"--\r\n"]
    headers = [
        (b"content-type", b"multipart/form-data; boundary=" + boundary),
        (b"cookie", b"medhub_csrf=tok"),
        (b"x-csrf-token", b"tok"),
    ]
    sent, pulled = await _run(app, UPLOAD, headers=headers, chunks=chunks)

    start, body = _problem(sent)
    assert start["status"] == 400
    assert (b"content-type", b"application/problem+json") in start["headers"]
    assert body["type"].endswith("/validation-error")
    assert pulled <= MAX + MULTIPART_ALLOWANCE + CHUNK + len(head)
    svc.store.assert_not_called()


def test_upload_above_one_mib_reaches_the_service_as_a_file_already_on_disk():
    """SR-013 AC 6: the memory bound rests on Starlette spooling a file part larger than its
    1 MiB `spool_max_size` to a temporary file (SOUP-003); the object `store()` receives has been
    rolled over to disk, not held in memory."""
    app = create_app()
    seen: dict[str, object] = {}

    def store(actor, entry_id, filename, content_type, fileobj):
        seen["rolled"] = fileobj._rolled
        seen["size"] = fileobj.seek(0, 2)
        fileobj.seek(0)
        return SimpleNamespace(
            id=uuid.uuid4(),
            clinical_entry_id=entry_id,
            patient_id=uuid.uuid4(),
            filename=filename,
            content_type=content_type,
            size=seen["size"],
            checksum="abc",
            created_at=datetime.now(UTC),
        )

    svc = MagicMock(spec=AttachmentService)
    svc.store.side_effect = store
    app.dependency_overrides[_get_attachment_service] = lambda: svc
    app.dependency_overrides[get_current_user] = lambda: MagicMock()
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app, raise_server_exceptions=False)
    size = (1 << 20) + 1024  # above the 1 MiB spool threshold, within the test's bound
    resp = client.post(
        UPLOAD,
        files={"file": ("a.bin", bytes(size), "application/octet-stream")},
        headers={"X-CSRF-Token": "tok"},
        cookies={"medhub_csrf": "tok"},
    )
    assert resp.status_code == 201
    assert seen["size"] == size
    assert seen["rolled"] is True


def test_full_app_accepts_an_upload_below_the_limit():
    """The guard does not disturb a normal upload; the service gets the spooled file."""
    app = create_app()
    svc = MagicMock(spec=AttachmentService)
    svc.store.return_value = SimpleNamespace(
        id=uuid.uuid4(),
        clinical_entry_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        filename="a.pdf",
        content_type="application/pdf",
        size=3,
        checksum="abc",
        created_at=datetime.now(UTC),
    )
    app.dependency_overrides[_get_attachment_service] = lambda: svc
    app.dependency_overrides[get_current_user] = lambda: MagicMock()
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post(
        UPLOAD,
        files={"file": ("a.pdf", b"PDF", "application/pdf")},
        headers={"X-CSRF-Token": "tok"},
        cookies={"medhub_csrf": "tok"},
    )
    assert resp.status_code == 201
    fileobj = svc.store.call_args[0][4]
    assert hasattr(fileobj, "read") and hasattr(fileobj, "seek")
