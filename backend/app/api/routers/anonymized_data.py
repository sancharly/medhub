"""Anonymized data retrieval endpoint (TASK-062)."""

from __future__ import annotations

import redis as redis_lib
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_redis
from app.api.errors import RateLimitedError
from app.api.schemas.lifecycle import AnonymizedRetrieveRequest, AnonymizedRetrieveResponse
from app.audit.service import AuditService
from app.auth.password import PasswordService
from app.auth.session import SessionService
from app.core.client_address import client_address
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.anonymized_dataset_repo import AnonymizedDatasetRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.password_history_repo import PasswordHistoryRepository
from app.db.repositories.session import get_db
from app.identity.erasure import ErasureService

router = APIRouter(prefix="/anonymized-data", tags=["anonymized-data"])

# Rate limit: 5 attempts per originating client address in a fixed 3600-second window that starts
# at the address's first counted attempt (SR-042 AC 4, AC 5; ADR-0013 limit, ADR-0019 address).
_RATE_LIMIT_WINDOW_SECONDS = 3600
_RATE_LIMIT_MAX_ATTEMPTS = 5


def _check_rate_limit(address: str | None, r: redis_lib.Redis) -> None:
    """Count one attempt for ``address``; refuse the sixth within the window (SR-042 AC 4)."""
    if address is None:  # no peer at all: refuse rather than share a bucket
        raise RateLimitedError("Too many retrieval attempts. Try again later.")
    key = f"rate:anonymized_retrieve:{address}"
    # One MULTI/EXEC: the increment is atomic, and NX starts the window only when the key has no
    # expiry yet, so later attempts never extend it.
    pipe = r.pipeline(transaction=True)
    pipe.incr(key)
    pipe.expire(key, _RATE_LIMIT_WINDOW_SECONDS, nx=True)
    count = int(pipe.execute()[0])
    if count > _RATE_LIMIT_MAX_ATTEMPTS:
        raise RateLimitedError("Too many retrieval attempts. Try again later.")


def _get_erasure_service(
    db: Session = Depends(get_db),
    r: redis_lib.Redis = Depends(get_redis),
) -> ErasureService:
    audit_svc = AuditService(AuditRepository(db))
    password_svc = PasswordService(PasswordHistoryRepository(db))
    session_svc = SessionService(r)
    return ErasureService(
        AccountRepository(db),
        AnonymizedDatasetRepository(db),
        session_svc,
        password_svc,
        audit_svc,
    )


@router.post("/retrieve", response_model=AnonymizedRetrieveResponse)
def retrieve_anonymized_data(
    body: AnonymizedRetrieveRequest,
    request: Request,
    svc: ErasureService = Depends(_get_erasure_service),
    r: redis_lib.Redis = Depends(get_redis),
) -> AnonymizedRetrieveResponse:
    """Retrieve anonymized dataset by retrieval code. No session required (ADR-0013)."""
    _check_rate_limit(client_address(request), r)
    dataset = svc.retrieve_anonymized(body.retrieval_code)
    return AnonymizedRetrieveResponse(
        dataset_id=dataset.id,
        payload=dataset.payload or {},
    )
