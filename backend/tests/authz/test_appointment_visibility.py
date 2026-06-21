"""TASK-051: Appointment visibility tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.authz.appointment_visibility import can_view_appointment
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.appointment import Appointment, AppointmentState


def _make_account(user_type: UserType, id: uuid.UUID | None = None) -> Account:
    return Account(
        id=id or uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _make_appointment(doctor_id: uuid.UUID, patient_id: uuid.UUID) -> Appointment:
    return Appointment(
        id=uuid.uuid4(),
        doctor_id=doctor_id,
        patient_id=patient_id,
        scheduled_at=datetime.now(UTC),
        state=AppointmentState.PENDING,
    )


def test_doctor_can_view_own_appointment() -> None:
    doctor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    appt = _make_appointment(doctor.id, patient.id)
    assert can_view_appointment(doctor, appt) is True


def test_patient_can_view_own_appointment() -> None:
    doctor = _make_account(UserType.DOCTOR)
    patient = _make_account(UserType.PATIENT)
    appt = _make_appointment(doctor.id, patient.id)
    assert can_view_appointment(patient, appt) is True


def test_admin_can_view_any_appointment() -> None:
    admin = _make_account(UserType.ADMIN)
    appt = _make_appointment(uuid.uuid4(), uuid.uuid4())
    assert can_view_appointment(admin, appt) is True


def test_sysadmin_can_view_any_appointment() -> None:
    sysadmin = _make_account(UserType.SYSADMIN)
    appt = _make_appointment(uuid.uuid4(), uuid.uuid4())
    assert can_view_appointment(sysadmin, appt) is True


def test_other_doctor_cannot_view_appointment() -> None:
    other_doctor = _make_account(UserType.DOCTOR)
    appt = _make_appointment(uuid.uuid4(), uuid.uuid4())
    assert can_view_appointment(other_doctor, appt) is False


def test_other_patient_cannot_view_appointment() -> None:
    other_patient = _make_account(UserType.PATIENT)
    appt = _make_appointment(uuid.uuid4(), uuid.uuid4())
    assert can_view_appointment(other_patient, appt) is False
