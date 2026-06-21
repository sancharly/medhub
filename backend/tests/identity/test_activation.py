"""TASK-032: Account activation tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.api.errors import AuthorizationError, UnauthenticatedError
from app.auth.password import PasswordService
from app.db.models.account import Account, AccountStatus, UserType
from app.identity.activation import ActivationService, issue_activation_token


def _make_inactive_account() -> Account:
    acct = Account(
        id=uuid.uuid4(),
        email="user@example.com",
        user_type=UserType.PATIENT,
        status=AccountStatus.INACTIVE,
    )
    return acct


def _build_svc(account: Account | None) -> ActivationService:
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = account
    pw_svc = PasswordService()
    mock_audit = MagicMock()
    return ActivationService(mock_repo, pw_svc, mock_audit)


VALID_PW = "Str0ng!Pass#99"


def test_issue_activation_token_stores_hash() -> None:
    acct = _make_inactive_account()
    raw = issue_activation_token(acct)
    assert acct.activation_token_hash is not None
    assert raw not in acct.activation_token_hash  # hash ≠ raw token
    assert acct.activation_token_expires_at is not None


def test_issue_activation_token_expires_in_72h() -> None:
    acct = _make_inactive_account()
    before = datetime.now(UTC)
    issue_activation_token(acct)
    assert acct.activation_token_expires_at > before + timedelta(hours=71)
    assert acct.activation_token_expires_at < before + timedelta(hours=73)


def test_activate_sets_active_and_clears_token() -> None:
    acct = _make_inactive_account()
    raw = issue_activation_token(acct)
    svc = _build_svc(acct)

    result = svc.activate(acct.id, raw, VALID_PW)

    assert result.status == AccountStatus.ACTIVE
    assert result.activation_token_hash is None
    assert result.activation_token_expires_at is None


def test_activate_stores_hashed_password() -> None:
    acct = _make_inactive_account()
    raw = issue_activation_token(acct)
    svc = _build_svc(acct)

    result = svc.activate(acct.id, raw, VALID_PW)
    assert result.password_hash is not None
    assert result.password_hash.startswith("$argon2id$")


def test_activate_wrong_token_raises() -> None:
    acct = _make_inactive_account()
    issue_activation_token(acct)
    svc = _build_svc(acct)
    with pytest.raises(UnauthenticatedError):
        svc.activate(acct.id, "wrong-token", VALID_PW)


def test_activate_expired_token_raises() -> None:
    acct = _make_inactive_account()
    raw = issue_activation_token(acct)
    # Expire the token
    acct.activation_token_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    svc = _build_svc(acct)
    with pytest.raises(UnauthenticatedError):
        svc.activate(acct.id, raw, VALID_PW)


def test_activate_already_active_account_raises() -> None:
    acct = _make_inactive_account()
    acct.status = AccountStatus.ACTIVE
    raw = issue_activation_token(acct)
    svc = _build_svc(acct)
    with pytest.raises(UnauthenticatedError):
        svc.activate(acct.id, raw, VALID_PW)


def test_activate_audits_event() -> None:
    acct = _make_inactive_account()
    raw = issue_activation_token(acct)
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = acct
    mock_audit = MagicMock()
    svc = ActivationService(mock_repo, PasswordService(), mock_audit)

    svc.activate(acct.id, raw, VALID_PW)
    mock_audit.record.assert_called_once()
    assert "ACCOUNT_ACTIVATED" in str(mock_audit.record.call_args)


def test_resend_activation_admin_only() -> None:
    acct = _make_inactive_account()
    actor = Account(
        id=uuid.uuid4(),
        email="patient@example.com",
        user_type=UserType.PATIENT,
        status=AccountStatus.ACTIVE,
    )
    svc = _build_svc(acct)
    with pytest.raises(AuthorizationError):
        svc.resend_activation(actor, acct.id)


def test_resend_activation_invalidates_old_token() -> None:
    acct = _make_inactive_account()
    first_raw = issue_activation_token(acct)
    first_hash = acct.activation_token_hash

    actor = Account(
        id=uuid.uuid4(),
        email="admin@example.com",
        user_type=UserType.ADMIN,
        status=AccountStatus.ACTIVE,
    )
    svc = _build_svc(acct)
    new_raw = svc.resend_activation(actor, acct.id)

    assert acct.activation_token_hash != first_hash
    assert new_raw != first_raw
