"""TASK-042: Module enablement tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from app.api.errors import AuthorizationError, NotFoundError
from app.authz.service import AuthorizationService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.group import Group
from app.db.models.module import ModuleRegistry
from app.groups.service import GroupService


def _make_account(user_type: UserType) -> Account:
    return Account(
        id=uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _build_svc(
    group: Group | None = None,
    module: ModuleRegistry | None = None,
) -> tuple[GroupService, MagicMock, MagicMock]:
    mock_group_repo = MagicMock()
    mock_group_repo.get.return_value = group

    mock_account_repo = MagicMock()

    mock_module_repo = MagicMock()
    mock_module_repo.get_by_key.return_value = module

    mock_audit = MagicMock()

    mock_consent = MagicMock()
    mock_consent.has_active_grant.return_value = False
    authz_svc = AuthorizationService(mock_consent, MagicMock())

    svc = GroupService(mock_group_repo, mock_account_repo, mock_module_repo, mock_audit, authz_svc)
    return svc, mock_module_repo, mock_audit


def test_sysadmin_can_enable_module() -> None:
    actor = _make_account(UserType.SYSADMIN)
    group = Group(id=uuid.uuid4(), name="Test")
    module = ModuleRegistry(id=uuid.uuid4(), module_key="dicom", name="DICOM", version="1.0")
    svc, mock_module_repo, _ = _build_svc(group=group, module=module)
    svc.set_module_enabled(actor, group.id, "dicom", enabled=True)
    mock_module_repo.set_enablement.assert_called_once_with(group.id, module.id, True)


def test_sysadmin_can_disable_module() -> None:
    actor = _make_account(UserType.SYSADMIN)
    group = Group(id=uuid.uuid4(), name="Test")
    module = ModuleRegistry(id=uuid.uuid4(), module_key="dicom", name="DICOM", version="1.0")
    svc, mock_module_repo, _ = _build_svc(group=group, module=module)
    svc.set_module_enabled(actor, group.id, "dicom", enabled=False)
    mock_module_repo.set_enablement.assert_called_once_with(group.id, module.id, False)


def test_set_module_enabled_group_not_found() -> None:
    actor = _make_account(UserType.SYSADMIN)
    svc, _, _ = _build_svc(group=None)
    with pytest.raises(NotFoundError):
        svc.set_module_enabled(actor, uuid.uuid4(), "dicom", enabled=True)


def test_set_module_enabled_module_not_found() -> None:
    actor = _make_account(UserType.SYSADMIN)
    group = Group(id=uuid.uuid4(), name="Test")
    svc, _, _ = _build_svc(group=group, module=None)
    with pytest.raises(NotFoundError):
        svc.set_module_enabled(actor, group.id, "unknown_module", enabled=True)


def test_non_sysadmin_cannot_set_module_enabled() -> None:
    actor = _make_account(UserType.ADMIN)
    svc, _, _ = _build_svc()
    with pytest.raises(AuthorizationError):
        svc.set_module_enabled(actor, uuid.uuid4(), "dicom", enabled=True)


def test_enable_module_emits_audit() -> None:
    actor = _make_account(UserType.SYSADMIN)
    group = Group(id=uuid.uuid4(), name="Test")
    module = ModuleRegistry(id=uuid.uuid4(), module_key="dicom", name="DICOM", version="1.0")
    svc, _, mock_audit = _build_svc(group=group, module=module)
    svc.set_module_enabled(actor, group.id, "dicom", enabled=True)
    mock_audit.record.assert_called()
    assert "MODULE_ENABLE" in str(mock_audit.record.call_args)


def test_disable_module_emits_disable_audit() -> None:
    actor = _make_account(UserType.SYSADMIN)
    group = Group(id=uuid.uuid4(), name="Test")
    module = ModuleRegistry(id=uuid.uuid4(), module_key="dicom", name="DICOM", version="1.0")
    svc, _, mock_audit = _build_svc(group=group, module=module)
    svc.set_module_enabled(actor, group.id, "dicom", enabled=False)
    assert "MODULE_DISABLE" in str(mock_audit.record.call_args)
