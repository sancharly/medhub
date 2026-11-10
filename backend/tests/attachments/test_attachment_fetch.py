"""TASK-046: AttachmentService open tests."""

from __future__ import annotations

import hashlib
import uuid
from unittest.mock import MagicMock

import pytest

from app.api.errors import AttachmentIntegrityError, AuthorizationError, NotFoundError
from app.attachments.service import AttachmentService
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.attachment import Attachment
from app.db.models.audit import AuditOutcome


def _make_account(user_type: UserType, id: uuid.UUID | None = None) -> Account:
    return Account(
        id=id or uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


_ORIGINAL = b"file content"


def _make_attachment(patient_id: uuid.UUID, data: bytes = _ORIGINAL) -> Attachment:
    return Attachment(
        id=uuid.uuid4(),
        clinical_entry_id=uuid.uuid4(),
        patient_id=patient_id,
        filename="xray.dcm",
        content_type="application/dicom",
        size=1024,
        storage_key="attachments/xray.dcm",
        checksum=hashlib.sha256(data).hexdigest(),
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


def test_open_unmodified_object_returns_identical_bytes_and_audits_success() -> None:
    """TC-007.7: a matching checksum changes nothing for the user (SR-013 AC 5)."""
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    attachment = _make_attachment(patient.id)
    svc, mock_audit = _build_svc(attachment=attachment, storage_data=_ORIGINAL)

    data, _, _ = svc.open(doctor, attachment.id)

    assert data == _ORIGINAL
    kwargs = mock_audit.record.call_args.kwargs
    assert kwargs["action"] == "ATTACHMENT_ACCESS"
    assert kwargs["outcome"] == AuditOutcome.SUCCESS


def test_open_substituted_object_is_refused_and_audited_as_failure() -> None:
    """TC-007.6: stored bytes differ from the upload checksum -> no content, FAILURE audit."""
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    attachment = _make_attachment(patient.id)
    substituted = b"planted content"
    svc, mock_audit = _build_svc(attachment=attachment, storage_data=substituted)

    with pytest.raises(AttachmentIntegrityError) as excinfo:
        svc.open(doctor, attachment.id)

    err = excinfo.value
    assert err.status == 502
    assert str(attachment.id) in err.detail
    assert attachment.checksum not in err.detail
    assert hashlib.sha256(substituted).hexdigest() not in err.detail
    assert "planted" not in err.detail
    kwargs = mock_audit.record.call_args.kwargs
    assert kwargs["action"] == "ATTACHMENT_ACCESS"
    assert kwargs["outcome"] == AuditOutcome.FAILURE
    assert kwargs["actor"] == doctor.id
    assert kwargs["target_type"] == "attachment"
    assert kwargs["target_id"] == str(attachment.id)
    # No SUCCESS access row was written for the refused read.
    assert all(
        c.kwargs["outcome"] == AuditOutcome.FAILURE for c in mock_audit.record.call_args_list
    )


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


def _failure_calls(mock_audit: MagicMock) -> list:
    return [
        c for c in mock_audit.record.call_args_list if c.kwargs["outcome"] == AuditOutcome.FAILURE
    ]


def test_storage_error_records_one_failure_and_propagates() -> None:
    """AC-3 (TC-007.10): storage raises -> FAILURE ATTACHMENT_ACCESS, no SUCCESS."""
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    attachment = _make_attachment(patient.id)
    svc, mock_audit = _build_svc(attachment=attachment)
    svc._storage.get_object.side_effect = RuntimeError("store down")  # type: ignore[attr-defined]

    with pytest.raises(RuntimeError, match="store down"):
        svc.open(doctor, attachment.id)

    assert mock_audit.record.call_count == 1
    kwargs = _failure_calls(mock_audit)[0].kwargs
    assert kwargs["action"] == "ATTACHMENT_ACCESS"
    assert kwargs["actor"] == doctor.id
    assert kwargs["target_type"] == "attachment"
    assert kwargs["target_id"] == str(attachment.id)


def test_missing_object_records_one_failure_and_raises_not_found() -> None:
    """AC-3 (TC-007.10): row without object -> NotFoundError and a FAILURE row."""
    patient = _make_account(UserType.PATIENT)
    doctor = _make_account(UserType.DOCTOR)
    attachment = _make_attachment(patient.id)
    svc, mock_audit = _build_svc(attachment=attachment)
    svc._storage.get_object.return_value = None  # type: ignore[attr-defined]

    with pytest.raises(NotFoundError):
        svc.open(doctor, attachment.id)

    assert mock_audit.record.call_count == 1
    kwargs = _failure_calls(mock_audit)[0].kwargs
    assert kwargs["actor"] == doctor.id
    assert kwargs["target_id"] == str(attachment.id)


def test_record_access_failure_writes_attachment_failure_row() -> None:
    """AC-3: the public method writes the ADR-0016 FAILURE event with the request's address."""
    doctor = _make_account(UserType.DOCTOR)
    svc, mock_audit = _build_svc()
    att_id = uuid.uuid4()

    svc.record_access_failure(doctor, att_id)

    mock_audit.record.assert_called_once_with(
        actor=doctor.id,
        action="ATTACHMENT_ACCESS",
        target_type="attachment",
        target_id=str(att_id),
        outcome=AuditOutcome.FAILURE,
        ip=None,
    )
