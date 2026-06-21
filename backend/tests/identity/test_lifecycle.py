"""TASK-033: Account lifecycle tests."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import fakeredis
import pytest

from app.api.errors import AuthorizationError
from app.auth.session import SessionService
from app.db.models.account import Account, AccountStatus, UserType
from app.identity.lifecycle import LifecycleService


def _make_account(user_type: UserType) -> Account:
    return Account(
        id=uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _build_svc(target: Account | None) -> tuple[LifecycleService, MagicMock]:
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = target
    r = fakeredis.FakeRedis()
    session_svc = SessionService(r)
    mock_audit = MagicMock()
    svc = LifecycleService(mock_repo, session_svc, mock_audit)
    return svc, mock_audit


def test_sysadmin_can_deactivate() -> None:
    actor = _make_account(UserType.SYSADMIN)
    target = _make_account(UserType.PATIENT)
    svc, mock_audit = _build_svc(target)
    svc.deactivate(actor, target.id)
    assert target.status == AccountStatus.DEACTIVATED


def test_deactivate_non_sysadmin_raises() -> None:
    actor = _make_account(UserType.ADMIN)
    target = _make_account(UserType.PATIENT)
    svc, _ = _build_svc(target)
    with pytest.raises(AuthorizationError):
        svc.deactivate(actor, target.id)


def test_deactivate_self_raises() -> None:
    actor = _make_account(UserType.SYSADMIN)
    svc, _ = _build_svc(actor)
    with pytest.raises(AuthorizationError):
        svc.deactivate(actor, actor.id)


def test_deactivate_audits_event() -> None:
    actor = _make_account(UserType.SYSADMIN)
    target = _make_account(UserType.PATIENT)
    svc, mock_audit = _build_svc(target)
    svc.deactivate(actor, target.id)
    assert "ACCOUNT_DEACTIVATED" in str(mock_audit.record.call_args)


def test_sysadmin_can_reactivate() -> None:
    actor = _make_account(UserType.SYSADMIN)
    target = _make_account(UserType.PATIENT)
    target.status = AccountStatus.DEACTIVATED
    svc, _ = _build_svc(target)
    svc.reactivate(actor, target.id)
    assert target.status == AccountStatus.ACTIVE


def test_reactivate_non_sysadmin_raises() -> None:
    actor = _make_account(UserType.ADMIN)
    target = _make_account(UserType.PATIENT)
    svc, _ = _build_svc(target)
    with pytest.raises(AuthorizationError):
        svc.reactivate(actor, target.id)


def test_reactivate_audits_event() -> None:
    actor = _make_account(UserType.SYSADMIN)
    target = _make_account(UserType.PATIENT)
    svc, mock_audit = _build_svc(target)
    svc.reactivate(actor, target.id)
    assert "ACCOUNT_REACTIVATED" in str(mock_audit.record.call_args)


def test_deactivate_flush_called_before_invalidate_all() -> None:
    """DB flush must happen before session invalidation to avoid inconsistent state."""
    call_order: list[str] = []

    actor = _make_account(UserType.SYSADMIN)
    target = _make_account(UserType.PATIENT)

    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = target
    mock_repo.flush.side_effect = lambda: call_order.append("flush")

    mock_session_svc = MagicMock()
    mock_session_svc.invalidate_all.side_effect = lambda _: call_order.append("invalidate_all")

    mock_audit = MagicMock()

    svc = LifecycleService(mock_repo, mock_session_svc, mock_audit)
    svc.deactivate(actor, target.id)

    assert "flush" in call_order
    assert "invalidate_all" in call_order
    assert call_order.index("flush") < call_order.index("invalidate_all")
