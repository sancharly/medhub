"""Appointment repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

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

    def list_all(self) -> list[Appointment]:
        result = self._session.execute(select(Appointment))
        return list(result.scalars().all())

    def update_state(self, appointment: Appointment, new_state: object) -> None:
        appointment.state = new_state  # type: ignore[assignment]
        self._session.flush()
