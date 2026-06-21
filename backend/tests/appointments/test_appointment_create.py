"""TASK-047: AppointmentService create tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.api.errors import AuthorizationError, ValidationProblem
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


def _build_svc(
    actor: Account,
    doctor: Account | None = None,
    patient: Account | None = None,
) -> tuple[AppointmentService, MagicMock]:
    mock_appt_repo = MagicMock()
    new_appt = Appointment(
        id=uuid.uuid4(),
        doctor_id=(doctor.id if doctor else uuid.uuid4()),
        patient_id=(patient.id if patient else uuid.uuid4()),
        scheduled_at=datetime.now(UTC),
        state=AppointmentState.PENDING,
    )
    mock_appt_repo.add.return_value = new_appt

    mock_account_repo = MagicMock()

    def _get_account(id: uuid.UUID) -> Account | None:
        if doctor and id == doctor.id:
            return doctor
        if patient and id == patient.id:
            return patient
        return None

    mock_account_repo.get_by_id.side_effect = _get_account

    mock_audit = MagicMock()
    mock_consent = MagicMock()
    mock_consent.has_active_grant.return_value = False
    authz_svc = AuthorizationService(mock_consent, MagicMock())

    svc = AppointmentService(mock_appt_repo, mock_account_repo, mock_audit, authz_svc, mock_consent)
    return svc, mock_audit


def test_admin_can_create_appointment() -> None:
    actor = _make_account(UserType.ADMIN)
    doctor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    svc, _ = _build_svc(actor, doctor=doctor, patient=patient)

    appt = svc.create(actor, doctor.id, patient.id, datetime.now(UTC))

    assert appt.state == AppointmentState.PENDING


def test_sysadmin_can_create_appointment() -> None:
    actor = _make_account(UserType.SYSADMIN)
    doctor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    svc, _ = _build_svc(actor, doctor=doctor, patient=patient)

    appt = svc.create(actor, doctor.id, patient.id, datetime.now(UTC))

    assert appt is not None


def test_doctor_can_create_appointment() -> None:
    actor = _make_account(UserType.DOCTOR)
    doctor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    svc, _ = _build_svc(actor, doctor=doctor, patient=patient)

    appt = svc.create(actor, doctor.id, patient.id, datetime.now(UTC))

    assert appt is not None


def test_patient_cannot_create_appointment() -> None:
    actor = _make_account(UserType.PATIENT)
    svc, _ = _build_svc(actor)
    with pytest.raises(AuthorizationError):
        svc.create(actor, uuid.uuid4(), uuid.uuid4(), datetime.now(UTC))


def test_create_with_non_doctor_account_raises_validation() -> None:
    actor = _make_account(UserType.ADMIN)
    fake_doctor = _make_account(UserType.PATIENT)  # wrong type
    patient = _make_account(UserType.PATIENT)
    svc, _ = _build_svc(actor, doctor=fake_doctor, patient=patient)

    with pytest.raises(ValidationProblem):
        svc.create(actor, fake_doctor.id, patient.id, datetime.now(UTC))


def test_create_with_non_patient_account_raises_validation() -> None:
    actor = _make_account(UserType.ADMIN)
    doctor = _make_account(UserType.DOCTOR)
    fake_patient = _make_account(UserType.DOCTOR)  # wrong type
    svc, _ = _build_svc(actor, doctor=doctor, patient=fake_patient)

    with pytest.raises(ValidationProblem):
        svc.create(actor, doctor.id, fake_patient.id, datetime.now(UTC))


def test_create_emits_audit() -> None:
    actor = _make_account(UserType.ADMIN)
    doctor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    svc, mock_audit = _build_svc(actor, doctor=doctor, patient=patient)

    svc.create(actor, doctor.id, patient.id, datetime.now(UTC))

    mock_audit.record.assert_called()
    assert "APPOINTMENT_CREATE" in str(mock_audit.record.call_args)
