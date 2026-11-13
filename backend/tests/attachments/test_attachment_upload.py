"""TASK-045: AttachmentService store tests."""

from __future__ import annotations

import hashlib
import io
import tracemalloc
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.api.errors import AuthorizationError, NotFoundError, ValidationProblem
from app.attachments.service import AttachmentService
from app.authz.service import AuthorizationService
from app.core.config import Settings
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.attachment import Attachment
from app.db.models.clinical import ClinicalEntry


def _make_account(user_type: UserType, id: uuid.UUID | None = None) -> Account:
    return Account(
        id=id or uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _make_entry(patient_id: uuid.UUID) -> ClinicalEntry:
    return ClinicalEntry(
        id=uuid.uuid4(),
        patient_id=patient_id,
        author_doctor_id=uuid.uuid4(),
        occurred_at=datetime.now(UTC),
        description="Test",
    )


def _build_svc(
    effective_access: bool = True,
    entry: ClinicalEntry | None = None,
) -> tuple[AttachmentService, MagicMock, MagicMock, MagicMock]:
    mock_attachment_repo = MagicMock()
    new_attachment = Attachment(
        id=uuid.uuid4(),
        clinical_entry_id=entry.id if entry else uuid.uuid4(),
        patient_id=entry.patient_id if entry else uuid.uuid4(),
        filename="test.pdf",
        content_type="application/pdf",
        size=100,
        storage_key="attachments/key",
        checksum="abc",
    )
    mock_attachment_repo.add.return_value = new_attachment

    mock_clinical_repo = MagicMock()
    mock_clinical_repo.get.return_value = entry

    mock_audit = MagicMock()
    mock_storage = MagicMock()

    mock_consent = MagicMock()
    mock_consent.has_active_grant.return_value = effective_access
    authz_svc = AuthorizationService(mock_consent, MagicMock())

    svc = AttachmentService(
        mock_attachment_repo, mock_clinical_repo, mock_audit, authz_svc, mock_storage
    )
    return svc, mock_attachment_repo, mock_storage, mock_audit


def test_doctor_with_consent_can_store_attachment() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, mock_attachment_repo, _, _ = _build_svc(effective_access=True, entry=entry)

    svc.store(doctor, entry.id, "test.pdf", "application/pdf", io.BytesIO(b"PDF content here"))
    mock_attachment_repo.add.assert_called_once()


def test_store_attachment_entry_not_found() -> None:
    doctor = _make_account(UserType.DOCTOR)
    svc, _, _, _ = _build_svc(entry=None)
    with pytest.raises(NotFoundError):
        svc.store(doctor, uuid.uuid4(), "test.pdf", "application/pdf", io.BytesIO(b"data"))


def test_doctor_without_consent_denied_upload() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, _, _, _ = _build_svc(effective_access=False, entry=entry)
    with pytest.raises(AuthorizationError):
        svc.store(doctor, entry.id, "test.pdf", "application/pdf", io.BytesIO(b"data"))


def test_store_calls_object_storage() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, _, mock_storage, _ = _build_svc(effective_access=True, entry=entry)

    svc.store(doctor, entry.id, "test.pdf", "application/pdf", io.BytesIO(b"data"))
    mock_storage.put_object.assert_called_once()


def test_store_invalid_dicom_raises_validation() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, _, _, _ = _build_svc(effective_access=True, entry=entry)

    with pytest.raises(ValidationProblem):
        svc.store(
            doctor, entry.id, "test.dcm", "application/dicom", io.BytesIO(b"not a real dicom file")
        )


def test_store_emits_audit() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, _, _, mock_audit = _build_svc(effective_access=True, entry=entry)

    svc.store(doctor, entry.id, "test.pdf", "application/pdf", io.BytesIO(b"PDF data content"))
    mock_audit.record.assert_called()
    assert "ATTACHMENT_UPLOAD" in str(mock_audit.record.call_args)


def test_dicom_upload_stores_metadata() -> None:
    """Valid DICOM upload stores dicom_metadata in the attachment row."""
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, mock_repo, _, _ = _build_svc(effective_access=True, entry=entry)

    mock_ds = MagicMock()
    mock_ds.Modality = "CT"
    mock_ds.PatientID = None
    mock_ds.StudyDate = None

    with patch("pydicom.dcmread", return_value=mock_ds):
        svc.store(doctor, entry.id, "scan.dcm", "application/dicom", io.BytesIO(b"fake dcm"))

    mock_repo.add.assert_called_once()
    stored: Attachment = mock_repo.add.call_args[0][0]
    assert stored.dicom_metadata is not None
    assert stored.dicom_metadata.get("modality") == "CT"


def test_filename_over_255_bytes_is_rejected_with_400() -> None:
    """TASK-206 AC-2 (PRB-069): 256 bytes is refused; nothing is written."""
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, repo, storage, audit = _build_svc(effective_access=True, entry=entry)

    with pytest.raises(ValidationProblem) as exc:
        svc.store(doctor, entry.id, "a" * 252 + ".pdf", "application/pdf", io.BytesIO(b"data"))
    assert exc.value.status == 400
    assert exc.value.errors[0].field == "file"
    assert exc.value.errors[0].rule == "filename_max_bytes"
    storage.put_object.assert_not_called()
    repo.add.assert_not_called()


def test_filename_bound_counts_utf8_bytes_not_characters() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, repo, storage, _ = _build_svc(effective_access=True, entry=entry)

    with pytest.raises(ValidationProblem):
        svc.store(
            doctor, entry.id, "患" * 84 + ".txt", "text/plain", io.BytesIO(b"data")
        )  # 256 bytes
    storage.put_object.assert_not_called()


def test_filename_of_exactly_255_bytes_is_accepted() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, repo, storage, _ = _build_svc(effective_access=True, entry=entry)

    svc.store(
        doctor, entry.id, "患" * 83 + "ab.txt", "text/plain", io.BytesIO(b"data")
    )  # 255 bytes
    storage.put_object.assert_called_once()
    repo.add.assert_called_once()


# --- TASK-135: bounded-memory upload, limit enforced while reading (SR-013 AC 6, SR-017 AC 6) ---


class _ZeroFile:
    """A readable, seekable file of ``total`` zero bytes that never holds more than one chunk."""

    def __init__(self, total: int) -> None:
        self.total = total
        self.pos = 0
        self.max_chunk = 0

    def read(self, n: int = -1) -> bytes:
        n = self.total - self.pos if n < 0 else min(n, self.total - self.pos)
        self.pos += n
        self.max_chunk = max(self.max_chunk, n)
        return bytes(n)

    def seek(self, offset: int, whence: int = 0) -> int:
        assert whence == 0
        self.pos = offset
        return offset

    def tell(self) -> int:
        return self.pos


def _zeros_sha256(total: int) -> str:
    digest = hashlib.sha256()
    block = bytes(1 << 20)
    for _ in range(total // len(block)):
        digest.update(block)
    digest.update(bytes(total % len(block)))
    return digest.hexdigest()


def _store_zeros(monkeypatch, maximum: int, total: int):
    monkeypatch.setattr(
        "app.attachments.service.get_settings",
        lambda: SimpleNamespace(attachment_max_bytes=maximum),
    )
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, repo, storage, _ = _build_svc(effective_access=True, entry=entry)
    fileobj = _ZeroFile(total)

    def run() -> Attachment:
        return svc.store(doctor, entry.id, "big.bin", "application/octet-stream", fileobj)

    return repo, storage, fileobj, run


def test_upload_over_limit_refused_within_limit_plus_one_chunk(monkeypatch) -> None:
    """SR-013 AC 6: over the maximum, refuse after reading at most the maximum plus one chunk."""
    maximum = 1 << 20
    repo, storage, fileobj, run = _store_zeros(monkeypatch, maximum, maximum + (10 << 20))
    with pytest.raises(ValidationProblem) as exc:
        run()
    assert exc.value.status == 400
    assert fileobj.pos <= maximum + 65536
    assert fileobj.max_chunk <= 65536
    storage.put_object.assert_not_called()
    repo.add.assert_not_called()


def test_upload_at_limit_accepted(monkeypatch) -> None:
    """SR-013 AC 6, SR-017 AC 6: exactly the 150 MiB maximum is stored, checksum is the SHA-256."""
    maximum = Settings.model_fields["attachment_max_bytes"].default
    assert maximum == 150 * 1024 * 1024
    repo, storage, fileobj, run = _store_zeros(monkeypatch, maximum, maximum)
    run()
    storage.put_object.assert_called_once()
    _key, body, size, _ctype = storage.put_object.call_args[0]
    assert body is fileobj and size == maximum
    assert fileobj.pos == 0  # rewound for the upload
    stored: Attachment = repo.add.call_args[0][0]
    assert stored.size == maximum
    assert stored.checksum == _zeros_sha256(maximum)


def test_upload_one_byte_over_limit_refused(monkeypatch) -> None:
    """SR-013 AC 6: the boundary is exact."""
    repo, storage, _, run = _store_zeros(monkeypatch, 1 << 20, (1 << 20) + 1)
    with pytest.raises(ValidationProblem):
        run()
    storage.put_object.assert_not_called()


def test_upload_memory_bounded(monkeypatch) -> None:
    """SR-013 AC 6: the peak allocation does not grow with the object size."""
    peaks = []
    for total in (20 << 20, 60 << 20):
        _, _, _, run = _store_zeros(monkeypatch, 150 << 20, total)
        tracemalloc.start()
        try:
            run()
            peaks.append(tracemalloc.get_traced_memory()[1])
        finally:
            tracemalloc.stop()
    assert all(peak < 4 << 20 for peak in peaks), peaks
