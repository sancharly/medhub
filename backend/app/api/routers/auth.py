"""Auth/session API router (TASK-060)."""

from __future__ import annotations

from datetime import UTC, datetime

import redis as redis_lib
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_redis, get_session, get_session_service
from app.api.errors import UnauthenticatedError, ValidationProblem
from app.api.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MeSummary,
    PasswordChangeRequest,
    SessionExtendResponse,
)
from app.audit.service import AuditService
from app.auth.cookies import clear_session_cookie
from app.auth.csrf import require_csrf
from app.auth.lockout import LockoutService
from app.auth.login import LoginFailure, LoginService
from app.auth.password import PasswordPolicyError, PasswordService
from app.auth.session import Session as UserSession
from app.auth.session import SessionService
from app.db.models.account import Account
from app.db.models.audit import AuditOutcome
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.password_history_repo import PasswordHistoryRepository
from app.db.repositories.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_login_service(
    db: Session = Depends(get_db),
    r: redis_lib.Redis = Depends(get_redis),
) -> LoginService:
    audit_svc = AuditService(AuditRepository(db))
    password_svc = PasswordService()
    session_svc = SessionService(r)
    return LoginService(AccountRepository(db), password_svc, session_svc, audit_svc)


@router.post("/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    svc: LoginService = Depends(_get_login_service),
    db: Session = Depends(get_db),
    r: redis_lib.Redis = Depends(get_redis),
) -> LoginResponse:
    """Authenticate; set session+CSRF cookies; return user summary."""
    ip = request.client.host if request.client else None
    audit_svc = AuditService(AuditRepository(db))
    lockout_svc = LockoutService(r, audit_svc)
    result = svc.login(body.email, body.password, ip, response, lockout_svc=lockout_svc)

    if isinstance(result, LoginFailure):
        raise UnauthenticatedError("Invalid credentials.")

    # result is LoginSuccess
    session = result.session
    if session is None:
        raise UnauthenticatedError("Session creation failed.")
    account = AccountRepository(db).get_by_id(session.account_id)
    if account is None:
        raise UnauthenticatedError("Account not found.")

    must_change = PasswordService().is_expired(account)

    return LoginResponse(
        user=MeSummary(
            id=account.id,
            first_name=account.first_name,
            surname=account.surname,
            user_type=account.user_type,
        ),
        must_change_password=must_change,
        evicted_session=False,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    request: Request,
    session: UserSession = Depends(get_session),
    svc: SessionService = Depends(get_session_service),
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> None:
    """Invalidate session, clear cookie, audit LOGOUT."""
    svc.invalidate(session.session_id)
    clear_session_cookie(response)
    audit_svc = AuditService(AuditRepository(db))
    audit_svc.record(
        actor=session.account_id,
        action="LOGOUT",
        target_type="session",
        target_id=session.session_id,
        outcome=AuditOutcome.SUCCESS,
        ip=request.client.host if request.client else None,
    )


@router.post("/session/extend", response_model=SessionExtendResponse)
async def extend_session(
    session: UserSession = Depends(get_session),
    svc: SessionService = Depends(get_session_service),
    _csrf: None = Depends(require_csrf),
) -> SessionExtendResponse:
    """TTL was already slid by resolve() in get_session; return the new inactivity deadline."""
    new_expiry = svc.get_inactivity_expiry(session)
    return SessionExtendResponse(expires_at=new_expiry)


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: PasswordChangeRequest,
    request: Request,
    actor: Account = Depends(get_current_user),
    session: UserSession = Depends(get_session),
    svc: SessionService = Depends(get_session_service),
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> None:
    """Verify current password, validate new, hash+persist, invalidate other sessions."""
    if body.new_password != body.confirm_new_password:
        raise ValidationProblem("New password and confirmation do not match.")

    history_repo = PasswordHistoryRepository(db)
    password_svc = PasswordService(history_repo)

    current_hash = actor.password_hash or ""
    if not password_svc.verify(current_hash, body.current_password):
        raise UnauthenticatedError("Current password is incorrect.")

    try:
        password_svc.validate_policy(actor, body.new_password)
    except PasswordPolicyError as exc:
        raise ValidationProblem(
            f"Password policy violated: {[v.value for v in exc.violations]}"
        ) from exc

    new_hash = password_svc.hash(body.new_password)
    actor.password_hash = new_hash
    actor.password_changed_at = datetime.now(UTC)
    password_svc.record_history(actor.id, new_hash)
    db.add(actor)
    db.commit()

    # Invalidate all other sessions via the public service method
    for sid in svc.list_account_session_ids(actor.id):
        if sid != session.session_id:
            svc.invalidate(sid)

    audit_svc = AuditService(AuditRepository(db))
    audit_svc.record(
        actor=actor.id,
        action="PASSWORD_CHANGED",
        target_type="account",
        target_id=str(actor.id),
        outcome=AuditOutcome.SUCCESS,
        ip=request.client.host if request.client else None,
    )
