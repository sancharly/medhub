# TASK-072 — RouterRegistry.mount + ModuleAccessGuard gating

- **Phase:** 5 — Module host + DICOM backend
- **Software item / unit:** SI-MODHOST / U-MH-RouterMount
- **Implements:** SR-016 (AC-2 enabled module presented to authorized users, mounted under module path), SR-015 (AC-3/AC-4 access only when enabled)
- **Depends on:** TASK-071 (PlatformServices), TASK-043 (ModuleAccessGuard) — must be merged first
- **Branch:** `feature/router-mount`
- **Status:** Not started

## Objective

Mount each discovered module's `APIRouter` under `/api/v1/modules/{module_key}` via the `RouterRegistry` passed to `manifest.register(...)`, and ensure every mounted module endpoint is gated by `ModuleAccessGuard` (enablement) **before** the per-endpoint `AuthorizationService` (consent) runs. This realizes the module-presentation and access-boundary requirements: a module endpoint is reachable only when enabled for one of the caller's groups. Traces to SR-016 AC-2 and SR-015 AC-3/AC-4.

## Interfaces to honor

Implements `RouterRegistry` from [12-interfaces.md](../../design/12-interfaces.md) §12.1 **verbatim**:

```python
class RouterRegistry:
    def mount(self, module_key: str, router: APIRouter) -> None: ...   # under /api/v1/modules/{key}
```

- Each module's `register(registry, services)` (TASK-070 manifest) calls `registry.mount(module_key, router)`; the host mounts it at `/api/v1/modules/{module_key}` ([api-design.md](../../specifications/api-design.md), ADR-0005).
- Every mounted route is wrapped with the `require_module_enabled(module_key)` dependency (TASK-043) so `ModuleAccessGuard.is_module_enabled(account_id, module_key)` runs first; per [api-design.md](../../specifications/api-design.md) flow step 3 / runtime view 6.4, enablement is checked **before** authorization. The module's own routes still pass `AuthorizationService` for the underlying PHI (via PlatformServices, TASK-071).
- The registry must not let a module mount outside its `/api/v1/modules/{module_key}` prefix (boundary enforcement, SR-016 AC-3) — it owns the prefix, the module supplies only the sub-paths.

## Implementation detail

- Files to create / modify:
  - `backend/app/modules/router_registry.py` — `RouterRegistry` implementation holding the FastAPI app/parent router; `mount(module_key, router)` includes the router with `prefix=f"/api/v1/modules/{module_key}"` and attaches `dependencies=[Depends(require_module_enabled(module_key))]` to the whole subtree (gating every route uniformly).
  - `backend/app/modules/host.py` — `register_all_modules(app, manifests, platform_services)`: for each discovered manifest (TASK-070), build a `RouterRegistry` bound to `module_key`, call `manifest.register(registry, platform_services)`.
  - `backend/app/main.py` — lifespan: after discovery (TASK-070), call `register_all_modules` (surgical).
- Mount path: `/api/v1/modules/{module_key}/...` exactly (ADR-0005, api-design). The DICOM endpoint (TASK-073) lands at `/api/v1/modules/dicom-viewer/studies/{attachmentId}`.
- The enablement gate produces, on a disabled module, `403 /errors/forbidden` + the denied-module-access audit event (the dependency wrapper from TASK-043). The route handler is never entered when disabled (SR-015 AC-3/AC-4).
- Audit: denied module access is audited by the guard dependency (TASK-043); mounting itself is a startup concern (covered by TASK-070 sync audit).
- Error cases (RFC 7807): module not enabled for any of the caller's groups → `403 /errors/forbidden`; unauthenticated → `401 /errors/unauthenticated`; a module attempting to mount a duplicate `module_key` or outside its prefix → host rejects at registration (logged, module skipped — ADR-0005 isolation).
- Edge cases: enabling/disabling at runtime (TASK-042) changes reachability immediately because the guard reads live enablement per request (SR-015 AC-4) — no app restart, no remount. `GET /me/modules` (the nav source) and the mounted-route gate read the **same** enablement, so what the UI shows matches what the API allows (SR-016 AC-2).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/modules/test_router_mount.py`):
  - `mount("dicom-viewer", router)` exposes the module's routes under `/api/v1/modules/dicom-viewer/...` (SR-016 AC-2, ADR-0005 path).
  - every mounted route carries the `require_module_enabled` dependency (gating is uniform, no route escapes the guard).
  - a module attempting to mount outside its prefix or a duplicate key is rejected/skipped (boundary, ADR-0005).
- Integration (`backend/tests/modules/test_module_gating.py`):
  - module **enabled** for the caller's group → request reaches the handler and proceeds to `AuthorizationService` (SR-015 AC-3).
  - module **not enabled** → `403 /errors/forbidden`, handler never entered, denied access audited (SR-015 AC-3, SR-023).
  - disable the module (TASK-042) → the next request is `403` without restart (SR-015 AC-4, live read).
  - the enablement seen by `GET /me/modules` matches the gate (UI/API consistency, SR-016 AC-2).

## Acceptance criteria

- [ ] Each module's router is mounted under `/api/v1/modules/{module_key}` via `RouterRegistry.mount` (SR-016 AC-2, ADR-0005).
- [ ] Every mounted route is gated by `ModuleAccessGuard` (enablement) before authorization (SR-015 AC-3, runtime view 6.4).
- [ ] A request to a module not enabled for any of the caller's groups returns 403 and never enters the handler (SR-015 AC-3/AC-4).
- [ ] Disabling a module at runtime blocks access on the next request without restart (SR-015 AC-4).
- [ ] A module cannot mount outside its prefix or duplicate a key (boundary, SR-016 AC-3).
- [ ] Denied module access is audited (SR-023).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit + integration tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (module routes appear under the module prefix)
- [ ] Audit events emitted for security-relevant actions (denied module access, SR-023)
- [ ] Traceability matrix row updated (SR-016 AC-2, SR-015 → TASK-072 → tests)
- [ ] Security review completed (module access gating / authorization ordering — SR-031.6)
