"""ConsentGrant repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.consent import ConsentGrant
from app.db.repositories.base import Repository


class ConsentRepository(Repository[ConsentGrant]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ConsentGrant)

    def list_for_patient(self, patient_id: uuid.UUID) -> list[ConsentGrant]:
        result = self._session.execute(
            select(ConsentGrant).where(ConsentGrant.patient_id == patient_id)
        )
        return list(result.scalars().all())

    def list_active_for_patient_doctor(
        self, patient_id: uuid.UUID, doctor_id: uuid.UUID
    ) -> list[ConsentGrant]:
        result = self._session.execute(
            select(ConsentGrant).where(
                ConsentGrant.patient_id == patient_id,
                ConsentGrant.doctor_id == doctor_id,
                ConsentGrant.active.is_(True),
            )
        )
        return list(result.scalars().all())
