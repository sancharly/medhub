---
id: "TASK-042"
type: task
title: "Per-group module enablement"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-015"
    relation: implements
  - target: "TASK-040"
    relation: relates_to
tags: ["audit-verified", "phase:3-domain-services"]
---

- **Phase:** 3 — Domain services
- **Software item / unit:** SI-GROUPS / U-GRP-ModuleEnable
- **Implements:** SR-015 (AC-1 enable, AC-2 disable); ADR-0005
- **Depends on:** TASK-040 (Group CRUD) — must be merged first
- **Branch:** `feature/module-enablement`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Let a system administrator enable or disable a module for one or more user groups. Enablement is **pure data** (groups × modules) per ADR-0005 — turning a module on/off requires no code change. This task owns the `GroupModuleEnablement` table and the `set_module_enabled` write; the runtime read/union and request gating are TASK-043 (`ModuleAccessGuard`). Traces to SR-015 AC-1/AC-2.

## Interfaces to honor

Extends `GroupService` from [12-interfaces.md](../../design/12-interfaces.md) §12.1:

```python
class GroupService:
    def set_module_enabled(self, actor: Account, group_id: UUID,
                           module_key: str, enabled: bool) -> None: ...   # SR-015
    def enabled_modules_for_group(self, group_id: UUID) -> list[str]: ...  # read for admin UI / guard
```

- `set_module_enabled` authorizes **sysadmin-only** via `AuthorizationService.authorize(actor, "modules:enable", group)` (SR-005, SR-015 control measure). Deny-by-default.
- This unit records the enablement edge only; it **must not** read a user's groups or make the runtime access decision (that is TASK-043, SI-AUTHZ). It validates `module_key` against the installed `ModuleRegistry` (TASK-070) so an unknown module cannot be enabled.

## Implementation detail

- Files to create / modify:
  - `backend/app/groups/service.py` — add `set_module_enabled`, `enabled_modules_for_group`.
  - `backend/app/db/models/group_module_enablement.py` — `GroupModuleEnablement`: `group_id` (FK groups), `module_key` (str, FK/soft-ref to `module_registry.module_key`), `enabled` (bool), `updated_at`; unique `(group_id, module_key)`.
  - `backend/app/db/repositories/group_repository.py` — `upsert_enablement(group_id, module_key, enabled)`, `enabled_module_keys_for_group(group_id)`, `enabled_module_keys_for_groups(group_ids)` (the last is consumed by TASK-043).
  - `backend/app/db/alembic/versions/<rev>_group_module_enablement.py` — migration.
- Endpoint (SI-API): `PUT /groups/{id}/modules/{moduleKey}` with body `{ "enabled": true|false }` ([api-design.md](../../specifications/api-design.md)). Idempotent upsert.
- Library: SQLAlchemy 2.x upsert (`insert(...).on_conflict_do_update`) on `(group_id, module_key)`.
- Audit (SR-023 AC-4 administrative action): record `module.enable` / `module.disable` with actor, group id, module key, new value.
- Error cases:
  - Non-sysadmin → `403 /errors/forbidden`.
  - Unknown group → `404 /errors/not-found`.
  - `module_key` not in `ModuleRegistry` → `404 /errors/not-found` (cannot enable a non-installed module).
  - Missing/invalid `enabled` → `400 /errors/validation-error`.
- Edge cases: enabling an already-enabled (or disabling an already-disabled) module is idempotent — same final state, still audited as an administrative action. Disabling sets `enabled = false` rather than deleting the row, preserving an auditable history.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/groups/test_module_enablement.py`):
  - sysadmin enables module for a group → enablement row `enabled=true`; appears in `enabled_modules_for_group` (SR-015 AC-1).
  - sysadmin enables the same module for multiple groups (SR-015 AC-1 "one or more groups").
  - sysadmin disables a previously enabled module → `enabled=false`; absent from enabled list (SR-015 AC-2).
  - enabling an unknown `module_key` → 404, nothing written (validation against ModuleRegistry).
  - enable then enable again → idempotent, single row, audited each time (SR-023).
  - non-sysadmin → denied 403, no change, denied-access audited (SR-005, SR-023).
- Integration (`backend/tests/api/test_module_enablement_api.py`): `PUT /groups/{id}/modules/{moduleKey}` toggles enablement; reflected in a follow-up read; non-sysadmin denied with `problem+json`.

## Acceptance criteria

- [x] A sysadmin can enable a module for one or more groups (SR-015 AC-1).
- [x] A sysadmin can disable a previously enabled module for a group (SR-015 AC-2).
- [x] Enablement is stored as pure data in `GroupModuleEnablement`; no code edit enables a module (ADR-0005).
- [x] Only installed (registered) modules can be enabled.
- [x] Enable/disable restricted to sysadmin and audited (SR-005, SR-023).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit + integration tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (enablement endpoint)
- [x] Audit events emitted for security-relevant actions (SR-023)
- [x] Traceability matrix row updated (SR-015 → TASK-042 → tests)
- [x] Security review N/A (authz consumed, not implemented here)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
