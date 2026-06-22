"""ModuleRegistry and GroupModuleEnablement repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.module import GroupModuleEnablement, ModuleRegistry
from app.db.repositories.base import Repository


class ModuleRepository(Repository[ModuleRegistry]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ModuleRegistry)

    def get_by_key(self, module_key: str) -> ModuleRegistry | None:
        result = self._session.execute(
            select(ModuleRegistry).where(ModuleRegistry.module_key == module_key)
        )
        return result.scalar_one_or_none()

    def get_enablement(
        self, group_id: uuid.UUID, module_id: uuid.UUID
    ) -> GroupModuleEnablement | None:
        return self._session.get(GroupModuleEnablement, (group_id, module_id))

    def set_enablement(
        self, group_id: uuid.UUID, module_id: uuid.UUID, enabled: bool
    ) -> GroupModuleEnablement:
        enablement = self.get_enablement(group_id, module_id)
        if enablement is None:
            enablement = GroupModuleEnablement(
                group_id=group_id, module_id=module_id, enabled=enabled
            )
            self._session.add(enablement)
        else:
            enablement.enabled = enabled
        self._session.flush()
        return enablement

    def enabled_module_keys_for_group(self, group_id: uuid.UUID) -> list[str]:
        result = self._session.execute(
            select(ModuleRegistry.module_key)
            .join(
                GroupModuleEnablement,
                GroupModuleEnablement.module_id == ModuleRegistry.id,
            )
            .where(
                GroupModuleEnablement.group_id == group_id,
                GroupModuleEnablement.enabled.is_(True),
            )
        )
        return list(result.scalars().all())

    def enabled_module_keys_for_groups(self, group_ids: list[uuid.UUID]) -> list[str]:
        if not group_ids:
            return []
        result = self._session.execute(
            select(ModuleRegistry.module_key)
            .join(
                GroupModuleEnablement,
                GroupModuleEnablement.module_id == ModuleRegistry.id,
            )
            .where(
                GroupModuleEnablement.group_id.in_(group_ids),
                GroupModuleEnablement.enabled.is_(True),
            )
        )
        return list(result.scalars().all())
