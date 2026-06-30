"""TASK-041: Group membership management tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.api.errors import AuthorizationError, NotFoundError
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.group import Group, GroupMembership, MembershipSource
from app.groups.auto_membership import sync_automatic_membership
from app.groups.service import GroupService


def _make_account(user_type: UserType, id: uuid.UUID | None = None) -> Account:
    return Account(
        id=id or uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _build_svc(
    group: Group | None = None,
    account: Account | None = None,
    existing_membership: GroupMembership | None = None,
    memberships: list[GroupMembership] | None = None,
) -> tuple[GroupService, MagicMock, MagicMock]:
    mock_group_repo = MagicMock()
    mock_group_repo.get.return_value = group
    mock_group_repo.get_membership.return_value = existing_membership
    mock_group_repo.memberships_for_account.return_value = memberships or []

    mock_account_repo = MagicMock()
    mock_account_repo.get_by_id.return_value = account

    mock_module_repo = MagicMock()
    mock_audit = MagicMock()

    mock_consent = MagicMock()
    mock_consent.has_active_grant.return_value = False
    authz_svc = AuthorizationService(mock_consent, MagicMock())

    svc = GroupService(mock_group_repo, mock_account_repo, mock_module_repo, mock_audit, authz_svc)
    return svc, mock_group_repo, mock_audit


def test_sysadmin_can_add_member() -> None:
    actor = _make_account(UserType.SYSADMIN)
    group = Group(id=uuid.uuid4(), name="Test")
    member = _make_account(UserType.PATIENT)
    svc, mock_group_repo, _ = _build_svc(group=group, account=member)
    svc.add_member(actor, group.id, member.id)
    mock_group_repo.add_membership.assert_called_once()


def test_add_member_group_not_found() -> None:
    actor = _make_account(UserType.SYSADMIN)
    svc, _, _ = _build_svc(group=None)
    with pytest.raises(NotFoundError):
        svc.add_member(actor, uuid.uuid4(), uuid.uuid4())


def test_add_member_account_not_found() -> None:
    actor = _make_account(UserType.SYSADMIN)
    group = Group(id=uuid.uuid4(), name="Test")
    svc, _, _ = _build_svc(group=group, account=None)
    with pytest.raises(NotFoundError):
        svc.add_member(actor, group.id, uuid.uuid4())


def test_add_member_idempotent_if_already_manual() -> None:
    actor = _make_account(UserType.SYSADMIN)
    group = Group(id=uuid.uuid4(), name="Test")
    member = _make_account(UserType.PATIENT)
    existing = GroupMembership(
        group_id=group.id, account_id=member.id, source=MembershipSource.MANUAL
    )
    svc, mock_group_repo, _ = _build_svc(group=group, account=member, existing_membership=existing)
    svc.add_member(actor, group.id, member.id)
    mock_group_repo.add_membership.assert_not_called()


def test_non_sysadmin_cannot_add_member() -> None:
    actor = _make_account(UserType.ADMIN)
    svc, _, _ = _build_svc()
    with pytest.raises(AuthorizationError):
        svc.add_member(actor, uuid.uuid4(), uuid.uuid4())


def test_sysadmin_can_remove_member() -> None:
    actor = _make_account(UserType.SYSADMIN)
    group_id = uuid.uuid4()
    account_id = uuid.uuid4()
    svc, mock_group_repo, _ = _build_svc()
    svc.remove_member(actor, group_id, account_id)
    mock_group_repo.remove_membership.assert_called_once_with(
        group_id, account_id, MembershipSource.MANUAL
    )


def test_non_sysadmin_cannot_remove_member() -> None:
    actor = _make_account(UserType.DOCTOR)
    svc, _, _ = _build_svc()
    with pytest.raises(AuthorizationError):
        svc.remove_member(actor, uuid.uuid4(), uuid.uuid4())


def test_groups_of_returns_groups_for_all_memberships() -> None:
    account_id = uuid.uuid4()
    group_id_1 = uuid.uuid4()
    group_id_2 = uuid.uuid4()
    memberships = [
        GroupMembership(group_id=group_id_1, account_id=account_id, source=MembershipSource.AUTO),
        GroupMembership(group_id=group_id_2, account_id=account_id, source=MembershipSource.MANUAL),
    ]
    g1 = Group(id=group_id_1, name="A")
    g2 = Group(id=group_id_2, name="B")

    svc, mock_group_repo, _ = _build_svc(memberships=memberships)
    mock_group_repo.get.side_effect = lambda gid: g1 if gid == group_id_1 else g2

    result = svc.groups_of(account_id)
    assert len(result) == 2


def test_add_member_emits_audit() -> None:
    actor = _make_account(UserType.SYSADMIN)
    group = Group(id=uuid.uuid4(), name="Test")
    member = _make_account(UserType.PATIENT)
    svc, _, mock_audit = _build_svc(group=group, account=member)
    svc.add_member(actor, group.id, member.id)
    mock_audit.record.assert_called()
    assert "GROUP_MEMBER_ADD" in str(mock_audit.record.call_args)


def test_remove_member_emits_audit() -> None:
    actor = _make_account(UserType.SYSADMIN)
    svc, _, mock_audit = _build_svc()
    svc.remove_member(actor, uuid.uuid4(), uuid.uuid4())
    mock_audit.record.assert_called()
    assert "GROUP_MEMBER_REMOVE" in str(mock_audit.record.call_args)


# --- TASK-041: sync_automatic_membership tests ---


def _make_auto_group(auto_user_type: UserType | None = None) -> Group:
    return Group(id=uuid.uuid4(), name="AutoGroup", auto_user_type=auto_user_type)


def test_sync_auto_membership_assigns_matching_group() -> None:
    """Account with matching user_type gets AUTO membership added."""
    account = _make_account(UserType.DOCTOR)
    group = _make_auto_group(auto_user_type=UserType.DOCTOR)

    mock_repo = MagicMock()
    mock_repo.list_auto_groups_for_type.return_value = [group]
    mock_repo.memberships_for_account.return_value = []  # no existing auto memberships

    sync_automatic_membership(account, mock_repo)

    mock_repo.add_membership.assert_called_once()
    added = mock_repo.add_membership.call_args[0][0]
    assert added.group_id == group.id
    assert added.account_id == account.id
    assert added.source == MembershipSource.AUTO


def test_sync_auto_membership_removes_stale_group() -> None:
    """When user type changes, old AUTO membership is removed."""
    account = _make_account(UserType.PATIENT)  # now a patient
    old_group = _make_auto_group(auto_user_type=UserType.DOCTOR)  # was a doctor group

    old_membership = GroupMembership(
        group_id=old_group.id, account_id=account.id, source=MembershipSource.AUTO
    )

    mock_repo = MagicMock()
    mock_repo.list_auto_groups_for_type.return_value = []  # no groups for PATIENT
    mock_repo.memberships_for_account.return_value = [old_membership]

    sync_automatic_membership(account, mock_repo)

    # Should remove the stale AUTO membership
    mock_repo.remove_membership.assert_called_once_with(
        old_group.id, account.id, MembershipSource.AUTO
    )
    # No new memberships added
    mock_repo.add_membership.assert_not_called()


def test_sync_auto_membership_does_not_touch_manual_memberships() -> None:
    """MANUAL memberships are not affected by sync."""
    account = _make_account(UserType.DOCTOR)
    auto_group = _make_auto_group(auto_user_type=UserType.DOCTOR)

    manual_membership = GroupMembership(
        group_id=uuid.uuid4(), account_id=account.id, source=MembershipSource.MANUAL
    )

    mock_repo = MagicMock()
    mock_repo.list_auto_groups_for_type.return_value = [auto_group]
    mock_repo.memberships_for_account.return_value = [manual_membership]

    sync_automatic_membership(account, mock_repo)

    # Only the AUTO group should be added; MANUAL untouched
    mock_repo.add_membership.assert_called_once()
    added = mock_repo.add_membership.call_args[0][0]
    assert added.group_id == auto_group.id
    # remove_membership NOT called for the manual membership
    mock_repo.remove_membership.assert_not_called()
