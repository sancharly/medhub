"""TASK-040: GroupService create_group and list_groups tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.api.errors import AuthorizationError, ConflictError, ValidationProblem
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.group import Group
from app.groups.service import GroupService


def _make_account(user_type: UserType) -> Account:
    return Account(
        id=uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _build_svc(
    existing_group: Group | None = None,
    groups: list[Group] | None = None,
) -> tuple[GroupService, MagicMock, MagicMock]:
    mock_group_repo = MagicMock()
    mock_group_repo.get_by_name.return_value = existing_group
    mock_group_repo.list_all.return_value = groups or []
    new_group = Group(id=uuid.uuid4(), name="test-group")
    mock_group_repo.add.return_value = new_group

    mock_account_repo = MagicMock()
    mock_module_repo = MagicMock()
    mock_audit = MagicMock()

    mock_consent = MagicMock()
    mock_consent.has_active_grant.return_value = False
    authz_svc = AuthorizationService(mock_consent, MagicMock())

    svc = GroupService(mock_group_repo, mock_account_repo, mock_module_repo, mock_audit, authz_svc)
    return svc, mock_group_repo, mock_audit


def test_sysadmin_creates_group_persisted() -> None:
    actor = _make_account(UserType.SYSADMIN)
    svc, mock_group_repo, _ = _build_svc()
    svc.create_group(actor, "Physicians")
    mock_group_repo.add.assert_called_once()


def test_create_group_trims_name() -> None:
    actor = _make_account(UserType.SYSADMIN)
    svc, mock_group_repo, _ = _build_svc()
    svc.create_group(actor, "  Physicians  ")
    call_args = mock_group_repo.add.call_args[0][0]
    assert call_args.name == "Physicians"


def test_create_group_emits_audit() -> None:
    actor = _make_account(UserType.SYSADMIN)
    svc, _, mock_audit = _build_svc()
    svc.create_group(actor, "Physicians")
    mock_audit.record.assert_called()
    call_str = str(mock_audit.record.call_args)
    assert "GROUP_CREATE" in call_str


def test_create_group_blank_name_raises_validation() -> None:
    actor = _make_account(UserType.SYSADMIN)
    svc, _, _ = _build_svc()
    with pytest.raises(ValidationProblem):
        svc.create_group(actor, "   ")


def test_create_group_whitespace_only_raises_validation() -> None:
    actor = _make_account(UserType.SYSADMIN)
    svc, _, _ = _build_svc()
    with pytest.raises(ValidationProblem):
        svc.create_group(actor, "")


def test_create_group_duplicate_raises_conflict() -> None:
    actor = _make_account(UserType.SYSADMIN)
    svc, mock_group_repo, _ = _build_svc()
    mock_group_repo.add.side_effect = IntegrityError("uq_group_name", {}, Exception())
    with pytest.raises(ConflictError):
        svc.create_group(actor, "Physicians")


def test_doctor_cannot_create_group() -> None:
    actor = _make_account(UserType.DOCTOR)
    svc, _, _ = _build_svc()
    with pytest.raises(AuthorizationError):
        svc.create_group(actor, "Physicians")


def test_patient_cannot_create_group() -> None:
    actor = _make_account(UserType.PATIENT)
    svc, _, _ = _build_svc()
    with pytest.raises(AuthorizationError):
        svc.create_group(actor, "Physicians")


def test_admin_cannot_create_group() -> None:
    actor = _make_account(UserType.ADMIN)
    svc, _, _ = _build_svc()
    with pytest.raises(AuthorizationError):
        svc.create_group(actor, "Physicians")


def test_list_groups_returns_all() -> None:
    actor = _make_account(UserType.SYSADMIN)
    g1 = Group(id=uuid.uuid4(), name="A")
    g2 = Group(id=uuid.uuid4(), name="B")
    svc, _, _ = _build_svc(groups=[g1, g2])
    result = svc.list_groups(actor)
    assert len(result) == 2


def test_non_sysadmin_cannot_list_groups() -> None:
    actor = _make_account(UserType.ADMIN)
    svc, _, _ = _build_svc()
    with pytest.raises(AuthorizationError):
        svc.list_groups(actor)
