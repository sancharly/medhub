"""GroupService — group CRUD, membership management, module enablement (TASK-040/041/042)."""

from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError

from app.api.errors import ConflictError, NotFoundError, ValidationProblem
from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.authz.service import AuthorizationService, Resource
from app.db.models.account import Account
from app.db.models.audit import AuditOutcome
from app.db.models.group import Group, GroupMembership, MembershipSource
from app.db.repositories.account_repo import AccountRepository
from app.db.repositories.group_repo import GroupRepository
from app.db.repositories.module_repo import ModuleRepository


class GroupService:
    def __init__(
        self,
        group_repo: GroupRepository,
        account_repo: AccountRepository,
        module_repo: ModuleRepository,
        audit_svc: AuditService,
        authz_svc: AuthorizationService,
        consent_svc: object = None,
    ) -> None:
        self._group_repo = group_repo
        self._account_repo = account_repo
        self._module_repo = module_repo
        self._audit_svc = audit_svc
        self._authz_svc = authz_svc

    # --- TASK-040: Group CRUD ---

    def create_group(self, actor: Account, name: str) -> Group:
        """Create a new group. SYSADMIN only."""
        self._authz_svc.authorize(
            actor,
            "groups:create",
            Resource(resource_type="group", owner_id=None, patient_id=None),
        )

        trimmed = name.strip()
        if not trimmed:
            raise ValidationProblem("Group name must not be blank.")

        group = Group(name=trimmed)
        try:
            self._group_repo.add(group)
        except IntegrityError:
            raise ConflictError(f"A group named '{trimmed}' already exists.")

        self._audit_svc.record(
            actor=actor.id,
            action=AuditAction.GROUP_CREATE,
            target_type="group",
            target_id=str(group.id),
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        return group

    def list_groups(self, actor: Account) -> list[Group]:
        """List all groups. SYSADMIN only."""
        self._authz_svc.authorize(
            actor,
            "groups:list",
            Resource(resource_type="group", owner_id=None, patient_id=None),
        )
        return self._group_repo.list_all()

    # --- TASK-041: Membership management ---

    def add_member(self, actor: Account, group_id: uuid.UUID, account_id: uuid.UUID) -> None:
        """Add a MANUAL membership. SYSADMIN only. Idempotent."""
        self._authz_svc.authorize(
            actor,
            "groups:manage_members",
            Resource(resource_type="group", owner_id=None, patient_id=None),
        )

        group = self._group_repo.get(group_id)
        if group is None:
            raise NotFoundError(f"Group {group_id} not found.")

        account = self._account_repo.get_by_id(account_id)
        if account is None:
            raise NotFoundError(f"Account {account_id} not found.")

        # Check for existing MANUAL membership (idempotent)
        existing = self._group_repo.get_membership(group_id, account_id)
        if existing is not None and existing.source == MembershipSource.MANUAL:
            return  # already a manual member

        membership = GroupMembership(
            group_id=group_id,
            account_id=account_id,
            source=MembershipSource.MANUAL,
        )
        self._group_repo.add_membership(membership)

        self._audit_svc.record(
            actor=actor.id,
            action=AuditAction.GROUP_MEMBER_ADD,
            target_type="group_membership",
            target_id=f"{group_id}:{account_id}",
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )

    def remove_member(self, actor: Account, group_id: uuid.UUID, account_id: uuid.UUID) -> None:
        """Remove only the MANUAL membership. AUTO memberships are untouched."""
        self._authz_svc.authorize(
            actor,
            "groups:manage_members",
            Resource(resource_type="group", owner_id=None, patient_id=None),
        )

        self._group_repo.remove_membership(group_id, account_id, MembershipSource.MANUAL)

        self._audit_svc.record(
            actor=actor.id,
            action=AuditAction.GROUP_MEMBER_REMOVE,
            target_type="group_membership",
            target_id=f"{group_id}:{account_id}",
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )

    def groups_of(self, account_id: uuid.UUID) -> list[Group]:
        """Return all groups the account belongs to (any source)."""
        memberships = self._group_repo.memberships_for_account(account_id)
        groups = []
        for m in memberships:
            group = self._group_repo.get(m.group_id)
            if group is not None:
                groups.append(group)
        return groups

    def sync_automatic_membership(self, account: Account) -> None:
        """Sync AUTO group memberships based on account.user_type."""
        from app.groups.auto_membership import sync_automatic_membership  # noqa: PLC0415

        sync_automatic_membership(account, self._group_repo)

    # --- TASK-042: Module enablement ---

    def set_module_enabled(
        self, actor: Account, group_id: uuid.UUID, module_key: str, enabled: bool
    ) -> None:
        """Enable or disable a module for a group. SYSADMIN only."""
        self._authz_svc.authorize(
            actor,
            "modules:enable",
            Resource(resource_type="group_module", owner_id=None, patient_id=None),
        )

        group = self._group_repo.get(group_id)
        if group is None:
            raise NotFoundError(f"Group {group_id} not found.")

        module = self._module_repo.get_by_key(module_key)
        if module is None:
            raise NotFoundError(f"Module '{module_key}' not registered.")

        self._module_repo.set_enablement(group_id, module.id, enabled)

        action = AuditAction.MODULE_ENABLE if enabled else AuditAction.MODULE_DISABLE
        self._audit_svc.record(
            actor=actor.id,
            action=action,
            target_type="group_module",
            target_id=f"{group_id}:{module_key}",
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )

    def enabled_modules_for_group(self, group_id: uuid.UUID) -> list[str]:
        """Return list of enabled module keys for a group."""
        return self._module_repo.enabled_module_keys_for_group(group_id)
