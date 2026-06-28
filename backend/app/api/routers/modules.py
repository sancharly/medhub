"""Modules admin API router (TASK-070) — sysadmin only."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.errors import AuthorizationError
from app.db.models.account import Account, UserType
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
    if actor.user_type != UserType.SYSADMIN:
        raise AuthorizationError("Only sysadmins may list installed modules.")

    repo = ModuleRepository(db)
    records = repo.list_installed()
    items = [ModuleResponse.model_validate(r) for r in records]
    return ModuleListResponse(items=items, total=len(items))
