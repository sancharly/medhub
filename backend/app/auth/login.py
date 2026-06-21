"""LoginService — full login flow with anti-enumeration (TASK-023).

Flow:
  1. Normalise email
  2. Look up account (always call PasswordService.verify even if not found)
  3. Generic failure for: not found, wrong password, INACTIVE, DEACTIVATED, locked
  4. On success: reset lockout, create session, set cookies, audit
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fastapi import Response

from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.auth.cookies import set_session_cookie
from app.auth.csrf import issue_csrf_token
from app.auth.password import PasswordService, get_dummy_hash
from app.auth.session import Session, SessionService
from app.db.models.account import Account, AccountStatus
from app.db.models.audit import AuditOutcome
from app.db.repositories.account_repo import AccountRepository

_GENERIC_FAILURE = "Invalid credentials."


@dataclass
class LoginSuccess:
    kind: Literal["success"] = "success"
    session: Session | None = None
    csrf_token: str | None = None


@dataclass
class LoginFailure:
    kind: Literal["failure"] = "failure"
    # Never expose WHY it failed to the caller
    detail: str = _GENERIC_FAILURE


LoginResult = LoginSuccess | LoginFailure


class LoginService:
    def __init__(
        self,
        account_repo: AccountRepository,
        password_svc: PasswordService,
        session_svc: SessionService,
        audit_svc: AuditService,
    ) -> None:
        self._account_repo = account_repo
        self._password_svc = password_svc
        self._session_svc = session_svc
        self._audit_svc = audit_svc

    def login(
        self,
        email: str,
        password: str,
        ip: str | None,
        response: Response,
        lockout_svc: object | None = None,
    ) -> LoginResult:
        """Authenticate a user and return a session on success.

        Anti-enumeration: always calls verify(), never short-circuits early.
        Never logs password or which specific field failed.
        """
        normalised_email = email.strip().lower()

        account: Account | None = self._account_repo.get_by_email(normalised_email)

        # Always verify to keep timing consistent (anti-enumeration)
        if account is None:
            self._password_svc.verify(get_dummy_hash(), password)  # result discarded
            self._audit_svc.record(
                actor=None,
                action=AuditAction.LOGIN_FAILURE,
                target_type="account",
                target_id=None,
                outcome=AuditOutcome.FAILURE,
                ip=ip,
            )
            if lockout_svc is not None:
                if not lockout_svc.is_email_locked(normalised_email):  # type: ignore[attr-defined]
                    lockout_svc.record_failure(None, normalised_email, ip)  # type: ignore[attr-defined]
            return LoginFailure()

        pw_hash = account.password_hash or get_dummy_hash()
        password_ok = self._password_svc.verify(pw_hash, password)

        # Check lockout (after verify to preserve timing)
        if lockout_svc is not None and lockout_svc.is_locked(account.id):  # type: ignore[attr-defined]
            self._audit_svc.record(
                actor=account.id,
                action=AuditAction.LOGIN_FAILURE,
                target_type="account",
                target_id=str(account.id),
                outcome=AuditOutcome.FAILURE,
                ip=ip,
            )
            return LoginFailure()

        # Generic failure for any non-ACTIVE state or wrong password
        if not password_ok or account.status != AccountStatus.ACTIVE:
            self._audit_svc.record(
                actor=account.id,
                action=AuditAction.LOGIN_FAILURE,
                target_type="account",
                target_id=str(account.id),
                outcome=AuditOutcome.FAILURE,
                ip=ip,
            )
            if lockout_svc is not None:
                lockout_svc.record_failure(account.id, normalised_email, ip)  # type: ignore[attr-defined]
            return LoginFailure()

        # Success path
        if lockout_svc is not None:
            lockout_svc.reset(account.id)  # type: ignore[attr-defined]

        result = self._session_svc.create_session(account, ip=ip)
        set_session_cookie(response, result.session.session_id)
        csrf_token = issue_csrf_token(response)

        self._audit_svc.record(
            actor=account.id,
            action=AuditAction.LOGIN_SUCCESS,
            target_type="account",
            target_id=str(account.id),
            outcome=AuditOutcome.SUCCESS,
            ip=ip,
        )

        return LoginSuccess(session=result.session, csrf_token=csrf_token)
