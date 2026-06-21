"""ClinicalEntry repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.clinical import ClinicalEntry
from app.db.repositories.base import Repository


class ClinicalRepository(Repository[ClinicalEntry]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ClinicalEntry)

    def list_for_patient(self, patient_id: uuid.UUID) -> list[ClinicalEntry]:
        result = self._session.execute(
            select(ClinicalEntry).where(ClinicalEntry.patient_id == patient_id)
        )
        return list(result.scalars().all())
