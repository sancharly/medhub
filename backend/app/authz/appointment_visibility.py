"""Appointment visibility rules (TASK-051).

Visibility: actor is the doctor, the patient, or has ADMIN/SYSADMIN role.
"""

from __future__ import annotations

from app.db.models.account import Account, UserType
from app.db.models.appointment import Appointment


def can_view_appointment(actor: Account, appointment: Appointment) -> bool:
    """Return True if the actor is allowed to see the appointment."""
    if actor.user_type in (UserType.ADMIN, UserType.SYSADMIN):
        return True
    if actor.id == appointment.doctor_id:
        return True
    if actor.id == appointment.patient_id:
        return True
    return False
