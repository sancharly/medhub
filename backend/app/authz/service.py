"""AuthorizationService — RBAC + ownership (TASK-027).

Decision algorithm (deny-by-default):
  PATIENT  → allow account:read / clinical:read own resources only
  DOCTOR   → allow clinical:read / clinical:write iff effective_access() is True
  ADMIN    → deny all clinical:*; non-clinical reads via admin projection
  SYSADMIN → account-lifecycle / group / module-admin only
  Default  → DENY

Decision carries: allow + basis (OWNER | CONSENT:MANUAL | CONSENT:APPOINTMENT:{id} | ROLE)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

from app.api.errors import AuthorizationError
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.db.models.account import Account, UserType
from app.db.models.audit import AuditOutcome

DecisionBasis = Literal["OWNER", "ROLE"] | str  # "CONSENT:MANUAL", "CONSENT:APPOINTMENT:{id}"


@dataclass
class Decision:
    allow: bool
    basis: DecisionBasis


@dataclass
class Resource:
    """Lightweight resource descriptor passed to authorize()."""

    resource_type: str  # e.g. "account", "clinical_entry"
    owner_id: uuid.UUID | None  # account that owns this resource
    patient_id: uuid.UUID | None  # patient the resource belongs to


class AuthorizationService:
    def __init__(
        self,
        consent_svc: object,  # ConsentService — injected to avoid circular import
        audit_svc: AuditService,
    ) -> None:
        self._consent_svc = consent_svc
        self._audit_svc = audit_svc

    def authorize(
        self,
        actor: Account,
        action: str,
        resource: Resource,
    ) -> Decision:
        """Evaluate the access request and return a Decision.

        Raises AuthorizationError (403) on deny after auditing.
        """
        decision = self._evaluate(actor, action, resource)

        if decision.allow:
            self._audit_svc.record(
                actor=actor.id,
                action=AuditAction.AUTHZ_ALLOWED,
                target_type=resource.resource_type,
                target_id=str(resource.owner_id or resource.patient_id or ""),
                outcome=AuditOutcome.SUCCESS,
                ip=None,
            )
        else:
            self._audit_svc.record(
                actor=actor.id,
                action=AuditAction.AUTHZ_DENIED,
                target_type=resource.resource_type,
                target_id=str(resource.owner_id or resource.patient_id or ""),
                outcome=AuditOutcome.FAILURE,
                ip=None,
            )
            raise AuthorizationError("You do not have permission to perform this action.")

        return decision

    def _evaluate(self, actor: Account, action: str, resource: Resource) -> Decision:
        role = actor.user_type

        if role == UserType.PATIENT:
            return self._eval_patient(actor, action, resource)
        if role == UserType.DOCTOR:
            return self._eval_doctor(actor, action, resource)
        if role == UserType.ADMIN:
            return self._eval_admin(actor, action, resource)
        if role == UserType.SYSADMIN:
            return self._eval_sysadmin(actor, action, resource)

        return Decision(allow=False, basis="ROLE")

    def _eval_patient(self, actor: Account, action: str, resource: Resource) -> Decision:
        # Patients may only read their own account and clinical data
        own = resource.owner_id == actor.id or resource.patient_id == actor.id
        if action in ("account:read", "clinical:read") and own:
            return Decision(allow=True, basis="OWNER")
        return Decision(allow=False, basis="OWNER")

    def _eval_doctor(self, actor: Account, action: str, resource: Resource) -> Decision:
        if action not in ("clinical:read", "clinical:write", "account:read"):
            return Decision(allow=False, basis="ROLE")

        # Doctors can read their own account
        if action == "account:read" and resource.owner_id == actor.id:
            return Decision(allow=True, basis="OWNER")

        patient_id = resource.patient_id
        if patient_id is None:
            return Decision(allow=False, basis="ROLE")

        has_access = self.effective_access(actor.id, patient_id)
        if has_access:
            return Decision(allow=True, basis="CONSENT:MANUAL")

        return Decision(allow=False, basis="ROLE")

    def _eval_admin(self, actor: Account, action: str, resource: Resource) -> Decision:
        # Admins cannot access clinical data
        if action.startswith("clinical:"):
            return Decision(allow=False, basis="ROLE")
        # Non-clinical reads are allowed (admin projection enforced at API layer)
        if action in ("account:read", "account:list"):
            return Decision(allow=True, basis="ROLE")
        return Decision(allow=False, basis="ROLE")

    def _eval_sysadmin(self, actor: Account, action: str, resource: Resource) -> Decision:
        # SYSADMINs handle account lifecycle, groups, modules — NOT clinical data
        if action.startswith("clinical:"):
            return Decision(allow=False, basis="ROLE")
        lifecycle_actions = {
            "account:create",
            "account:read",
            "account:list",
            "account:deactivate",
            "account:reactivate",
            "account:delete",
            "group:manage",
            "module:manage",
            "account:unlock",
        }
        if action in lifecycle_actions:
            return Decision(allow=True, basis="ROLE")
        return Decision(allow=False, basis="ROLE")

    def effective_access(self, doctor_id: uuid.UUID, patient_id: uuid.UUID) -> bool:
        """Live consent check — no cache."""
        result: bool = self._consent_svc.has_active_grant(  # type: ignore[attr-defined]
            doctor_id, patient_id
        )
        return result


def get_authorization_service() -> AuthorizationService:
    """Default factory used by the FastAPI dependency system.

    Wires up real dependencies. In tests, use dependency_overrides.
    """
    from app.audit.service import AuditService  # noqa: PLC0415
    from app.authz.consent import ConsentService  # noqa: PLC0415
    from app.db.repositories.audit_repo import AuditRepository  # noqa: PLC0415
    from app.db.repositories.consent_repo import ConsentRepository  # noqa: PLC0415
    from app.db.repositories.session import get_db  # noqa: PLC0415

    db = next(get_db())
    audit_svc = AuditService(AuditRepository(db))
    consent_svc = ConsentService(ConsentRepository(db), audit_svc)
    return AuthorizationService(consent_svc, audit_svc)
