---
id: "TASK-101"
type: task
title: "Nav gating by `GET /me/modules`"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-015"
    relation: implements
  - target: "SR-016"
    relation: implements
  - target: "TASK-100"
    relation: relates_to
  - target: "TASK-067"
    relation: relates_to
tags: ["phase:8-frontend-module-system-dicom"]
---

- **Phase:** 8 — Frontend module system + DICOM viewer
- **Software item / unit:** SI-FE-MODREG / U-FEM-NavGate
- **Implements:** SR-015 (AC-3/4 user accesses a module only if enabled for one of their groups; disabling removes access), SR-016.2 (enabled module presented in nav); ADR-0005
- **Depends on:** TASK-100 (`ModuleRegistry` + `FrontendModule`), TASK-067 (`GET /me/modules` endpoint, SI-API) — must be merged first
- **Branch:** `feature/fe-nav-gating`
- **Status:** Not started

## Objective

Gate module navigation in the shell so a module's `navItem` and route render **only if** its `moduleKey` is in the set returned by `GET /me/modules` — the modules enabled for the current user's groups (SR-015, SR-016.2). This is the frontend enforcement of per-group module enablement (set in TASK-096) and the contract clause "shell renders nav only if `moduleKey ∈ GET /me/modules`" (§12.2). Client gating is **convenience**: the module byte endpoints still pass `ModuleAccessGuard` server-side (SR-015, runtime view 6.4), so hiding nav never substitutes for server enforcement (SR-031.5).

## Interfaces to honor

Consumes the `ModuleRegistry` (TASK-100), the typed `ApiClient`, and `ShellServices`:

```ts
apiClient.getMyModules();          // GET /me/modules -> string[] of enabled moduleKeys (SR-015, SR-016.2)
registry.list();                   // FrontendModule[] (TASK-100)
// shell renders navItem + route only for modules whose key is in the enabled set
```

- The shell renders `navItem` **iff** `module.moduleKey ∈ getMyModules()` (§12.2 contract, SR-016.2). When the set changes (e.g., admin disables a module), the gated nav and route disappear after the query refetches (SR-015.4).
- This is a UI gate only; it must **not** be relied on as an access control. The DICOM byte endpoint independently enforces enablement + authorization server-side (SR-015 + SR-005, runtime view 6.4). Deep-linking to a disabled module's route must also be blocked client-side (route guard) and will be denied server-side regardless.
- Cookie + CSRF via `ApiClient` (SR-031.3).

## Implementation detail

- Files to create / modify:
  - `frontend/src/app/shell/useEnabledModules.ts` — `useQuery(['me','modules'])` → `getMyModules()`; returns the enabled `moduleKey` set; reasonable stale time, invalidated on login and on admin module-enablement changes.
  - `frontend/src/app/shell/ModuleNav.tsx` — renders `registry.list().filter(m => enabled.has(m.moduleKey))` as nav items (SR-016.2); items hidden otherwise.
  - `frontend/src/app/shell/ModuleRouteGuard.tsx` — wraps each module route: if the module's key is not in the enabled set, render an access-denied/redirect surface instead of mounting the lazy component (blocks deep links, SR-015.3).
  - Wire `ModuleNav` and `ModuleRouteGuard` into the existing shell layout/router (TASK-081) — additive; no module code changes (SR-016.1).
- Libraries: React 18 (`Suspense` around the lazy module), TanStack Query, React Router, MUI nav primitives.
- Loading: while `/me/modules` is loading, module nav items are not shown (avoid flashing an item the user may not have). Error fetching modules → no module nav (fail-closed) + error toast (SR-027.3); core nav unaffected.
- Fail-closed default: if the enabled set is unknown, modules are **hidden**, never shown — consistent with deny-by-default (SR-005 spirit on the UI side).

## Tests (write first — TDD, CLAUDE.md §4)

- Component tests (Vitest + RTL + MSW), `frontend/src/app/shell/ModuleNav.test.tsx`:
  - `GET /me/modules` returns `['dicom-viewer']` and the registry has the DICOM module → its nav item is rendered (SR-016.2).
  - `GET /me/modules` returns `[]` → no module nav item rendered (SR-015.3).
  - the set changes from `['dicom-viewer']` to `[]` after refetch → the nav item disappears (SR-015.4).
  - error/loading from `/me/modules` → fail-closed: no module nav shown (deny-by-default UI).
- Route-guard test, `frontend/src/app/shell/ModuleRouteGuard.test.tsx`:
  - deep-linking to the DICOM route when `dicom-viewer ∉ enabled` → access-denied/redirect, lazy component **not** mounted (SR-015.3); when enabled → component mounts.
- Each test names the SR AC it verifies.

## Acceptance criteria

- [ ] A module's nav item renders only when its `moduleKey ∈ GET /me/modules` (SR-016.2, §12.2 contract).
- [ ] When a module is disabled for all of the user's groups, its nav item and route become inaccessible after refetch (SR-015.3/4).
- [ ] Deep-linking to a disabled module's route is blocked client-side and denied server-side (SR-015.3, SR-031.5).
- [ ] Gating is fail-closed (unknown set → hidden) and never substitutes for server-side enforcement (SR-005, runtime view 6.4).

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc`)
- [ ] Unit/component tests pass; coverage target met
- [ ] Traceability matrix row updated (SR-015, SR-016.2 → TASK-101 → tests)
