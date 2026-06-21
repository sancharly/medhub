"""FastAPI auth/session/authorization dependencies (TASK-025).

Deny-by-default: only health and openapi endpoints are unauthenticated.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

import redis as redis_lib
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.api.errors import UnauthenticatedError
from app.auth.session import Session as UserSession
from app.auth.session import SessionService
from app.core.config import get_settings
from app.db.models.account import Account
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.session import get_db

# ---------------------------------------------------------------------------
# Redis client dependency
# ---------------------------------------------------------------------------


def get_redis() -> redis_lib.Redis:
    """Return a Redis client from the configured URL."""
    return redis_lib.Redis.from_url(get_settings().redis_url, decode_responses=False)


def get_session_service(r: redis_lib.Redis = Depends(get_redis)) -> SessionService:
    return SessionService(r)


# ---------------------------------------------------------------------------
# Session dependency
# ---------------------------------------------------------------------------

_SESSION_COOKIE = "medhub_session"


async def get_session(
    request: Request,
    svc: SessionService = Depends(get_session_service),
) -> UserSession:
    """Extract and validate the session cookie.

    Raises UnauthenticatedError (401) if the session is absent or expired.
    CSRF is enforced inside require_csrf for state-changing methods — that
    dependency is wired at router level, not here, so it can be overridden
    in tests without duplicating the session lookup.
    """
    session_id = request.cookies.get(_SESSION_COOKIE)
    if not session_id:
        raise UnauthenticatedError("No session cookie present.")

    session = svc.resolve(session_id)
    if session is None:
        raise UnauthenticatedError("Session expired or invalid.")

    return session


# ---------------------------------------------------------------------------
# Current-user dependency
# ---------------------------------------------------------------------------


async def get_current_user(
    session: UserSession = Depends(get_session),
    db: Session = Depends(get_db),
) -> Account:
    """Load the Account for the current session.

    Defense-in-depth: re-checks that the account is still active.
    """
    from app.db.models.account import AccountStatus  # noqa: PLC0415

    repo = AccountRepository(db)
    account = repo.get_by_id(session.account_id)
    if account is None or account.status != AccountStatus.ACTIVE:
        raise UnauthenticatedError("Account is not active.")
    return account


# ---------------------------------------------------------------------------
# Authorization protocol
# ---------------------------------------------------------------------------


class AuthorizationServiceProtocol(Protocol):
    def authorize(
        self,
        actor: Account,
        action: str,
        resource: object,
    ) -> object: ...


# ---------------------------------------------------------------------------
# require() factory
# ---------------------------------------------------------------------------


def require(
    action: str,
    resource_loader: Callable[..., object],
) -> Callable[..., object]:
    """Return a FastAPI dependency that authorises and returns the loaded resource.

    Usage::

        @router.get("/patients/{patient_id}/notes")
        def list_notes(
            resource=Depends(require("clinical:read", load_patient)),
            actor: Account = Depends(get_current_user),
        ):
            ...

    The resource_loader is called as a dependency and must return the resource.
    AuthorizationService.authorize() is called; raises 403 on deny.
    """

    async def _dependency(
        actor: Account = Depends(get_current_user),
        resource: object = Depends(resource_loader),
        authz: object = Depends(_get_authz_service),
    ) -> object:
        authz.authorize(actor, action, resource)  # type: ignore[attr-defined]
        return resource

    return _dependency


def _get_authz_service() -> object:
    """Placeholder — TASK-027 will provide the real implementation.

    Imported lazily so TASK-025 can land before TASK-027.
    """
    from app.authz.service import get_authorization_service  # noqa: PLC0415

    return get_authorization_service()
