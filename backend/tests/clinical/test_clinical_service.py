"""TASK-044: ClinicalDataService tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.api.errors import AuthorizationError, ValidationProblem
from app.authz.service import AuthorizationService
from app.clinical.service import ClinicalDataService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.clinical import ClinicalEntry


def _make_account(user_type: UserType, id: uuid.UUID | None = None) -> Account:
    return Account(
        id=id or uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _build_svc(
    effective_access: bool = True,
    patient: Account | None = None,
    entries: list[ClinicalEntry] | None = None,
) -> tuple[ClinicalDataService, MagicMock, MagicMock]:
    mock_clinical_repo = MagicMock()
    new_entry = ClinicalEntry(
        id=uuid.uuid4(),
        patient_id=patient.id if patient else uuid.uuid4(),
        author_doctor_id=uuid.uuid4(),
        occurred_at=datetime.now(UTC),
        description="Test entry",
    )
    mock_clinical_repo.add.return_value = new_entry
    mock_clinical_repo.list_for_patient_ordered.return_value = entries or []

    mock_account_repo = MagicMock()
    mock_account_repo.get_by_id.return_value = patient

    mock_audit = MagicMock()

    mock_consent = MagicMock()
    mock_consent.has_active_grant.return_value = effective_access
    authz_svc = AuthorizationService(mock_consent, MagicMock())

    svc = ClinicalDataService(mock_clinical_repo, mock_account_repo, mock_audit, authz_svc)
    return svc, mock_clinical_repo, mock_audit


def test_doctor_with_consent_creates_entry() -> None:
    """SR-012 AC-3: author_doctor_id is always the actor, not from request."""
    actor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    svc, mock_clinical_repo, _ = _build_svc(effective_access=True, patient=patient)

    svc.create_entry(actor, patient.id, datetime.now(UTC), "Patient has fever.")
    created_call = mock_clinical_repo.add.call_args[0][0]
    assert created_call.author_doctor_id == actor.id


def test_create_entry_blank_description_raises_validation() -> None:
    actor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    svc, _, _ = _build_svc(effective_access=True, patient=patient)
    with pytest.raises(ValidationProblem):
        svc.create_entry(actor, patient.id, datetime.now(UTC), "   ")


def test_doctor_without_consent_denied_create() -> None:
    actor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    svc, _, _ = _build_svc(effective_access=False, patient=patient)
    with pytest.raises(AuthorizationError):
        svc.create_entry(actor, patient.id, datetime.now(UTC), "Some description.")


def test_patient_lists_own_entries() -> None:
    patient = _make_account(UserType.PATIENT)
    entry = ClinicalEntry(
        id=uuid.uuid4(),
        patient_id=patient.id,
        author_doctor_id=uuid.uuid4(),
        occurred_at=datetime.now(UTC),
        description="Entry",
    )
    svc, _, _ = _build_svc(patient=patient, entries=[entry])
    result = svc.list_entries(patient, patient.id)
    assert len(result) == 1


def test_patient_cannot_list_other_patients_entries() -> None:
    patient = _make_account(UserType.PATIENT)
    other_patient_id = uuid.uuid4()
    svc, _, _ = _build_svc(patient=patient)
    with pytest.raises(AuthorizationError):
        svc.list_entries(patient, other_patient_id)


def test_doctor_with_consent_lists_entries() -> None:
    doctor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    entry = ClinicalEntry(
        id=uuid.uuid4(),
        patient_id=patient.id,
        author_doctor_id=doctor.id,
        occurred_at=datetime.now(UTC),
        description="Entry",
    )
    svc, _, _ = _build_svc(effective_access=True, patient=patient, entries=[entry])
    result = svc.list_entries(doctor, patient.id)
    assert len(result) == 1


def test_doctor_without_consent_cannot_list_entries() -> None:
    doctor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    svc, _, _ = _build_svc(effective_access=False, patient=patient)
    with pytest.raises(AuthorizationError):
        svc.list_entries(doctor, patient.id)


def test_create_entry_emits_audit() -> None:
    actor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    svc, _, mock_audit = _build_svc(effective_access=True, patient=patient)
    svc.create_entry(actor, patient.id, datetime.now(UTC), "Test description.")
    mock_audit.record.assert_called()
    assert "CLINICAL_CREATE" in str(mock_audit.record.call_args)
