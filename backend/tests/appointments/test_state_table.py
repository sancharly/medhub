"""TASK-048: Appointment state machine table tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.api.errors import ConflictError
from app.appointments.state import ALLOWED_TRANSITIONS, transition
from app.db.models.appointment import Appointment, AppointmentState


def _make_appointment(state: AppointmentState) -> Appointment:
    return Appointment(
        id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        scheduled_at=datetime.now(UTC),
        state=state,
    )


def test_pending_to_confirmed_allowed() -> None:
    appt = _make_appointment(AppointmentState.PENDING)
    transition(appt, AppointmentState.CONFIRMED)  # should not raise


def test_pending_to_declined_allowed() -> None:
    appt = _make_appointment(AppointmentState.PENDING)
    transition(appt, AppointmentState.DECLINED)  # should not raise


def test_confirmed_to_declined_allowed() -> None:
    appt = _make_appointment(AppointmentState.CONFIRMED)
    transition(appt, AppointmentState.DECLINED)  # should not raise


def test_confirmed_to_pending_disallowed() -> None:
    appt = _make_appointment(AppointmentState.CONFIRMED)
    with pytest.raises(ConflictError):
        transition(appt, AppointmentState.PENDING)


def test_declined_to_any_disallowed() -> None:
    appt = _make_appointment(AppointmentState.DECLINED)
    with pytest.raises(ConflictError):
        transition(appt, AppointmentState.PENDING)
    appt2 = _make_appointment(AppointmentState.DECLINED)
    with pytest.raises(ConflictError):
        transition(appt2, AppointmentState.CONFIRMED)


def test_allowed_transitions_set_contents() -> None:
    assert (AppointmentState.PENDING, AppointmentState.CONFIRMED) in ALLOWED_TRANSITIONS
    assert (AppointmentState.PENDING, AppointmentState.DECLINED) in ALLOWED_TRANSITIONS
    assert (AppointmentState.CONFIRMED, AppointmentState.DECLINED) in ALLOWED_TRANSITIONS
    assert len(ALLOWED_TRANSITIONS) == 3
