"""Automatic group membership based on UserType (TASK-041).

Groups with auto_user_type set are automatically assigned to matching accounts
on activation. This module provides the data-driven sync logic.
"""

from __future__ import annotations

from app.db.models.account import Account
from app.db.models.group import GroupMembership, MembershipSource
from app.db.repositories.group_repo import GroupRepository


def sync_automatic_membership(account: Account, group_repo: GroupRepository) -> None:
    """Assign AUTO memberships for groups matching account.user_type.

    Removes AUTO memberships for groups that no longer match. MANUAL memberships
    are never touched.
    """
    # Groups this account should belong to automatically
    target_groups = group_repo.list_auto_groups_for_type(account.user_type)
    target_group_ids = {g.id for g in target_groups}

    # Current AUTO memberships for the account
    all_memberships = group_repo.memberships_for_account(account.id)
    auto_memberships = [m for m in all_memberships if m.source == MembershipSource.AUTO]
    current_auto_group_ids = {m.group_id for m in auto_memberships}

    # Add missing AUTO memberships
    for group_id in target_group_ids - current_auto_group_ids:
        membership = GroupMembership(
            group_id=group_id,
            account_id=account.id,
            source=MembershipSource.AUTO,
        )
        group_repo.add_membership(membership)

    # Remove AUTO memberships that no longer match
    for group_id in current_auto_group_ids - target_group_ids:
        group_repo.remove_membership(group_id, account.id, MembershipSource.AUTO)
