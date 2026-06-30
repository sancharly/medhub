"""Me API router (TASK-067)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas.me import MeModulesResponse, MeResponse
from app.auth.password import PasswordService
from app.db.models.account import Account
from app.db.repositories.group_repo import GroupRepository
from app.db.repositories.module_repo import ModuleRepository
from app.db.repositories.session import get_db

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeResponse)
def get_me(actor: Account = Depends(get_current_user)) -> MeResponse:
    must_change = PasswordService().is_expired(actor)
    data = MeResponse.model_validate(actor)
    data.must_change_password = must_change
    return data


@router.get("/modules", response_model=MeModulesResponse)
def get_my_modules(
    actor: Account = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeModulesResponse:
    group_repo = GroupRepository(db)
    module_repo = ModuleRepository(db)
    memberships = group_repo.memberships_for_account(actor.id)
    group_ids = [m.group_id for m in memberships]
    enabled_keys = module_repo.enabled_module_keys_for_groups(group_ids)
    return MeModulesResponse(modules=enabled_keys)
