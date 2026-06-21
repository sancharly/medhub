"""Appointment repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.account import Account, UserType
from app.db.models.appointment import Appointment
from app.db.repositories.base import Repository


class AppointmentRepository(Repository[Appointment]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Appointment)

    def list_for_doctor(self, doctor_id: uuid.UUID) -> list[Appointment]:
        result = self._session.execute(
            select(Appointment).where(Appointment.doctor_id == doctor_id)
        )
        return list(result.scalars().all())

    def list_for_patient(self, patient_id: uuid.UUID) -> list[Appointment]:
        result = self._session.execute(
            select(Appointment).where(Appointment.patient_id == patient_id)
        )
        return list(result.scalars().all())

    def list_for_actor(self, actor: Account) -> list[Appointment]:
        """Return appointments visible to the actor based on their role."""
        if actor.user_type in (UserType.ADMIN, UserType.SYSADMIN):
            result = self._session.execute(select(Appointment))
            return list(result.scalars().all())
        if actor.user_type == UserType.DOCTOR:
            return self.list_for_doctor(actor.id)
        if actor.user_type == UserType.PATIENT:
            return self.list_for_patient(actor.id)
        return []

    def update_state(self, appointment: Appointment, new_state: object) -> None:
        appointment.state = new_state  # type: ignore[assignment]
        self._session.flush()
