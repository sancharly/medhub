"""Appointment state machine (TASK-048)."""

from app.api.errors import ConflictError
from app.db.models.appointment import Appointment, AppointmentState

# Valid state transitions: (from_state, to_state)
ALLOWED_TRANSITIONS: set[tuple[AppointmentState, AppointmentState]] = {
    (AppointmentState.PENDING, AppointmentState.CONFIRMED),
    (AppointmentState.PENDING, AppointmentState.DECLINED),
    (AppointmentState.CONFIRMED, AppointmentState.DECLINED),
}


def transition(appointment: Appointment, target_state: AppointmentState) -> Appointment:
    """Validate and apply a state transition.

    Raises ConflictError if the transition is not allowed.
    """
    edge = (appointment.state, target_state)
    if edge not in ALLOWED_TRANSITIONS:
        raise ConflictError(
            f"Invalid appointment transition: {appointment.state.value} -> {target_state.value}"
        )
    return appointment
