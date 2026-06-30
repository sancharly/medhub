"""TASK-045: AttachmentService store tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.api.errors import AuthorizationError, NotFoundError, ValidationProblem
from app.attachments.service import AttachmentService
from app.authz.service import AuthorizationService
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

    svc.store(doctor, entry.id, "test.pdf", "application/pdf", b"PDF content here")
    mock_attachment_repo.add.assert_called_once()


def test_store_attachment_entry_not_found() -> None:
    doctor = _make_account(UserType.DOCTOR)
    svc, _, _, _ = _build_svc(entry=None)
    with pytest.raises(NotFoundError):
        svc.store(doctor, uuid.uuid4(), "test.pdf", "application/pdf", b"data")


def test_doctor_without_consent_denied_upload() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, _, _, _ = _build_svc(effective_access=False, entry=entry)
    with pytest.raises(AuthorizationError):
        svc.store(doctor, entry.id, "test.pdf", "application/pdf", b"data")


def test_store_calls_object_storage() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, _, mock_storage, _ = _build_svc(effective_access=True, entry=entry)

    svc.store(doctor, entry.id, "test.pdf", "application/pdf", b"data")
    mock_storage.put_object.assert_called_once()


def test_store_invalid_dicom_raises_validation() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, _, _, _ = _build_svc(effective_access=True, entry=entry)

    with pytest.raises(ValidationProblem):
        svc.store(doctor, entry.id, "test.dcm", "application/dicom", b"not a real dicom file")


def test_store_emits_audit() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    entry = _make_entry(patient.id)
    svc, _, _, mock_audit = _build_svc(effective_access=True, entry=entry)

    svc.store(doctor, entry.id, "test.pdf", "application/pdf", b"PDF data content")
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
        svc.store(doctor, entry.id, "scan.dcm", "application/dicom", b"fake dcm")

    mock_repo.add.assert_called_once()
    stored: Attachment = mock_repo.add.call_args[0][0]
    assert stored.dicom_metadata is not None
    assert stored.dicom_metadata.get("modality") == "CT"
