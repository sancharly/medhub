"""Account deactivate/reactivate lifecycle (TASK-033)."""

from __future__ import annotations

import uuid

from app.api.errors import AuthorizationError
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.auth.session import SessionService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.audit import AuditOutcome
from app.db.repositories.account_repo import AccountRepository


class LifecycleService:
    def __init__(
        self,
        account_repo: AccountRepository,
        session_svc: SessionService,
        audit_svc: AuditService,
    ) -> None:
        self._repo = account_repo
        self._session_svc = session_svc
        self._audit_svc = audit_svc

    def deactivate(self, actor: Account, account_id: uuid.UUID) -> None:
        """Deactivate an account. SYSADMIN only. Rejects self-deactivation.

        Kills all existing sessions synchronously, then enqueues propagation.
        """
        if actor.user_type != UserType.SYSADMIN:
            raise AuthorizationError("Only SYSADMIN can deactivate accounts.")
        if actor.id == account_id:
            raise AuthorizationError("Cannot deactivate your own account.")

        account = self._repo.get_by_id(account_id)
        if account is None:
            from app.api.errors import NotFoundError  # noqa: PLC0415

            raise NotFoundError(f"Account {account_id} not found.")

        account.status = AccountStatus.DEACTIVATED

        # Flush status change to DB before killing Redis sessions; ensures the account
        # is seen as DEACTIVATED by any DB read, even before the transaction commits.
        self._repo.flush()

        # Kill sessions synchronously
        self._session_svc.invalidate_all(account_id)

        # Enqueue async propagation task
        try:
            from app.workers.session_tasks import propagate_session_kill  # noqa: PLC0415

            propagate_session_kill.delay(str(account_id))
        except Exception:
            pass  # Best-effort; sync invalidation already done

        self._audit_svc.record(
            actor=actor.id,
            action=AuditAction.ACCOUNT_DEACTIVATED,
            target_type="account",
            target_id=str(account_id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )

    def reactivate(self, actor: Account, account_id: uuid.UUID) -> None:
        """Reactivate a DEACTIVATED account. SYSADMIN only."""
        if actor.user_type != UserType.SYSADMIN:
            raise AuthorizationError("Only SYSADMIN can reactivate accounts.")

        account = self._repo.get_by_id(account_id)
        if account is None:
            from app.api.errors import NotFoundError  # noqa: PLC0415

            raise NotFoundError(f"Account {account_id} not found.")

        account.status = AccountStatus.ACTIVE

        self._audit_svc.record(
            actor=actor.id,
            action=AuditAction.ACCOUNT_REACTIVATED,
            target_type="account",
            target_id=str(account_id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
