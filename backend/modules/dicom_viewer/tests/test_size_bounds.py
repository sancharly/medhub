"""TASK-218: stored-size and declared-decoded-size bounds before any pixel decode (PRB-006).

SR-017 AC 6 and SR-026 AC 3; TC-019.1 to TC-019.4 in TS-019. NumPy is not installed (SOUP-015,
PRB-048), so the decode itself is stubbed; the bounds and the error path are what is tested.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import numpy as np
import pydicom
from dicom_viewer.router import build_router
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from app.api.deps import get_current_user, get_platform_services
from app.api.errors import register_error_handlers
from app.attachments.service import AttachmentService
from app.audit.service import AuditService
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.attachment import Attachment
from app.modules.platform_services import PlatformServices
from tests.fixtures import build_compressed, build_dicom, build_short_pixel_data

# The module's own ``tests`` package shadows backend/tests, so the shared fake store (TASK-217)
# is loaded by path.
_spec = importlib.util.spec_from_file_location(
    "fake_object_store",
    Path(__file__).parents[3] / "tests" / "attachments" / "fake_object_store.py",
)
assert _spec is not None and _spec.loader is not None
_fake_store = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fake_store)
FakeObjectStore = _fake_store.FakeObjectStore

MAX_STORED = 157286400  # 150 MiB
MAX_DECODED = 1073741824  # 1 GiB


def _dicom(rows: int, columns: int, *, frames: int = 1, bits: int = 16, pixel_bytes: int = 0):
    """A synthetic dataset: the header declares the size, ``pixel_bytes`` of OB data follow."""
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.7"
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds = Dataset()
    ds.file_meta = meta
    ds.Rows = rows
    ds.Columns = columns
    ds.BitsAllocated = bits
    ds.SamplesPerPixel = 1
    if frames != 1:
        ds.NumberOfFrames = frames
    if pixel_bytes >= 0:
        ds.add_new(0x7FE00010, "OB", bytes(pixel_bytes))
    buf = io.BytesIO()
    pydicom.dcmwrite(buf, ds, enforce_file_format=True)
    return buf.getvalue()


def _padded_to(total: int, rows: int, columns: int, frames: int) -> bytes:
    base = _dicom(rows, columns, frames=frames, pixel_bytes=0)
    return _dicom(rows, columns, frames=frames, pixel_bytes=total - len(base))


class _Frame:
    """Stands in for the NumPy array of a decode (or of one frame of it).

    ``shape`` is the array the header describes, since the code checks it against the header; the
    bytes are never produced.
    """

    def __init__(self, shape: tuple[int, ...] = (1, 1), itemsize: int = 1) -> None:
        self.shape = shape
        self.ndim = len(shape)
        self.dtype = np.dtype(f"u{itemsize}")
        self.nbytes = int(np.prod(shape)) * itemsize

    def __getitem__(self, index: int) -> _Frame:
        return _Frame(self.shape[1:], self.dtype.itemsize)

    def astype(self, dtype: np.dtype, copy: bool = True) -> _Frame:
        return self

    def tobytes(self) -> bytes:
        return b"FRAME"


@contextmanager
def _pixel_array(value=None, error: Exception | None = None) -> Iterator[PropertyMock]:
    mock = PropertyMock(return_value=value, side_effect=error)
    with patch.object(Dataset, "pixel_array", mock):
        yield mock


def _attachment(data: bytes, size: int | None = None) -> Attachment:
    return Attachment(
        id=uuid.uuid4(),
        clinical_entry_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        filename="study.dcm",
        content_type="application/dicom",
        size=len(data) if size is None else size,
        storage_key="attachments/study.dcm",
        checksum=hashlib.sha256(data).hexdigest(),
    )


def _client(attachment: Attachment, store: FakeObjectStore) -> TestClient:
    repo = MagicMock()
    repo.get.return_value = attachment
    service = AttachmentService(
        repo,
        MagicMock(),
        AuditService(MagicMock()),
        MagicMock(spec=AuthorizationService),
        store,
    )
    actor = MagicMock(spec=Account)
    actor.id = uuid.uuid4()
    actor.user_type = UserType.DOCTOR
    actor.status = AccountStatus.ACTIVE
    services = PlatformServices(
        authorization=MagicMock(),
        clinical=MagicMock(),
        attachments=service,
        audit=MagicMock(),
    )
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(build_router(), prefix="/dicom")
    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_platform_services] = lambda: services
    return TestClient(app)


def _get(client: TestClient, attachment: Attachment, frame: int = 0):
    return client.get(f"/dicom/studies/{attachment.id}?frame={frame}")


def _assert_problem(resp, rule: str | None = None) -> None:
    assert resp.status_code == 400
    assert resp.headers["content-type"].startswith("application/problem+json")
    body = resp.json()
    assert body["status"] == 400
    if rule is not None:
        assert [e["rule"] for e in body["errors"]] == [rule]


def test_stored_size_over_bound_refused_before_read() -> None:
    """TC-019.1 (SR-017 AC 6): a record of 150 MiB + 1 is refused; the store is not read."""
    data = _dicom(2, 2, pixel_bytes=8)
    attachment = _attachment(data, size=MAX_STORED + 1)
    store = FakeObjectStore(data)

    with _pixel_array(_Frame()) as pixel_array:
        resp = _get(_client(attachment, store), attachment)

    _assert_problem(resp, "dicom_stored_size_exceeded")
    assert str(MAX_STORED) in resp.json()["detail"]
    assert store.calls == []
    pixel_array.assert_not_called()


def test_declared_decoded_size_over_bound_refused_with_small_stored_bytes() -> None:
    """TC-019.2 (SR-017 AC 6): a tiny object whose header declares 1 GiB + 1 is refused before
    ``pixel_array`` is touched."""
    # 32768 x 32768 x 1 frame x 1 sample x 1 byte = 1 GiB; one more column is 1 GiB + 32768.
    data = _dicom(32768, 32769, bits=8, pixel_bytes=8)
    assert len(data) < 1024
    attachment = _attachment(data)

    with _pixel_array(_Frame()) as pixel_array:
        resp = _get(_client(attachment, FakeObjectStore(data)), attachment)

    _assert_problem(resp, "dicom_decoded_size_exceeded")
    pixel_array.assert_not_called()


def test_declared_decoded_size_counts_frames_samples_and_bytes() -> None:
    """TC-019.2: every factor of the declared size counts (here only frames push it over)."""
    data = _dicom(1024, 1024, frames=513, bits=16, pixel_bytes=8)  # 513 MiB * 2 = just over 1 GiB
    attachment = _attachment(data)

    with _pixel_array(_Frame()) as pixel_array:
        resp = _get(_client(attachment, FakeObjectStore(data)), attachment)

    _assert_problem(resp, "dicom_decoded_size_exceeded")
    pixel_array.assert_not_called()


def test_header_without_declared_size_is_refused() -> None:
    """TC-019.2: a missing size attribute is refused, not guessed."""
    data = _dicom(0, 4, pixel_bytes=8)
    attachment = _attachment(data)

    with _pixel_array(_Frame()) as pixel_array:
        resp = _get(_client(attachment, FakeObjectStore(data)), attachment)

    _assert_problem(resp, "dicom_decode_failed")
    pixel_array.assert_not_called()


def test_truncated_pixel_stream_gives_error_and_no_image() -> None:
    """TC-019.3 (SR-017 AC 6): a decode that fails returns a problem and an empty-of-image body."""
    data = _dicom(4, 4, pixel_bytes=32)
    attachment = _attachment(data)

    with _pixel_array(error=ValueError("The amount of pixel data is shorter than expected")):
        resp = _get(_client(attachment, FakeObjectStore(data)), attachment)

    _assert_problem(resp, "dicom_decode_failed")
    assert b"FRAME" not in resp.content
    assert "application/dicom" not in resp.headers["content-type"]


def test_truncated_pixel_stream_real_decode() -> None:
    """TC-019.3 (SR-017 AC 6): pixel data one byte short of the header is really refused by the
    decoder: a 400 problem and no image."""
    data = build_short_pixel_data()
    attachment = _attachment(data)

    resp = _get(_client(attachment, FakeObjectStore(data)), attachment)

    _assert_problem(resp, "dicom_decode_failed")
    assert "application/octet-stream" not in resp.headers["content-type"]
    assert "application/dicom" not in resp.headers["content-type"]


def test_real_decode_at_small_size_within_bounds() -> None:
    """TC-019.3, TC-019.4 (SR-017 AC 6): a real 64 x 64 x 2-frame object, bounds at their defaults,
    is decoded and each frame returned exactly."""
    data, expected = build_dicom(ExplicitVRLittleEndian, rows=64, columns=64, frames=2)
    attachment = _attachment(data)
    client = _client(attachment, FakeObjectStore(data))

    for n in range(2):
        resp = _get(client, attachment, n)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/octet-stream"
        assert resp.content == expected[n].astype("<u2").tobytes()
        assert len(resp.content) == 64 * 64 * 2


def test_reference_study_at_bounds_not_refused() -> None:
    """TC-019.4 (SR-017 AC 6, SR-026 AC 3): a 150 MiB stored object whose header declares exactly
    1 GiB passes both checks; the decode is stubbed."""
    data = _padded_to(MAX_STORED, 8192, 8192, 8)  # 8192 * 8192 * 8 frames * 2 bytes = 1 GiB
    assert len(data) == MAX_STORED
    attachment = _attachment(data)
    store = FakeObjectStore(data)

    with _pixel_array(_Frame((8, 8192, 8192), 2)) as pixel_array:
        resp = _get(_client(attachment, store), attachment)

    assert resp.status_code == 200
    assert resp.content == b"FRAME"
    pixel_array.assert_called_once()
    assert ("get_object", None) in store.calls


def test_check_order_stored_then_syntax_then_declared_then_decode() -> None:
    """TC-019.8 (SR-017 AC 6, AC 10): stored size, then transfer syntax, then declared decoded size,
    then decode; each earlier refusal wins over a later one."""
    over_declared = (32768, 32769)  # 1 GiB + 32768 declared
    jpeg = "1.2.840.10008.1.2.4.50"
    unsupported_big = build_compressed(jpeg, rows=over_declared[0], columns=over_declared[1])
    supported_big, _ = _supported_over_declared()

    with _pixel_array(_Frame()) as pixel_array:
        # over the stored bound and unsupported: the stored bound wins
        attachment = _attachment(unsupported_big, size=MAX_STORED + 1)
        store = FakeObjectStore(unsupported_big)
        resp = _get(_client(attachment, store), attachment)
        _assert_problem(resp, "dicom_stored_size_exceeded")
        assert store.calls == []

        # unsupported and over the declared bound: the syntax wins
        attachment = _attachment(unsupported_big)
        resp = _get(_client(attachment, FakeObjectStore(unsupported_big)), attachment)
        _assert_problem(resp, "dicom_transfer_syntax_unsupported")

        # supported and over the declared bound: the declared bound
        attachment = _attachment(supported_big)
        resp = _get(_client(attachment, FakeObjectStore(supported_big)), attachment)
        _assert_problem(resp, "dicom_decoded_size_exceeded")

    pixel_array.assert_not_called()


def _supported_over_declared() -> tuple[bytes, None]:
    return _dicom(32768, 32769, bits=8, pixel_bytes=8), None
