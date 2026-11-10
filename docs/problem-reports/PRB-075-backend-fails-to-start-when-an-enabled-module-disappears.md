---
id: "PRB-075"
type: problem-report
title: "The backend does not start when a module with group enablement rows is uninstalled or its manifest is rejected"
status: open
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-08"
updated: "2026-11-08"
criticality: major
links: []
tags: ["modules", "hazard:availability", "found-in:TASK-201-qa"]
---

# PRB-075 — The backend does not start when a module with group enablement rows is uninstalled or its manifest is rejected

## Observed

Found by QA while reviewing TASK-201 (QA review 1, 2026-11-08, finding 1, against HEAD b905560). The
backend does not start when a group still has an enablement row for a module, enabled or not, and that
module is either:

- uninstalled, or
- still installed but its manifest is rejected by discovery.

QA confirmed the database part on PostgreSQL 16: `DELETE FROM module_registry` fails with 23503 when a
`group_module_enablement` row for the module has `enabled=false`. The full start-up failure follows from
the code below. It was not reproduced on a started stack.

## Impact

Availability. One module's state takes down the whole API, so every user loses access to every function,
clinical records included (RISK-007), until an operator acts. Two operations reach it, both only while
at least one other module is still discovered, because with none the lifespan skips the sync. `dicom-viewer`
is the only module today, so **neither path is reachable in the current configuration**; the problem
becomes real with a second module installed:

- uninstalling a module that any group has ever had enabled, while at least one other module is still
  discovered (with none, the sync is skipped);
- an upgrade whose manifest fails discovery. Discovery rejects a malformed `module_key` (check added by
  TASK-192, `backend/app/modules/discovery.py:37-38`) or version (TASK-200, `discovery.py:43-47`), and a
  rejected module counts as absent; the other module must still be discovered for the sync to run.

Disabling the module for every group first does not help, because disabling keeps the row.

**Operator workaround:** fix the manifest, or reinstall the previous module version, then restart the
backend.

## Investigation

1. At start-up the lifespan calls `ModuleRegistryService.sync_installed`, then `commit`
   (`backend/app/main.py:68-75`).
2. `sync_installed` upserts each discovered manifest, collects `present_keys`, then calls
   `self._repo.remove_absent(present_keys)` (`backend/app/modules/registry_service.py:45`). A module that
   failed discovery or is not installed is not in `present_keys`.
3. `ModuleRepository.remove_absent` issues
   `DELETE FROM module_registry WHERE module_key NOT IN (…)` (`backend/app/db/repositories/module_repo.py:102-107`).
4. `group_module_enablement.module_id` references `module_registry.id` through
   `fk_group_module_enablement_module_id`, which has no `ON DELETE` clause
   (`backend/app/db/alembic/versions/0001_initial.py:151-155`). The default is `NO ACTION`, so the delete fails
   with `ForeignKeyViolation` (SQLSTATE 23503) while any enablement row for the module exists.
5. `set_enablement` only updates `enabled` and never deletes the row (`module_repo.py:30-42`), so a
   disabled module still has its rows.
6. The lifespan catches the exception, rolls back, logs "Module registry sync failed at startup — modules
   unreachable" and re-raises (`backend/app/main.py:76-79`). The application does not start.

Root cause: the sync treats "absent from discovery" as "delete the registry row". That conflicts with a
foreign key that protects the enablement rows, and the start-up fails closed on any sync error. The
expected behaviour has not been decided: mark the module absent and keep its rows, cascade the delete, or
skip the row with a warning. That decision belongs to the CR that takes this PRB. It also touches what
`docs/design/11-risks-and-technical-debt.md` lists as an open decision (TASK-201 QA finding 1).

Related observation, tightened by TASK-202: `module_key.notin_([])` with no module discovered would match every
row, but the lifespan skips the sync when no manifest is discovered (`if manifests:` in `main.py`), so it does not
apply at start-up. It matters only if something else calls the sync with an empty list. "Uninstalling" reaches the
failure only when at least one other module is still discovered, because that is the only case in which the sync runs.

## Safety evaluation

No data is disclosed or altered; the transaction rolls back, so the registry and enablement rows survive.
The failure is total unavailability, not a wrong answer. Contributes to RISK-007.

- SR-016 (modular plugin architecture) AC 1: a module can be added without modifying other modules. In
  practice removing or upgrading one can stop the platform.
- SR-015 (per-group module enablement): the enablement rows that SR-015 creates are what block the start.

Criticality **major**: one routine operator action makes the whole application unavailable. There is a
documented workaround, the data is intact, and it needs an operator action, so it is not `critical`. No
release exists (CR-004 A-1), so no notification is needed. The human sets the final criticality.

## Resolution

Not fixed. Known anomaly outside CR-004, pending the human's decision. It has no `resolves` link.

## Source

TASK-201 QA review 1, finding 1 (`docs/design-outputs/tasks/TASK-201-arc42-and-design-records-for-cr-004.md`).

## Version history

- 1.0 (2026-11-08) — Created from the TASK-201 QA review. `open`, `major`.
