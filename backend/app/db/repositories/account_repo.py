"""Account repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.account import Account
from app.db.repositories.base import Repository


class AccountRepository(Repository[Account]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Account)

    def get_by_id(self, id: uuid.UUID) -> Account | None:
        return self.get(id)

    def get_by_email(self, email: str) -> Account | None:
        result = self._session.execute(select(Account).where(Account.email == email))
        return result.scalar_one_or_none()
