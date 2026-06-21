"""ModuleAccessGuard — checks whether a module is enabled for an account (TASK-043)."""

from __future__ import annotations

import uuid

from app.db.repositories.group_repo import GroupRepository
from app.db.repositories.module_repo import ModuleRepository


class ModuleAccessGuard:
    def __init__(self, group_repo: GroupRepository, module_repo: ModuleRepository) -> None:
        self._group_repo = group_repo
        self._module_repo = module_repo

    def is_module_enabled(self, account_id: uuid.UUID, module_key: str) -> bool:
        """Return True if any of the account's groups has the module enabled.

        Unknown module_key returns False (deny-by-default).
        """
        memberships = self._group_repo.memberships_for_account(account_id)
        if not memberships:
            return False

        group_ids = [m.group_id for m in memberships]
        enabled_keys = self._module_repo.enabled_module_keys_for_groups(group_ids)
        return module_key in enabled_keys
