"""ModuleRegistryService — sync discovered manifests to DB (TASK-070)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.audit.actions import AuditAction
from app.audit.service import AuditService
from app.db.models.audit import AuditOutcome
from app.db.models.module import ModuleRegistry
from app.db.repositories.module_repo import ModuleRepository
from app.modules.contract import ModuleManifest

logger = logging.getLogger(__name__)


class ModuleRegistryService:
    def __init__(self, module_repo: ModuleRepository, audit_svc: AuditService) -> None:
        self._repo = module_repo
        self._audit_svc = audit_svc

    def sync_installed(self, manifests: list[ModuleManifest], db: object) -> None:
        """Upsert all discovered manifests; remove absent ones; emit audit event."""
        now = datetime.now(UTC)
        present_keys: list[str] = []
        for manifest in manifests:
            self._repo.upsert(
                module_key=manifest.module_key,
                name=manifest.name,
                version=manifest.version,
                required_permissions=manifest.required_permissions,
                discovered_at=now,
            )
            present_keys.append(manifest.module_key)

        self._repo.remove_absent(present_keys)

        self._audit_svc.record(
            actor=None,
            action=AuditAction.MODULE_REGISTRY_SYNC,
            target_type="module_registry",
            target_id=None,
            outcome=AuditOutcome.SUCCESS,
            ip=None,
        )
        logger.info("Module registry synced — %d module(s) installed", len(present_keys))

    def list_installed(self) -> list[ModuleRegistry]:
        return self._repo.list_installed()

    def get(self, module_key: str) -> ModuleRegistry | None:
        return self._repo.get_by_key(module_key)
