"""Modules admin API router (TASK-070) — sysadmin only."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.errors import AuthorizationError
from app.audit.service import AuditService
from app.authz.consent import ConsentService
from app.authz.service import AuthorizationService, Resource
from app.db.models.account import Account
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.consent_repo import ConsentRepository
from app.db.repositories.module_repo import ModuleRepository
from app.db.repositories.session import get_db

router = APIRouter(prefix="/modules", tags=["modules"])


class ModuleResponse(BaseModel):
    module_key: str
    name: str
    version: str
    required_permissions: list[str]

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class ModuleListResponse(BaseModel):
    items: list[ModuleResponse]
    total: int


@router.get("", response_model=ModuleListResponse)
def list_modules(
    actor: Account = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ModuleListResponse:
    audit_svc = AuditService(AuditRepository(db))
    authz_svc = AuthorizationService(ConsentService(ConsentRepository(db), audit_svc), audit_svc)
    decision = authz_svc.decide(
        actor, "module:list", Resource(resource_type="module", owner_id=None, patient_id=None)
    )
    if not decision.allow:
        raise AuthorizationError("Only sysadmins may list installed modules.")

    repo = ModuleRepository(db)
    records = repo.list_installed()
    items = [ModuleResponse.model_validate(r) for r in records]
    return ModuleListResponse(items=items, total=len(items))
