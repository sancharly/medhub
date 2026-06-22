"""Groups API router (TASK-040/041/042)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas.groups import (
    AddMemberRequest,
    GroupCreate,
    GroupResponse,
    SetModuleEnabledRequest,
)
from app.audit.service import AuditService
from app.authz.service import AuthorizationService
from app.db.models.account import Account
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.group_repo import GroupRepository
from app.db.repositories.module_repo import ModuleRepository
from app.db.repositories.session import get_db
from app.groups.service import GroupService

router = APIRouter(prefix="/groups", tags=["groups"])


def _get_group_service(db: Session = Depends(get_db)) -> GroupService:
    from app.authz.consent import ConsentService  # noqa: PLC0415
    from app.db.repositories.consent_repo import ConsentRepository  # noqa: PLC0415

    audit_svc = AuditService(AuditRepository(db))
    consent_svc = ConsentService(ConsentRepository(db), audit_svc)
    authz_svc = AuthorizationService(consent_svc, audit_svc)
    return GroupService(
        GroupRepository(db),
        AccountRepository(db),
        ModuleRepository(db),
        audit_svc,
        authz_svc,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=GroupResponse)
def create_group(
    body: GroupCreate,
    actor: Account = Depends(get_current_user),
    svc: GroupService = Depends(_get_group_service),
) -> GroupResponse:
    group = svc.create_group(actor, body.name)
    return GroupResponse.model_validate(group)


@router.get("", response_model=list[GroupResponse])
def list_groups(
    actor: Account = Depends(get_current_user),
    svc: GroupService = Depends(_get_group_service),
) -> list[GroupResponse]:
    groups = svc.list_groups(actor)
    return [GroupResponse.model_validate(g) for g in groups]


@router.post("/{group_id}/members", status_code=status.HTTP_204_NO_CONTENT)
def add_member(
    group_id: uuid.UUID,
    body: AddMemberRequest,
    actor: Account = Depends(get_current_user),
    svc: GroupService = Depends(_get_group_service),
) -> None:
    svc.add_member(actor, group_id, body.account_id)


@router.delete("/{group_id}/members/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    group_id: uuid.UUID,
    account_id: uuid.UUID,
    actor: Account = Depends(get_current_user),
    svc: GroupService = Depends(_get_group_service),
) -> None:
    svc.remove_member(actor, group_id, account_id)


@router.put("/{group_id}/modules/{module_key}", status_code=status.HTTP_204_NO_CONTENT)
def set_module_enabled(
    group_id: uuid.UUID,
    module_key: str,
    body: SetModuleEnabledRequest,
    actor: Account = Depends(get_current_user),
    svc: GroupService = Depends(_get_group_service),
) -> None:
    svc.set_module_enabled(actor, group_id, module_key, body.enabled)
