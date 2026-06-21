"""Constraint tests (TASK-011): unique, FK, NOT NULL, enum enforcement."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.appointment import Appointment, AppointmentState


def _now() -> datetime:
    return datetime.now(UTC)


def _make_account(email: str, session) -> Account:
    acc = Account(
        email=email,
        user_type=UserType.PATIENT,
        status=AccountStatus.ACTIVE,
    )
    session.add(acc)
    session.flush()
    return acc


# SR-003.1: duplicate email must be rejected even for DELETED account


def test_duplicate_email_rejected(db_session):
    _make_account("dup@example.com", db_session)
    dup = Account(email="dup@example.com", user_type=UserType.DOCTOR, status=AccountStatus.DELETED)
    db_session.add(dup)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# SR-010.2: appointment with NULL doctor_id rejected


def test_appointment_null_doctor_id_rejected(db_session):
    patient = _make_account("nulldoc_pat@example.com", db_session)
    # Use raw SQL insert to bypass ORM default-generation and test DB NOT NULL
    with pytest.raises((IntegrityError, Exception)):
        db_session.execute(
            text(
                "INSERT INTO appointment"
                " (id, doctor_id, patient_id, scheduled_at, state, created_at)"
                " VALUES (:id, NULL, :patient_id, :scheduled_at, 'PENDING', now())"
            ),
            {"id": str(uuid.uuid4()), "patient_id": str(patient.id), "scheduled_at": _now()},
        )
        db_session.flush()
    db_session.rollback()


# SR-010.2: appointment with NULL patient_id rejected


def test_appointment_null_patient_id_rejected(db_session):
    doctor = Account(
        email="nullpat_doc@example.com",
        user_type=UserType.DOCTOR,
        status=AccountStatus.ACTIVE,
    )
    db_session.add(doctor)
    db_session.flush()
    with pytest.raises((IntegrityError, Exception)):
        db_session.execute(
            text(
                "INSERT INTO appointment"
                " (id, doctor_id, patient_id, scheduled_at, state, created_at)"
                " VALUES (:id, :doctor_id, NULL, :scheduled_at, 'PENDING', now())"
            ),
            {"id": str(uuid.uuid4()), "doctor_id": str(doctor.id), "scheduled_at": _now()},
        )
        db_session.flush()
    db_session.rollback()


# SR-010.2: appointment with NULL scheduled_at rejected


def test_appointment_null_scheduled_at_rejected(db_session):
    doctor = _make_account("null_sched_doc@example.com", db_session)
    patient = _make_account("null_sched_pat@example.com", db_session)
    with pytest.raises((IntegrityError, Exception)):
        db_session.execute(
            text(
                "INSERT INTO appointment"
                " (id, doctor_id, patient_id, scheduled_at, state, created_at)"
                " VALUES (:id, :doctor_id, :patient_id, NULL, 'PENDING', now())"
            ),
            {"id": str(uuid.uuid4()), "doctor_id": str(doctor.id), "patient_id": str(patient.id)},
        )
        db_session.flush()
    db_session.rollback()


# SR-010.1: appointment with non-existent account FK rejected


def test_appointment_nonexistent_fk_rejected(db_session):
    appt = Appointment(
        doctor_id=uuid.uuid4(),  # does not exist
        patient_id=uuid.uuid4(),  # does not exist
        scheduled_at=_now(),
        state=AppointmentState.PENDING,
    )
    db_session.add(appt)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
