"""TASK-048: AppointmentService confirm/decline tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.api.errors import AuthorizationError, ConflictError, NotFoundError
from app.appointments.service import AppointmentService
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.appointment import Appointment, AppointmentState


def _make_account(user_type: UserType, id: uuid.UUID | None = None) -> Account:
    return Account(
        id=id or uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _make_appointment(
    patient_id: uuid.UUID, state: AppointmentState = AppointmentState.PENDING
) -> Appointment:
    return Appointment(
        id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        patient_id=patient_id,
        scheduled_at=datetime.now(UTC),
        state=state,
    )


def _build_svc(
    appointment: Appointment | None = None,
) -> tuple[AppointmentService, MagicMock]:
    mock_appt_repo = MagicMock()
    mock_appt_repo.get.return_value = appointment

    mock_account_repo = MagicMock()
    mock_audit = MagicMock()
    mock_consent = MagicMock()
    mock_consent.has_active_grant.return_value = False
    authz_svc = AuthorizationService(mock_consent, MagicMock())

    svc = AppointmentService(mock_appt_repo, mock_account_repo, mock_audit, authz_svc, mock_consent)
    return svc, mock_audit


def test_patient_can_confirm_own_appointment() -> None:
    patient = _make_account(UserType.PATIENT)
    appt = _make_appointment(patient.id)
    svc, _ = _build_svc(appointment=appt)

    result = svc.confirm(patient, appt.id)
    assert result.state == AppointmentState.CONFIRMED


def test_patient_can_decline_own_appointment() -> None:
    patient = _make_account(UserType.PATIENT)
    appt = _make_appointment(patient.id)
    svc, _ = _build_svc(appointment=appt)

    result = svc.decline(patient, appt.id)
    assert result.state == AppointmentState.DECLINED


def test_other_patient_cannot_confirm_appointment() -> None:
    patient = _make_account(UserType.PATIENT)
    other_patient = _make_account(UserType.PATIENT)
    appt = _make_appointment(patient.id)
    svc, _ = _build_svc(appointment=appt)

    with pytest.raises(AuthorizationError):
        svc.confirm(other_patient, appt.id)


def test_confirm_already_declined_raises_conflict() -> None:
    patient = _make_account(UserType.PATIENT)
    appt = _make_appointment(patient.id, state=AppointmentState.DECLINED)
    svc, _ = _build_svc(appointment=appt)

    with pytest.raises(ConflictError):
        svc.confirm(patient, appt.id)


def test_confirm_not_found_raises_not_found() -> None:
    patient = _make_account(UserType.PATIENT)
    svc, _ = _build_svc(appointment=None)

    with pytest.raises(NotFoundError):
        svc.confirm(patient, uuid.uuid4())


def test_confirm_emits_audit() -> None:
    patient = _make_account(UserType.PATIENT)
    appt = _make_appointment(patient.id)
    svc, mock_audit = _build_svc(appointment=appt)

    svc.confirm(patient, appt.id)
    assert "APPOINTMENT_CONFIRM" in str(mock_audit.record.call_args)


def test_decline_emits_audit() -> None:
    patient = _make_account(UserType.PATIENT)
    appt = _make_appointment(patient.id)
    svc, mock_audit = _build_svc(appointment=appt)

    svc.decline(patient, appt.id)
    assert "APPOINTMENT_DECLINE" in str(mock_audit.record.call_args)
