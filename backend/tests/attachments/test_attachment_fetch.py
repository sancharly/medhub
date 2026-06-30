"""TASK-046: AttachmentService open tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.api.errors import AuthorizationError, NotFoundError
from app.attachments.service import AttachmentService
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.attachment import Attachment


def _make_account(user_type: UserType, id: uuid.UUID | None = None) -> Account:
    return Account(
        id=id or uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _make_attachment(patient_id: uuid.UUID) -> Attachment:
    return Attachment(
        id=uuid.uuid4(),
        clinical_entry_id=uuid.uuid4(),
        patient_id=patient_id,
        filename="xray.dcm",
        content_type="application/dicom",
        size=1024,
        storage_key="attachments/xray.dcm",
        checksum="deadbeef",
    )


def _build_svc(
    effective_access: bool = True,
    attachment: Attachment | None = None,
    storage_data: bytes = b"file content",
) -> tuple[AttachmentService, MagicMock]:
    mock_attachment_repo = MagicMock()
    mock_attachment_repo.get.return_value = attachment

    mock_clinical_repo = MagicMock()
    mock_audit = MagicMock()
    mock_storage = MagicMock()
    mock_storage.get_object.return_value = storage_data

    mock_consent = MagicMock()
    mock_consent.has_active_grant.return_value = effective_access
    authz_svc = AuthorizationService(mock_consent, MagicMock())

    svc = AttachmentService(
        mock_attachment_repo, mock_clinical_repo, mock_audit, authz_svc, mock_storage
    )
    return svc, mock_audit


def test_doctor_with_consent_can_open_attachment() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    attachment = _make_attachment(patient.id)
    svc, _ = _build_svc(effective_access=True, attachment=attachment)

    data, content_type, filename = svc.open(doctor, attachment.id)
    assert data == b"file content"
    assert content_type == "application/dicom"
    assert filename == "xray.dcm"


def test_open_attachment_not_found() -> None:
    doctor = _make_account(UserType.DOCTOR)
    svc, _ = _build_svc(attachment=None)
    with pytest.raises(NotFoundError):
        svc.open(doctor, uuid.uuid4())


def test_doctor_without_consent_cannot_open() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    attachment = _make_attachment(patient.id)
    svc, _ = _build_svc(effective_access=False, attachment=attachment)
    with pytest.raises(AuthorizationError):
        svc.open(doctor, attachment.id)


def test_open_emits_audit() -> None:
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    attachment = _make_attachment(patient.id)
    svc, mock_audit = _build_svc(effective_access=True, attachment=attachment)

    svc.open(doctor, attachment.id)
    mock_audit.record.assert_called()
    assert "ATTACHMENT_ACCESS" in str(mock_audit.record.call_args)


def _build_svc_for_list(
    effective_access: bool = True,
    entry: object | None = "default",
    attachments: list[Attachment] | None = None,
) -> tuple[AttachmentService, MagicMock, MagicMock]:
    mock_attachment_repo = MagicMock()
    mock_attachment_repo.list_for_clinical_entry.return_value = attachments or []

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
    return svc, mock_audit, mock_attachment_repo


class _FakeClinicalEntry:
    def __init__(self, patient_id: uuid.UUID) -> None:
        self.patient_id = patient_id


def test_list_attachments_returns_attachments_for_entry() -> None:
    doctor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    entry = _FakeClinicalEntry(patient.id)
    entry_id = uuid.uuid4()
    attachment = _make_attachment(patient.id)
    svc, _, mock_attachment_repo = _build_svc_for_list(
        effective_access=True, entry=entry, attachments=[attachment]
    )

    result = svc.list_attachments(doctor, entry_id)

    assert result == [attachment]
    mock_attachment_repo.list_for_clinical_entry.assert_called_once_with(entry_id)


def test_list_attachments_entry_not_found() -> None:
    doctor = _make_account(UserType.DOCTOR)
    svc, _, _ = _build_svc_for_list(entry=None)
    with pytest.raises(NotFoundError):
        svc.list_attachments(doctor, uuid.uuid4())


def test_list_attachments_without_consent_denied() -> None:
    doctor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    entry = _FakeClinicalEntry(patient.id)
    svc, _, _ = _build_svc_for_list(effective_access=False, entry=entry)
    with pytest.raises(AuthorizationError):
        svc.list_attachments(doctor, uuid.uuid4())


def test_list_attachments_emits_audit() -> None:
    doctor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    entry = _FakeClinicalEntry(patient.id)
    svc, mock_audit, _ = _build_svc_for_list(effective_access=True, entry=entry)

    svc.list_attachments(doctor, uuid.uuid4())
    mock_audit.record.assert_called()
    assert "ATTACHMENT_ACCESS" in str(mock_audit.record.call_args)
