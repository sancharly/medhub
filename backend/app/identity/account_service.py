"""AccountService — create and profile (TASK-030).

Authorization rules:
  - create: ADMIN can create DOCTOR/PATIENT/ADMIN; SYSADMIN can create all four
  - ADMIN cannot create SYSADMIN
  - profile read: scoped by AuthorizationService + admin projection for ADMIN role
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy.exc import IntegrityError

from app.api.errors import AuthorizationError, ConflictError, NotFoundError
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.authz.service import AuthorizationService, Resource
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.audit import AuditOutcome
from app.db.repositories.account_repo import AccountRepository

logger = logging.getLogger(__name__)


@dataclass
class AccountCreate:
    email: str
    user_type: UserType
    first_name: str | None = None
    family_name: str | None = None
    date_of_birth: date | None = None


class AccountService:
    def __init__(
        self,
        account_repo: AccountRepository,
        audit_svc: AuditService,
        authz_svc: AuthorizationService,
    ) -> None:
        self._repo = account_repo
        self._audit_svc = audit_svc
        self._authz_svc = authz_svc

    def create(self, creator: Account, data: AccountCreate) -> Account:
        """Create a new account.

        Authorisation:
          ADMIN  can create DOCTOR, PATIENT, ADMIN
          SYSADMIN can create all four user types
          ADMIN cannot create SYSADMIN
        """
        _check_create_permission(creator, data.user_type)

        # Unique email check (DB constraint is backup)
        if self._repo.get_by_email(data.email.strip().lower()) is not None:
            raise ConflictError(f"Email '{data.email}' is already registered.")

        account = Account(
            email=data.email.strip().lower(),
            user_type=data.user_type,
            status=AccountStatus.INACTIVE,
            first_name=data.first_name,
            surname=data.family_name,
            date_of_birth=data.date_of_birth,
        )

        try:
            self._repo.add(account)
        except IntegrityError:
            raise ConflictError(f"Email '{data.email}' is already registered.")

        self._audit_svc.record(
            actor=creator.id,
            action=AuditAction.ACCOUNT_CREATED,
            target_type="account",
            target_id=str(account.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )

        # Token issuance is not best-effort — failure must propagate (no token = stuck account)
        from app.identity.activation import issue_activation_token  # noqa: PLC0415

        raw_token = issue_activation_token(account)

        # Email delivery is best-effort; admin can resend if queue fails (SR-033.7)
        try:
            from app.workers.email_tasks import send_activation_email  # noqa: PLC0415

            send_activation_email.delay(str(account.id), raw_token)
        except Exception:
            logger.warning(
                "Failed to enqueue activation email for account %s; admin resend required",
                account.id,
            )

        return account

    def get_profile(self, actor: Account, account_id: uuid.UUID) -> Account:
        """Fetch an account, enforcing authz (account:read)."""
        account = self._repo.get_by_id(account_id)
        if account is None:
            raise NotFoundError(f"Account {account_id} not found.")

        resource = Resource(
            resource_type="account",
            owner_id=account.id,
            patient_id=account.id if account.user_type == UserType.PATIENT else None,
        )
        self._authz_svc.authorize(actor, "account:read", resource)
        return account


def _check_create_permission(creator: Account, target_type: UserType) -> None:
    role = creator.user_type
    if role == UserType.SYSADMIN:
        return  # can create all four
    if role == UserType.ADMIN:
        if target_type == UserType.SYSADMIN:
            raise AuthorizationError("ADMIN cannot create SYSADMIN accounts.")
        return  # can create DOCTOR, PATIENT, ADMIN
    raise AuthorizationError("Only ADMIN or SYSADMIN can create accounts.")
