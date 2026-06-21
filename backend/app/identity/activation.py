"""Account activation via 72h token (TASK-032).

Token lifecycle:
  issue_activation_token → raw token emailed, sha256 hash stored on account
  activate(token, password) → validate hash + expiry, set password, set ACTIVE
  resend_activation → ADMIN/SYSADMIN only; new token invalidates prior
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from app.api.errors import AuthorizationError, NotFoundError, UnauthenticatedError
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.auth.password import PasswordService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.audit import AuditOutcome
from app.db.repositories.account_repo import AccountRepository

TOKEN_EXPIRY_HOURS = 72


def _sha256(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_activation_token(account: Account) -> str:
    """Generate a token, store its sha256 hash on the account, return the raw token.

    The raw token must go only into the email — never logged or returned via API.
    """
    raw_token = secrets.token_urlsafe(32)
    account.activation_token_hash = _sha256(raw_token)
    account.activation_token_expires_at = datetime.now(UTC) + timedelta(hours=TOKEN_EXPIRY_HOURS)
    return raw_token


class ActivationService:
    def __init__(
        self,
        account_repo: AccountRepository,
        password_svc: PasswordService,
        audit_svc: AuditService,
    ) -> None:
        self._repo = account_repo
        self._password_svc = password_svc
        self._audit_svc = audit_svc

    def activate(self, account_id: uuid.UUID, token: str, password: str) -> Account:
        """Activate an account: validate token, set password, set ACTIVE.

        Raises UnauthenticatedError for any invalid combination (generic — no hint).
        Raises PasswordPolicyError if password policy is violated.
        """
        account = self._repo.get_by_id(account_id)
        if account is None:
            raise UnauthenticatedError("Invalid or expired activation token.")

        if not self._validate_token(account, token):
            raise UnauthenticatedError("Invalid or expired activation token.")

        if account.status != AccountStatus.INACTIVE:
            raise UnauthenticatedError("Account is not awaiting activation.")

        # Validate and hash the password
        self._password_svc.validate_policy(account, password, skip_history=True)
        pw_hash = self._password_svc.hash(password)

        account.password_hash = pw_hash
        account.status = AccountStatus.ACTIVE
        account.password_changed_at = datetime.now(UTC)

        # Invalidate the token
        account.activation_token_hash = None
        account.activation_token_expires_at = None

        self._audit_svc.record(
            actor=account.id,
            action=AuditAction.ACCOUNT_ACTIVATED,
            target_type="account",
            target_id=str(account.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )

        return account

    def resend_activation(self, actor: Account, account_id: uuid.UUID) -> str:
        """Re-issue an activation token. ADMIN or SYSADMIN only.

        Returns the raw token (caller must email it — never expose via API response).
        """
        if actor.user_type not in (UserType.ADMIN, UserType.SYSADMIN):
            raise AuthorizationError("Only ADMIN or SYSADMIN can resend activation emails.")

        account = self._repo.get_by_id(account_id)
        if account is None:
            raise NotFoundError(f"Account {account_id} not found.")

        raw_token = issue_activation_token(account)

        self._audit_svc.record(
            actor=actor.id,
            action=AuditAction.ACTIVATION_LINK_RESENT,
            target_type="account",
            target_id=str(account.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )

        return raw_token

    def _validate_token(self, account: Account, token: str) -> bool:
        if account.activation_token_hash is None or account.activation_token_expires_at is None:
            return False
        if datetime.now(UTC) > account.activation_token_expires_at:
            return False
        expected = _sha256(token)
        return secrets.compare_digest(account.activation_token_hash, expected)
