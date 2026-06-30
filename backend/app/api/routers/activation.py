"""Activation API router (TASK-061)."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.errors import ValidationProblem
from app.api.schemas.account import ActivationRequest, ActivationTokenStatus
from app.audit.service import AuditService
from app.auth.password import PasswordService
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.group_repo import GroupRepository
from app.db.repositories.session import get_db
from app.identity.activation import ActivationService

router = APIRouter(prefix="/activation", tags=["activation"])


def _get_activation_service(db: Session = Depends(get_db)) -> ActivationService:
    audit_svc = AuditService(AuditRepository(db))
    password_svc = PasswordService()
    group_repo = GroupRepository(db)
    return ActivationService(AccountRepository(db), password_svc, audit_svc, group_repo)


@router.get("/{token}", response_model=ActivationTokenStatus)
def validate_token(
    token: str,
    db: Session = Depends(get_db),
) -> ActivationTokenStatus:
    """Validate an activation token without consuming it."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    repo = AccountRepository(db)
    # Find account by token hash
    for account in repo.list():
        if account.activation_token_hash == token_hash:
            if (
                account.activation_token_expires_at is not None
                and datetime.now(UTC) <= account.activation_token_expires_at
            ):
                return ActivationTokenStatus(valid=True, account_id=account.id)
            return ActivationTokenStatus(valid=False)
    return ActivationTokenStatus(valid=False)


@router.post("/{token}", status_code=status.HTTP_204_NO_CONTENT)
def activate_account(
    token: str,
    body: ActivationRequest,
    svc: ActivationService = Depends(_get_activation_service),
) -> None:
    """Activate an account with the provided token and password."""
    if body.password != body.confirm_password:
        raise ValidationProblem("Password and confirm password do not match.")
    svc.activate(body.account_id, token, body.password)
