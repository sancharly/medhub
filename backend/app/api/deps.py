"""FastAPI auth/session/authorization dependencies (TASK-025).

Deny-by-default: only health and openapi endpoints are unauthenticated.
"""

from __future__ import annotations

import functools
from collections.abc import Callable

import redis as redis_lib
from fastapi import Depends, Request

from app.api.errors import UnauthenticatedError
from app.auth.session import Session as UserSession
from app.auth.session import SessionService
from app.core.config import get_settings
from app.db.models.account import Account
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.session import DbSession

# ---------------------------------------------------------------------------
# Redis client dependency
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def _redis_client() -> redis_lib.Redis:
    """One client, one bounded connection pool for the process (ADR-0022).

    A client per request opened a pool per request. The pool holds at most as many connections as
    the API has threads, so a request never finds the pool empty.
    """
    settings = get_settings()
    return redis_lib.Redis.from_url(
        settings.redis_url, decode_responses=False, max_connections=settings.api_threadpool_size
    )


def get_redis() -> redis_lib.Redis:
    """Return the process-wide Redis client."""
    return _redis_client()


def get_session_service(r: redis_lib.Redis = Depends(get_redis)) -> SessionService:
    return SessionService(r)


# ---------------------------------------------------------------------------
# Session dependency
# ---------------------------------------------------------------------------

_SESSION_COOKIE = "medhub_session"


def get_session(
    request: Request,
    svc: SessionService = Depends(get_session_service),
) -> UserSession:
    """Extract and validate the session cookie.

    Raises UnauthenticatedError (401) if the session is absent or expired.
    CSRF is not checked here. ``CsrfEnforcementMiddleware`` enforces it for every
    state-changing request outside the reviewed exempt paths (SR-031); ``require_csrf``
    on the routes is a second check of the same token, not the control.
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


def get_current_user(
    db: DbSession,
    session: UserSession = Depends(get_session),
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
# Module access guard dependency factory (TASK-043)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# PlatformServices dependency (TASK-071)
# ---------------------------------------------------------------------------


def get_platform_services(
    db: DbSession,
) -> object:
    """Yield a request-scoped PlatformServices wired from FastAPI DI."""
    from app.attachments.service import AttachmentService  # noqa: PLC0415
    from app.audit.service import AuditService  # noqa: PLC0415
    from app.authz.consent import ConsentService  # noqa: PLC0415
    from app.authz.service import AuthorizationService  # noqa: PLC0415
    from app.clinical.service import ClinicalDataService  # noqa: PLC0415
    from app.core.object_storage import ObjectStorageClient  # noqa: PLC0415
    from app.db.repositories.account_repo import AccountRepository  # noqa: PLC0415
    from app.db.repositories.attachment_repo import AttachmentRepository  # noqa: PLC0415
    from app.db.repositories.audit_repo import AuditRepository  # noqa: PLC0415
    from app.db.repositories.clinical_repo import ClinicalRepository  # noqa: PLC0415
    from app.db.repositories.consent_repo import ConsentRepository  # noqa: PLC0415
    from app.modules.platform_services import PlatformServices  # noqa: PLC0415

    audit_svc = AuditService(AuditRepository(db))
    consent_svc = ConsentService(ConsentRepository(db), audit_svc)
    authz_svc = AuthorizationService(consent_svc, audit_svc)
    clinical_svc = ClinicalDataService(
        ClinicalRepository(db), AccountRepository(db), audit_svc, authz_svc
    )
    attachment_svc = AttachmentService(
        AttachmentRepository(db),
        ClinicalRepository(db),
        audit_svc,
        authz_svc,
        ObjectStorageClient(),
    )
    return PlatformServices(
        authorization=authz_svc,
        clinical=clinical_svc,
        attachments=attachment_svc,
        audit=audit_svc,
    )


def require_module_enabled(module_key: str) -> Callable[..., object]:
    """Return a FastAPI dependency that raises AuthorizationError if module not enabled."""

    def _dependency(
        db: DbSession,
        actor: Account = Depends(get_current_user),
    ) -> None:
        from app.api.errors import AuthorizationError  # noqa: PLC0415
        from app.audit.service import AuditService  # noqa: PLC0415
        from app.authz.consent import ConsentService  # noqa: PLC0415
        from app.authz.module_guard import ModuleAccessGuard  # noqa: PLC0415
        from app.authz.service import AuthorizationService, Resource  # noqa: PLC0415
        from app.db.repositories.audit_repo import AuditRepository  # noqa: PLC0415
        from app.db.repositories.consent_repo import ConsentRepository  # noqa: PLC0415
        from app.db.repositories.group_repo import GroupRepository  # noqa: PLC0415
        from app.db.repositories.module_repo import ModuleRepository  # noqa: PLC0415

        guard = ModuleAccessGuard(GroupRepository(db), ModuleRepository(db))
        audit_svc = AuditService(AuditRepository(db))
        authz_svc = AuthorizationService(
            ConsentService(ConsentRepository(db), audit_svc), audit_svc
        )
        try:
            authz_svc.authorize(
                actor,
                "module:access",
                Resource(
                    resource_type="module",
                    owner_id=None,
                    patient_id=None,
                    resource_id=module_key,
                    module_enabled=guard.is_module_enabled(actor.id, module_key),
                ),
            )
        except AuthorizationError:
            # The AUTHZ_DENIED row is already written.
            raise AuthorizationError(
                f"Module '{module_key}' is not enabled for your account."
            ) from None

    return _dependency
