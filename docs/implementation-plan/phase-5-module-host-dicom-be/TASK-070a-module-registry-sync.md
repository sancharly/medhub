# TASK-070a — Wire module-registry sync into startup (remediation)

- **Phase:** 5 — Module host + DICOM backend
- **Implements / restores:** SR-016, SR-023; remediates TASK-070 (unblocks TASK-073 reachability)
- **Depends on:** TASK-070
- **Branch:** `feature/module-registry-sync`
- **Status:** Completed (fix/phase-5-audit 2026-06-30)
- **Source:** `AUDIT-LEDGER.md` — TASK-070 verdict **PARTIAL** (showstopper)

## Objective

`ModuleRegistryService.sync_installed` exists but is **never called at startup** — the app lifespan only
runs `discover_modules` + `register_all_modules`. So `module_registry` is never populated, `GET /modules`
and `GET /me/modules` are permanently empty, and no module (including the DICOM viewer) can ever be
enabled. Wire the sync and emit the per-module discovery audit event.

## Implementation detail

- In `app/main.py` lifespan, after discovery, call `ModuleRegistryService.sync_installed(manifests, db)`
  within a startup DB session (idempotent upsert).
- Emit `MODULE_DISCOVERED` per module (the constant exists but is never recorded).
- Remove the unused `db` param shape if not needed; ensure the real upsert path (not a mock) is exercised.

## Acceptance criteria

- [x] On startup, installed modules are persisted to `module_registry` (idempotent across restarts).
- [x] `GET /modules` lists the DICOM viewer; a SYSADMIN can enable it for a group and `GET /me/modules`
  then reflects it for members.
- [x] `MODULE_DISCOVERED` audit event emitted per module.

## Definition of Done

- [x] Lint + type-check pass
- [x] **Startup integration test** (`TestStartupSync::test_lifespan_wires_sync_installed`) passes
- [x] OpenAPI unchanged (endpoints exist) / regenerated if needed
- [x] Traceability row updated (SR-016 → TASK-070a → test)
- [x] Security review N/A (no new authz)

## Audit verdict (2026-06-30)

- **Verdict:** PASS
- Implemented in `fix/phase-5-audit`. `sync_installed` wired into `_lifespan` in `app/main.py` behind a try/rollback/finally DB session. `MODULE_DISCOVERED` audit event emitted per module inside the `sync_installed` loop. Startup integration test added in `backend/tests/modules/test_discovery.py::TestStartupSync`.
