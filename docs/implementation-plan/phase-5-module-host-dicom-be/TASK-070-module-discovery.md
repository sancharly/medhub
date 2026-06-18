# TASK-070 — Module discovery + ModuleManifest + registry

- **Phase:** 5 — Module host + DICOM backend
- **Software item / unit:** SI-MODHOST / U-MH-Discovery
- **Implements:** SR-016 (AC-1 add without modifying existing modules, AC-3 defined contract); ADR-0005
- **Depends on:** TASK-042 (per-group module enablement — `ModuleRegistry` is the soft-ref target for enablement) — must be merged first
- **Branch:** `feature/module-discovery`
- **Status:** Not started

## Objective

Discover installed backend modules at startup via Python packaging **entry points** in the `medhub.modules` group, load and validate each module's `ModuleManifest`, and persist the installed set to the `ModuleRegistry` table. Adding a module is a new package exposing the entry point — **zero edits** to existing modules or the core, and enablement remains pure data (TASK-042). Traces to SR-016 AC-1/AC-3 and ADR-0005.

## Interfaces to honor

Loads the **Module Contract** from [12-interfaces.md](../../design/12-interfaces.md) §12.1 / [api-design.md](../../specifications/api-design.md) **verbatim**:

```python
class ModuleManifest:
    module_key: str
    name: str
    version: str
    required_permissions: list[str]
    def register(self, registry: RouterRegistry, services: PlatformServices) -> None: ...
```

- Discovery uses Python entry points group **`medhub.modules`** (ADR-0005). A module package declares, in its `pyproject.toml`, `[project.entry-points."medhub.modules"]` → a callable/object yielding its `ModuleManifest`.
- This unit only **discovers, validates, and records** manifests; it does **not** mount routers (TASK-072) or build `PlatformServices` (TASK-071). It must not import any module's internals beyond loading its declared entry point (§12.1 invariants).
- Validation enforces the manifest invariants: non-empty `module_key` (stable id), `name`, `version` (semver), `required_permissions` a list of known permission strings; a malformed manifest is rejected and logged, not crashed-on (a bad module must not take down the host — ADR-0005 negative note).

## Implementation detail

- Files to create:
  - `backend/app/modules/contract.py` — the `ModuleManifest` protocol/ABC, `RouterRegistry` and `PlatformServices` type references (concrete impls in TASK-071/072), exactly matching §12.1 signatures.
  - `backend/app/modules/discovery.py` — `discover_modules() -> list[ModuleManifest]` using `importlib.metadata.entry_points(group="medhub.modules")`; load each, validate, collect; isolate per-module load errors (one bad module does not abort discovery).
  - `backend/app/modules/registry.py` — `ModuleRegistry` service: `sync_installed(manifests)` upserts rows; `list_installed()`; `get(module_key)`.
  - `backend/app/db/models/module_registry.py` — `ModuleRegistryRow`: `module_key` (PK/unique), `name`, `version`, `required_permissions` (JSONB), `discovered_at`.
  - `backend/app/db/repositories/module_repository.py` — `upsert(row)`, `list_all()`, `get(module_key)` (parameterized).
  - `backend/app/db/alembic/versions/<rev>_module_registry.py` — migration.
  - Startup wiring in `backend/app/main.py` (lifespan): run discovery → `sync_installed` (surgical addition).
- Endpoint (SI-API): `GET /modules` returns the installed registry (sysadmin) ([api-design.md](../../specifications/api-design.md)). TASK-042's enablement validates `module_key` against this registry.
- Audit: module discovery is a startup/administrative concern; record a `module.discovered`/`module.registry.sync` administrative event when the installed set changes (SR-023 AC-4).
- Error cases: a module entry point that fails to import or whose manifest is invalid → logged + skipped, **not** registered (deny-by-default — it cannot be enabled); discovery continues for the rest.
- Edge cases: a module previously installed but no longer present → mark absent/remove from registry so it can no longer be enabled (enablement rows for an absent module are inert). Re-running discovery is idempotent (upsert by `module_key`). The DICOM viewer (TASK-073) is discovered through exactly this path, proving SR-016 AC-1/AC-4.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/modules/test_discovery.py`):
  - a fake package exposing a valid `medhub.modules` entry point is discovered and its manifest validated (SR-016 AC-1/AC-3).
  - `sync_installed` upserts the `ModuleRegistry` row with key/name/version/permissions; re-run is idempotent.
  - a malformed manifest (missing `module_key`, bad version, non-list permissions) is rejected and skipped; discovery of others continues (ADR-0005 isolation).
  - an entry point that raises on import is isolated; other modules still register.
  - a previously-installed module now absent is removed/marked, so it cannot be enabled (TASK-042 cross-check).
  - `list_installed` / `GET /modules` returns the registered set to a sysadmin; non-sysadmin denied (SR-005).
  - registry sync emits an administrative audit event (SR-023 AC-4).
- Integration (`backend/tests/modules/test_discovery_startup.py`): app lifespan runs discovery and the DICOM viewer module (TASK-073, installed as a package) appears in `GET /modules` with `module_key == "dicom-viewer"` (SR-016 AC-4) — no edit to core code required to surface it (SR-016 AC-1).

## Acceptance criteria

- [ ] Modules are discovered via `medhub.modules` Python entry points (ADR-0005).
- [ ] Each module's `ModuleManifest` is loaded and validated against the §12.1 contract (SR-016 AC-3).
- [ ] The installed set is persisted to `ModuleRegistry`; sync is idempotent (SR-016).
- [ ] Adding a module requires only a new package + entry point — no edits to existing modules or core (SR-016 AC-1).
- [ ] A malformed or failing module is isolated and not registered; the host stays up (ADR-0005).
- [ ] Enablement (TASK-042) is pure data over the registry — no code change enables a module.

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit + integration tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (`GET /modules`)
- [ ] Audit events emitted for security-relevant actions (registry sync, SR-023 AC-4)
- [ ] Traceability matrix row updated (SR-016 → TASK-070 → tests)
- [ ] Security review N/A (no auth/session/authz code; module isolation covered by tests)
