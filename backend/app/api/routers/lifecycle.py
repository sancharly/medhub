"""Lifecycle (deactivate/reactivate/delete) endpoints (TASK-062)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_session_service
from app.api.errors import NotFoundError, ValidationProblem
from app.api.schemas.lifecycle import DeleteConfirmationRequest, DeletionResponse
from app.audit.service import AuditService
from app.auth.csrf import require_csrf
from app.auth.password import PasswordService
from app.auth.session import SessionService
from app.db.models.account import Account
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.anonymized_dataset_repo import AnonymizedDatasetRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.password_history_repo import PasswordHistoryRepository
from app.db.repositories.session import get_db
from app.identity.erasure import ErasureService
from app.identity.lifecycle import LifecycleService

router = APIRouter(prefix="/accounts", tags=["lifecycle"])


def _get_lifecycle_service(
    db: Session = Depends(get_db),
    session_svc: SessionService = Depends(get_session_service),
) -> LifecycleService:
    audit_svc = AuditService(AuditRepository(db))
    return LifecycleService(AccountRepository(db), session_svc, audit_svc)


def _get_erasure_service(
    db: Session = Depends(get_db),
    session_svc: SessionService = Depends(get_session_service),
) -> ErasureService:
    audit_svc = AuditService(AuditRepository(db))
    password_svc = PasswordService(PasswordHistoryRepository(db))
    return ErasureService(
        AccountRepository(db),
        AnonymizedDatasetRepository(db),
        session_svc,
        password_svc,
        audit_svc,
    )


@router.post("/{account_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_account(
    account_id: uuid.UUID,
    actor: Account = Depends(get_current_user),
    svc: LifecycleService = Depends(_get_lifecycle_service),
    _csrf: None = Depends(require_csrf),
) -> None:
    svc.deactivate(actor, account_id)


@router.post("/{account_id}/reactivate", status_code=status.HTTP_204_NO_CONTENT)
def reactivate_account(
    account_id: uuid.UUID,
    actor: Account = Depends(get_current_user),
    svc: LifecycleService = Depends(_get_lifecycle_service),
    _csrf: None = Depends(require_csrf),
) -> None:
    svc.reactivate(actor, account_id)


@router.delete("/{account_id}", response_model=DeletionResponse)
def delete_account(
    account_id: uuid.UUID,
    body: DeleteConfirmationRequest,
    actor: Account = Depends(get_current_user),
    db: Session = Depends(get_db),
    svc: ErasureService = Depends(_get_erasure_service),
    _csrf: None = Depends(require_csrf),
) -> DeletionResponse:
    # SR-034.6: verify explicit email+type confirmation against the target account
    target = AccountRepository(db).get_by_id(account_id)
    if target is None:
        raise NotFoundError("Account not found.")
    if target.email != body.confirm_email or target.user_type != body.confirm_account_type:
        raise ValidationProblem(
            "Confirmation email or account type does not match the target account."
        )
    result = svc.delete(actor, account_id)
    return DeletionResponse(
        dataset_id=result.dataset_id,
        message="Account erased. Retrieval code will be emailed.",
    )
