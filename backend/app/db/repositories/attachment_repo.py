"""Attachment repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.attachment import Attachment
from app.db.repositories.base import Repository


class AttachmentRepository(Repository[Attachment]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Attachment)

    def list_for_clinical_entry(self, clinical_entry_id: uuid.UUID) -> list[Attachment]:
        result = self._session.execute(
            select(Attachment).where(Attachment.clinical_entry_id == clinical_entry_id)
        )
        return list(result.scalars().all())
