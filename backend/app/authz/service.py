"""AuthorizationService — RBAC + ownership (TASK-027).

Decision algorithm (deny-by-default):
  PATIENT  → allow account:read / clinical:read own resources only
  DOCTOR   → allow clinical:read / clinical:write iff effective_access() is True
  ADMIN    → deny all clinical:*; non-clinical reads via admin projection
  SYSADMIN → account-lifecycle / group / module-admin only
  Default  → DENY

Identity actions (account:create / deactivate / reactivate / delete, activation:resend) are
decided in ``_eval_identity`` and audited like every other decision (ADR-0006, TASK-188).

Decision carries: allow + basis (OWNER | CONSENT:MANUAL | CONSENT:APPOINTMENT:{id} | ROLE)
"""

from __future__ import annotations

import enum
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
    doctor_id: uuid.UUID | None = None  # doctor of an appointment (appointment:read)
    resource_id: str | None = None  # audit target (appointment id, module key)
    module_enabled: bool | None = None  # ModuleAccessGuard result (module:access)
    target_user_type: UserType | None = None  # type of the account being created (account:create)


class AppointmentScopeKind(enum.Enum):
    ALL = "ALL"
    AS_DOCTOR = "AS_DOCTOR"
    AS_PATIENT = "AS_PATIENT"
    NONE = "NONE"


@dataclass(frozen=True)
class AppointmentScope:
    """Which appointments the actor may list (decided by ``appointment_scope``)."""

    kind: AppointmentScopeKind
    account_id: uuid.UUID | None = None


_IDENTITY_ACTIONS = frozenset(
    {
        "account:create",
        "account:deactivate",
        "account:reactivate",
        "account:delete",
        "activation:resend",
    }
)


