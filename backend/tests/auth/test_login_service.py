"""TASK-023: LoginService tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from fastapi.responses import Response

from app.auth.login import LoginFailure, LoginService, LoginSuccess
from app.auth.password import PasswordService
from app.auth.session import CreateSessionResult, Session, SessionService
from app.db.models.account import Account, AccountStatus, UserType


def _make_account(
    status: AccountStatus = AccountStatus.ACTIVE,
    password: str = "Str0ng!Pass#99",
) -> tuple[Account, str]:
    svc = PasswordService()
    pw_hash = svc.hash(password)
    acct = Account(
        id=uuid.uuid4(),
        email="user@example.com",
        user_type=UserType.PATIENT,
        status=status,
        password_hash=pw_hash,
    )
    return acct, password


def _make_session(account: Account) -> Session:
    now = datetime.now(UTC)
    return Session(
        session_id="sess-abc",
        account_id=account.id,
        role=account.user_type,
        created_at=now,
        last_seen_at=now,
        ip="1.1.1.1",
        absolute_expires_at=now + timedelta(hours=8),
    )


def _build_svc(account: Account | None, session: Session | None = None) -> LoginService:
    mock_repo = MagicMock()
    mock_repo.get_by_email.return_value = account

    pw_svc = PasswordService()

    mock_session_svc = MagicMock(spec=SessionService)
    if account and session:
        mock_session_svc.create_session.return_value = CreateSessionResult(
            session=session, evicted_session_id=None
        )

    mock_audit = MagicMock()

    return LoginService(
        account_repo=mock_repo,
        password_svc=pw_svc,
        session_svc=mock_session_svc,
        audit_svc=mock_audit,
    )


# --- success ---

def test_login_success_returns_session_and_csrf() -> None:
    acct, pw = _make_account()
    session = _make_session(acct)
    svc = _build_svc(acct, session)
    resp = Response()
    result = svc.login("user@example.com", pw, "1.1.1.1", resp)
    assert isinstance(result, LoginSuccess)
    assert result.session is not None
    assert result.csrf_token is not None


def test_login_normalises_email() -> None:
    acct, pw = _make_account()
    mock_repo = MagicMock()
    mock_repo.get_by_email.return_value = acct
    pw_svc = PasswordService()
    session = _make_session(acct)
    mock_session_svc = MagicMock(spec=SessionService)
    mock_session_svc.create_session.return_value = CreateSessionResult(
        session=session, evicted_session_id=None
    )
    svc = LoginService(mock_repo, pw_svc, mock_session_svc, MagicMock())
    svc.login("  USER@EXAMPLE.COM  ", pw, None, Response())
    mock_repo.get_by_email.assert_called_once_with("user@example.com")


def test_login_success_audits_success() -> None:
    acct, pw = _make_account()
    session = _make_session(acct)
    mock_repo = MagicMock()
    mock_repo.get_by_email.return_value = acct
    mock_session_svc = MagicMock(spec=SessionService)
    mock_session_svc.create_session.return_value = CreateSessionResult(
        session=session, evicted_session_id=None
    )
    mock_audit = MagicMock()

    svc = LoginService(mock_repo, PasswordService(), mock_session_svc, mock_audit)
    svc.login("user@example.com", pw, "1.2.3.4", Response())

    mock_audit.record.assert_called()
    call_kwargs = mock_audit.record.call_args
    assert "LOGIN_SUCCESS" in str(call_kwargs)


# --- failures ---

def test_login_wrong_password_returns_failure() -> None:
    acct, _ = _make_account()
    svc = _build_svc(acct)
    result = svc.login("user@example.com", "WrongP@ssword1!", "1.1.1.1", Response())
    assert isinstance(result, LoginFailure)


def test_login_account_not_found_returns_generic_failure() -> None:
    svc = _build_svc(account=None)
    result = svc.login("nobody@example.com", "SomeP@ss123!", None, Response())
    assert isinstance(result, LoginFailure)


def test_login_inactive_account_returns_failure() -> None:
    acct, pw = _make_account(status=AccountStatus.INACTIVE)
    svc = _build_svc(acct)
    result = svc.login("user@example.com", pw, None, Response())
    assert isinstance(result, LoginFailure)


def test_login_deactivated_account_returns_failure() -> None:
    acct, pw = _make_account(status=AccountStatus.DEACTIVATED)
    svc = _build_svc(acct)
    result = svc.login("user@example.com", pw, None, Response())
    assert isinstance(result, LoginFailure)


def test_login_failure_audits_failure() -> None:
    acct, _ = _make_account()
    mock_repo = MagicMock()
    mock_repo.get_by_email.return_value = acct
    mock_audit = MagicMock()
    svc = LoginService(mock_repo, PasswordService(), MagicMock(), mock_audit)
    svc.login("user@example.com", "WrongP@ss1!", None, Response())
    mock_audit.record.assert_called()
    call_kwargs = str(mock_audit.record.call_args)
    assert "LOGIN_FAILURE" in call_kwargs


def test_login_failure_never_leaks_password_in_audit() -> None:
    """Audit records must not contain the attempted password."""
    acct, _ = _make_account()
    mock_repo = MagicMock()
    mock_repo.get_by_email.return_value = acct
    mock_audit = MagicMock()
    svc = LoginService(mock_repo, PasswordService(), MagicMock(), mock_audit)
    svc.login("user@example.com", "SecretAttempt!123", None, Response())
    for call in mock_audit.record.call_args_list:
        assert "SecretAttempt!123" not in str(call)


def test_login_sets_session_cookie() -> None:
    acct, pw = _make_account()
    session = _make_session(acct)
    svc = _build_svc(acct, session)
    resp = Response()
    svc.login("user@example.com", pw, None, resp)
    cookie_headers = resp.headers.get("set-cookie", "")
    assert "medhub_session" in cookie_headers
