"""Accounts API router (TASK-061)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas.account import (
    AccountCreateRequest,
    AccountListResponse,
    AccountResponse,
)
from app.audit.service import AuditService
from app.auth.password import PasswordService  # noqa: F401 (used in resend_activation)
from app.authz.consent import ConsentService
from app.authz.service import AuthorizationService, Resource
from app.db.models.account import Account
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.session import get_db
from app.identity.account_service import AccountCreate, AccountService
from app.identity.activation import ActivationService

router = APIRouter(prefix="/accounts", tags=["accounts"])


def _get_account_service(db: Session = Depends(get_db)) -> AccountService:
    audit_svc = AuditService(AuditRepository(db))
    consent_svc = ConsentService(ConsentRepository(db), audit_svc)
    authz_svc = AuthorizationService(consent_svc, audit_svc)
    return AccountService(AccountRepository(db), audit_svc, authz_svc)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AccountResponse)
def create_account(
    body: AccountCreateRequest,
    actor: Account = Depends(get_current_user),
    svc: AccountService = Depends(_get_account_service),
) -> AccountResponse:
    data = AccountCreate(
        email=body.email,
        user_type=body.user_type,
        first_name=body.first_name,
        surname=body.surname,
        date_of_birth=body.date_of_birth,
    )
    account = svc.create(actor, data)
    return AccountResponse.model_validate(account)


@router.get("", response_model=AccountListResponse)
def list_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor: Account = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountListResponse:
    audit_svc = AuditService(AuditRepository(db))
    consent_svc = ConsentService(ConsentRepository(db), audit_svc)
    authz_svc = AuthorizationService(consent_svc, audit_svc)
    authz_svc.authorize(
        actor,
        "account:list",
        Resource(resource_type="account", owner_id=None, patient_id=None),
    )

    repo = AccountRepository(db)
    all_accounts = repo.list()
    total = len(all_accounts)
    start = (page - 1) * page_size
    items = all_accounts[start : start + page_size]
    return AccountListResponse(
        items=[AccountResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: uuid.UUID,
    actor: Account = Depends(get_current_user),
    svc: AccountService = Depends(_get_account_service),
) -> AccountResponse:
    account = svc.get_profile(actor, account_id)
    return AccountResponse.model_validate(account)


@router.post("/{account_id}/resend-activation", status_code=status.HTTP_202_ACCEPTED)
def resend_activation(
    account_id: uuid.UUID,
    actor: Account = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    audit_svc = AuditService(AuditRepository(db))
    password_svc = PasswordService()
    svc = ActivationService(AccountRepository(db), password_svc, audit_svc)
    svc.resend_activation(actor, account_id)
    return {"detail": "Activation email queued."}