# Actions that exactly one role may perform, whoever the target is (TASK-189). Router-level
# checks that used to compare ``user_type`` in the handler; a denial keeps ``basis="ROLE"``.
_ROLE_ONLY_ACTIONS: dict[str, UserType] = {
    "account:unlock": UserType.SYSADMIN,
    "module:list": UserType.SYSADMIN,
    "consent:grant": UserType.PATIENT,
    "consent:revoke": UserType.PATIENT,
    "consent:list": UserType.PATIENT,
    "patient_roster:list": UserType.DOCTOR,
}


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
        decision = self.decide(actor, action, resource)
        if not decision.allow:
            raise AuthorizationError("You do not have permission to perform this action.")
        return decision

    def decide(
        self,
        actor: Account,
        action: str,
        resource: Resource,
    ) -> Decision:
        """Evaluate and audit the access request; never raises on deny.

        For callers that must answer a refusal with a message of their own; the decision
        is audited exactly as ``authorize`` does (SR-023 AC 7).
        """
        decision = self._evaluate(actor, action, resource)
        target_id = resource.resource_id or str(resource.owner_id or resource.patient_id or "")

        if decision.allow:
            self._audit_svc.record(
                actor=actor.id,
                action=AuditAction.AUTHZ_ALLOWED,
                target_type=resource.resource_type,
                target_id=target_id,
                outcome=AuditOutcome.SUCCESS,
                ip=None,
            )
        else:
            self._audit_svc.record(
                actor=actor.id,
                action=AuditAction.AUTHZ_DENIED,
                target_type=resource.resource_type,
                target_id=target_id,
                outcome=AuditOutcome.FAILURE,
                ip=None,
            )

        return decision

    def appointment_scope(self, actor: Account) -> AppointmentScope:
        """Decide which appointments the actor lists; audited as ``appointment:list``.

        Raises AuthorizationError (403) after auditing when the actor may not list.
        """
        self.authorize(
            actor,
            "appointment:list",
            Resource(resource_type="appointment", owner_id=None, patient_id=None),
        )
        if actor.user_type in (UserType.ADMIN, UserType.SYSADMIN):
            return AppointmentScope(AppointmentScopeKind.ALL)
        if actor.user_type == UserType.DOCTOR:
            return AppointmentScope(AppointmentScopeKind.AS_DOCTOR, actor.id)
        if actor.user_type == UserType.PATIENT:
            return AppointmentScope(AppointmentScopeKind.AS_PATIENT, actor.id)
        return AppointmentScope(AppointmentScopeKind.NONE)

    def _evaluate(self, actor: Account, action: str, resource: Resource) -> Decision:
        if action == "appointment:read":
            return self._eval_appointment_read(actor, resource)
        if action == "module:access":
            # The module guard's live result is the input; no role overrides it (SR-015).
            if resource.module_enabled is True:
                return Decision(allow=True, basis="MODULE:ENABLED")
            return Decision(allow=False, basis="MODULE:DISABLED")

        if action in _ROLE_ONLY_ACTIONS:
            return Decision(allow=actor.user_type == _ROLE_ONLY_ACTIONS[action], basis="ROLE")
        if action in _IDENTITY_ACTIONS:
            return self._eval_identity(actor, action, resource)

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

    def _eval_identity(self, actor: Account, action: str, resource: Resource) -> Decision:
        """Identity and account-lifecycle decisions (SR-032 AC 1/4/5, SR-034 AC 1).

        The basis of a denial says why, so a caller can keep its refusal message:
        ``ROLE`` (the role may not), ``TARGET`` (ADMIN creating SYSADMIN), ``TARGET_UNSET``
        (no requested type), ``SELF`` (SYSADMIN deactivating itself).
        """
        role = actor.user_type
        if action == "account:create":
            # Deny unless the requested type is stated, whatever the role.
            if resource.target_user_type is None:
                return Decision(allow=False, basis="TARGET_UNSET")
            if role == UserType.SYSADMIN:
                return Decision(allow=True, basis="ROLE")
            if role == UserType.ADMIN:
                if resource.target_user_type == UserType.SYSADMIN:
                    return Decision(allow=False, basis="TARGET")
                return Decision(allow=True, basis="ROLE")
            return Decision(allow=False, basis="ROLE")
        if action == "account:deactivate":
            if role != UserType.SYSADMIN:
                return Decision(allow=False, basis="ROLE")
            if resource.owner_id == actor.id:
                return Decision(allow=False, basis="SELF")
            return Decision(allow=True, basis="ROLE")
        if action == "account:reactivate":
            return Decision(allow=role == UserType.SYSADMIN, basis="ROLE")
        if action == "account:delete":
            if role == UserType.SYSADMIN:
                return Decision(allow=True, basis="ROLE")
            if resource.owner_id is not None and resource.owner_id == actor.id:
                return Decision(allow=True, basis="OWNER")
            return Decision(allow=False, basis="ROLE")
        # activation:resend
        return Decision(allow=role in (UserType.ADMIN, UserType.SYSADMIN), basis="ROLE")

    def _eval_appointment_read(self, actor: Account, resource: Resource) -> Decision:
        """Visible to the appointment's doctor, its patient, and ADMIN/SYSADMIN (SR-011 AC 4)."""
        if actor.user_type in (UserType.ADMIN, UserType.SYSADMIN):
            return Decision(allow=True, basis="ROLE")
        if actor.id in (resource.doctor_id, resource.patient_id):
            return Decision(allow=True, basis="OWNER")
        return Decision(allow=False, basis="ROLE")

    def _eval_patient(self, actor: Account, action: str, resource: Resource) -> Decision:
        # Patients may only read their own account and clinical data
        own = resource.owner_id == actor.id or resource.patient_id == actor.id
        if action in ("account:read", "clinical:read") and own:
            return Decision(allow=True, basis="OWNER")
        # Patients can confirm/decline their own appointments
        if (
            action in ("appointment:confirm", "appointment:decline")
            and resource.owner_id == actor.id
        ):
            return Decision(allow=True, basis="OWNER")
        # Patients can list their own appointments (scoped at repo level)
        if action == "appointment:list":
            return Decision(allow=True, basis="OWNER")
        return Decision(allow=False, basis="OWNER")

    def _eval_doctor(self, actor: Account, action: str, resource: Resource) -> Decision:
        if action in ("appointment:create", "appointment:list"):
            return Decision(allow=True, basis="ROLE")
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
        if action in ("account:read", "account:list", "appointment:create", "appointment:list"):
            return Decision(allow=True, basis="ROLE")
        return Decision(allow=False, basis="ROLE")

    def _eval_sysadmin(self, actor: Account, action: str, resource: Resource) -> Decision:
        # SYSADMINs handle account lifecycle, groups, modules — NOT clinical data
        if action.startswith("clinical:"):
            return Decision(allow=False, basis="ROLE")
        lifecycle_actions = {
            "account:read",
            "account:list",
            "group:manage",
            "module:manage",
            # Phase 3 additions
            "groups:create",
            "groups:list",
            "groups:manage_members",
            "modules:enable",
            "appointment:create",
            "appointment:list",
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
