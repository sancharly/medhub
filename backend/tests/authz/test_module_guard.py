"""TASK-043: ModuleAccessGuard tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from app.authz.module_guard import ModuleAccessGuard
from app.db.models.group import GroupMembership, MembershipSource


def _build_guard(
    memberships: list[GroupMembership] | None = None,
    enabled_keys: list[str] | None = None,
) -> ModuleAccessGuard:
    mock_group_repo = MagicMock()
    mock_group_repo.memberships_for_account.return_value = memberships or []

    mock_module_repo = MagicMock()
    mock_module_repo.enabled_module_keys_for_groups.return_value = enabled_keys or []

    return ModuleAccessGuard(mock_group_repo, mock_module_repo)


def test_no_memberships_returns_false() -> None:
    guard = _build_guard(memberships=[])
    assert guard.is_module_enabled(uuid.uuid4(), "dicom") is False


def test_module_enabled_in_group_returns_true() -> None:
    group_id = uuid.uuid4()
    account_id = uuid.uuid4()
    membership = GroupMembership(
        group_id=group_id, account_id=account_id, source=MembershipSource.AUTO
    )
    guard = _build_guard(memberships=[membership], enabled_keys=["dicom"])
    assert guard.is_module_enabled(account_id, "dicom") is True


def test_module_not_enabled_returns_false() -> None:
    group_id = uuid.uuid4()
    account_id = uuid.uuid4()
    membership = GroupMembership(
        group_id=group_id, account_id=account_id, source=MembershipSource.AUTO
    )
    guard = _build_guard(memberships=[membership], enabled_keys=["other_module"])
    assert guard.is_module_enabled(account_id, "dicom") is False


def test_unknown_module_key_returns_false() -> None:
    group_id = uuid.uuid4()
    account_id = uuid.uuid4()
    membership = GroupMembership(
        group_id=group_id, account_id=account_id, source=MembershipSource.AUTO
    )
    guard = _build_guard(memberships=[membership], enabled_keys=[])
    assert guard.is_module_enabled(account_id, "nonexistent") is False


def test_group_ids_passed_to_module_repo() -> None:
    group_id_1 = uuid.uuid4()
    group_id_2 = uuid.uuid4()
    account_id = uuid.uuid4()
    memberships = [
        GroupMembership(group_id=group_id_1, account_id=account_id, source=MembershipSource.AUTO),
        GroupMembership(group_id=group_id_2, account_id=account_id, source=MembershipSource.MANUAL),
    ]
    mock_group_repo = MagicMock()
    mock_group_repo.memberships_for_account.return_value = memberships
    mock_module_repo = MagicMock()
    mock_module_repo.enabled_module_keys_for_groups.return_value = ["dicom"]

    guard = ModuleAccessGuard(mock_group_repo, mock_module_repo)
    guard.is_module_enabled(account_id, "dicom")

    called_group_ids = mock_module_repo.enabled_module_keys_for_groups.call_args[0][0]
    assert set(called_group_ids) == {group_id_1, group_id_2}
