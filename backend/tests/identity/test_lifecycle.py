"""TASK-033: Account lifecycle tests."""

from __future__ import annotations

import logging
import uuid
from unittest.mock import MagicMock, patch

import fakeredis
import pytest

from app.api.errors import AuthorizationError
from app.auth.session import SessionService
from app.authz.service import AuthorizationService
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
    svc = LifecycleService(
        mock_repo, session_svc, mock_audit, AuthorizationService(MagicMock(), MagicMock())
    )
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

    svc = LifecycleService(
        mock_repo, mock_session_svc, mock_audit, AuthorizationService(MagicMock(), MagicMock())
    )
    svc.deactivate(actor, target.id)

    assert "flush" in call_order
    assert "invalidate_all" in call_order
    assert call_order.index("flush") < call_order.index("invalidate_all")


def test_deactivate_logs_a_warning_when_enqueue_fails(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TASK-207 (PRB-013 call site): a failed enqueue is logged with the id only and the
    deactivation still succeeds."""
    # An Alembic ``fileConfig`` in another test can leave existing loggers disabled.
    monkeypatch.setattr(logging.getLogger("app.identity.lifecycle"), "disabled", False)
    actor = _make_account(UserType.SYSADMIN)
    target = _make_account(UserType.PATIENT)
    svc, _ = _build_svc(target)
    with (
        patch("app.workers.session_tasks.propagate_session_kill") as task,
        caplog.at_level(logging.WARNING, logger="app.identity.lifecycle"),
    ):
        task.delay.side_effect = RuntimeError("redis://:hunter2@broker:6379/0 unreachable")
        svc.deactivate(actor, target.id)
    assert target.status == AccountStatus.DEACTIVATED
    records = [r for r in caplog.records if r.name == "app.identity.lifecycle"]
    assert len(records) == 1
    assert records[0].levelno == logging.WARNING
    assert str(target.id) in records[0].getMessage()
    assert records[0].exc_info is None
    assert "hunter2" not in caplog.text
