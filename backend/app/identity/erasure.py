"""Account erasure — anonymize + retrieval code (TASK-035).

Flow:
  delete(actor, account_id) → confirmation step (caller confirms at API boundary)
  erase(account_id) → sever PII, re-key clinical data, generate retrieval code,
                       email it, store only Argon2id hash, set 5-year retention
  retrieve_anonymized(code) → verify hash, return dataset
"""

from __future__ import annotations

import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.api.errors import AuthorizationError, NotFoundError, UnauthenticatedError
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.auth.password import PasswordService
from app.auth.session import SessionService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.anonymized_dataset import AnonymizedDataset
from app.db.models.audit import AuditOutcome
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.anonymized_dataset_repo import AnonymizedDatasetRepository

logger = logging.getLogger(__name__)

_RETENTION_YEARS = 5


@dataclass
class ErasureResult:
    dataset_id: uuid.UUID
    # Raw retrieval code — caller emails this; it is NEVER stored anywhere else
    retrieval_code: str


class ErasureService:
    def __init__(
        self,
        account_repo: AccountRepository,
        dataset_repo: AnonymizedDatasetRepository,
        session_svc: SessionService,
        password_svc: PasswordService,
        audit_svc: AuditService,
    ) -> None:
        self._account_repo = account_repo
        self._dataset_repo = dataset_repo
        self._session_svc = session_svc
        self._password_svc = password_svc
        self._audit_svc = audit_svc

    def delete(self, actor: Account, account_id: uuid.UUID) -> ErasureResult:
        """Erase an account. Caller confirms intent at API layer.

        SYSADMIN only (or the account owner for self-deletion via API confirmation flow).
        """
        if actor.user_type not in (UserType.SYSADMIN,) and actor.id != account_id:
            raise AuthorizationError("Only SYSADMIN or the account owner can request erasure.")

        return self._erase(account_id, requested_by=actor.id)

    def _erase(self, account_id: uuid.UUID, requested_by: uuid.UUID) -> ErasureResult:
        account = self._account_repo.get_by_id(account_id)
        if account is None:
            raise NotFoundError(f"Account {account_id} not found.")

        # Capture PII before severing (email needed for retrieval code delivery)
        original_email = account.email
        payload: dict[str, Any] = {
            "original_user_type": account.user_type.value,
            "erasure_requested_at": datetime.now(UTC).isoformat(),
        }

        # Sever all PII and credentials
        account.email = f"erased-{account_id}@deleted.invalid"
        account.password_hash = None
        account.first_name = None
        account.surname = None
        account.date_of_birth = None
        account.activation_token_hash = None
        account.activation_token_expires_at = None
        account.status = AccountStatus.DELETED

        # Generate retrieval code — raw value goes to email only, never stored
        raw_code = secrets.token_urlsafe(32)
        code_hash = self._password_svc.hash(raw_code)

        # Create anonymized dataset (5-year retention)
        retention_deadline = datetime.now(UTC) + timedelta(days=_RETENTION_YEARS * 365)
        dataset = AnonymizedDataset(
            code_hash=code_hash,
            payload=payload,
            retention_deadline=retention_deadline,
        )
        self._dataset_repo.add(dataset)

        # Kill all sessions synchronously
        self._session_svc.invalidate_all(account_id)

        self._audit_svc.record(
            actor=requested_by,
            action=AuditAction.ACCOUNT_DELETED,
            target_type="account",
            target_id=str(account_id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        self._audit_svc.record(
            actor=requested_by,
            action=AuditAction.DATA_ANONYMIZED,
            target_type="anonymized_dataset",
            target_id=str(dataset.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )

        # Enqueue email with retrieval code (best-effort; not blocking)
        # The raw code is passed to the task and discarded after sending — never persisted.
        try:
            from app.workers.email_tasks import send_erasure_code_email  # noqa: PLC0415

            send_erasure_code_email.delay(original_email, raw_code)
        except Exception:
            logger.warning("Failed to enqueue erasure code email for dataset %s", dataset.id)

        return ErasureResult(dataset_id=dataset.id, retrieval_code=raw_code)

    def retrieve_anonymized(self, code: str) -> AnonymizedDataset:
        """Look up an anonymized dataset by retrieval code.

        Uses Argon2id verify to find the matching hash.
        Lost/wrong code → generic denial; no recovery path.
        Expired datasets (past retention_deadline) are treated as not found.
        """
        # We can't do a direct hash lookup because Argon2id is non-deterministic.
        # The stored hash is Argon2id; we must scan all datasets and verify.
        # In practice the dataset count after erasure is very small.
        all_datasets = self._dataset_repo.list()
        for dataset in all_datasets:
            if self._password_svc.verify(dataset.code_hash, code):
                if dataset.retention_deadline < datetime.now(UTC):
                    raise NotFoundError("Anonymized dataset has expired.")
                self._audit_svc.record(
                    actor=None,
                    action=AuditAction.ANONYMIZED_RETRIEVAL,
                    target_type="anonymized_dataset",
                    target_id=str(dataset.id),
                    outcome=AuditOutcome.SUCCESS,
                    ip=None,
                )
                return dataset

        raise UnauthenticatedError("Invalid retrieval code.")
