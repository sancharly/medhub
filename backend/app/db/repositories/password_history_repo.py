"""PasswordHistory repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.password_history import PasswordHistory
from app.db.repositories.base import Repository


class PasswordHistoryRepository(Repository[PasswordHistory]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, PasswordHistory)

    def list_recent(self, account_id: uuid.UUID, limit: int) -> list[PasswordHistory]:
        """Return the most recent `limit` password history entries for an account."""
        result = self._session.execute(
            select(PasswordHistory)
            .where(PasswordHistory.account_id == account_id)
            .order_by(PasswordHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
