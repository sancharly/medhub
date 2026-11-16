"""Me API router (TASK-067)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import (
    get_current_user,
    get_current_user_no_slide,
    get_session,
    get_session_service,
)
from app.api.schemas.me import MeModulesResponse, MeResponse
from app.auth.password import PasswordService
from app.auth.session import Session as UserSession
from app.auth.session import SessionService
from app.db.models.account import Account
from app.db.repositories.group_repo import GroupRepository
from app.db.repositories.module_repo import ModuleRepository
from app.db.repositories.session import DbSession

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeResponse)
def get_me(
    actor: Account = Depends(get_current_user),
    session: UserSession = Depends(get_session),
    svc: SessionService = Depends(get_session_service),
) -> MeResponse:
    return MeResponse(
        id=actor.id,
        email=actor.email,
        user_type=actor.user_type,
        state=actor.status,
        first_name=actor.first_name,
        surname=actor.surname,
        date_of_birth=actor.date_of_birth,
        created_at=actor.created_at,
        must_change_password=PasswordService().is_expired(actor),
        session_expires_in_seconds=svc.remaining_seconds(session),
    )


@router.get("/modules", response_model=MeModulesResponse)
def get_my_modules(
    db: DbSession,
    # The client polls this route on a timer (SR-015 AC 5). The session is validated but not
    # extended, so polling cannot keep an idle session alive (SR-030 AC 1, AC 2; RISK-005).
    actor: Account = Depends(get_current_user_no_slide),
) -> MeModulesResponse:
    group_repo = GroupRepository(db)
    module_repo = ModuleRepository(db)
    memberships = group_repo.memberships_for_account(actor.id)
    group_ids = [m.group_id for m in memberships]
    enabled_keys = module_repo.enabled_module_keys_for_groups(group_ids)
    return MeModulesResponse(modules=enabled_keys)
