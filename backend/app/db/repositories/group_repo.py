"""Group and GroupMembership repository."""

import uuid

from sqlalchemy.orm import Session

from app.db.models.group import Group, GroupMembership
from app.db.repositories.base import Repository


class GroupRepository(Repository[Group]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Group)

    def get_membership(self, group_id: uuid.UUID, account_id: uuid.UUID) -> GroupMembership | None:
        return self._session.get(GroupMembership, (group_id, account_id))

    def add_membership(self, membership: GroupMembership) -> GroupMembership:
        self._session.add(membership)
        self._session.flush()
        return membership
