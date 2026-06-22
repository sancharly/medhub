"""Group and GroupMembership repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.group import Group, GroupMembership, MembershipSource
from app.db.repositories.base import Repository


class GroupRepository(Repository[Group]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Group)

    def get_by_name(self, name: str) -> Group | None:
        result = self._session.execute(select(Group).where(Group.name == name))
        return result.scalar_one_or_none()

    def list_all(self) -> list[Group]:
        result = self._session.execute(select(Group))
        return list(result.scalars().all())

    def get_membership(self, group_id: uuid.UUID, account_id: uuid.UUID) -> GroupMembership | None:
        return self._session.get(GroupMembership, (group_id, account_id))

    def add_membership(self, membership: GroupMembership) -> GroupMembership:
        self._session.add(membership)
        self._session.flush()
        return membership

    def remove_membership(
        self, group_id: uuid.UUID, account_id: uuid.UUID, source: MembershipSource
    ) -> None:
        """Remove the membership row matching the given source only."""
        result = self._session.execute(
            select(GroupMembership).where(
                GroupMembership.group_id == group_id,
                GroupMembership.account_id == account_id,
                GroupMembership.source == source,
            )
        )
        membership = result.scalar_one_or_none()
        if membership is not None:
            self._session.delete(membership)
            self._session.flush()

    def memberships_for_account(self, account_id: uuid.UUID) -> list[GroupMembership]:
        result = self._session.execute(
            select(GroupMembership).where(GroupMembership.account_id == account_id)
        )
        return list(result.scalars().all())

    def members_of_group(self, group_id: uuid.UUID) -> list[GroupMembership]:
        result = self._session.execute(
            select(GroupMembership).where(GroupMembership.group_id == group_id)
        )
        return list(result.scalars().all())

    def list_auto_groups_for_type(self, user_type: object) -> list[Group]:
        result = self._session.execute(select(Group).where(Group.auto_user_type == user_type))
        return list(result.scalars().all())
