---
id: "TASK-145"
type: task
title: "Route-level code splitting with a chunk-failure fallback and an initial-payload budget check"
status: draft
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-13"
links:
  - target: "SR-026"
    relation: implements
  - target: "SR-027"
    relation: implements
  - target: "SR-020"
    relation: implements
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-020"
    relation: relates_to
  - target: "RISK-007"
    relation: relates_to
  - target: "ADD-018"
    relation: relates_to
  - target: "TS-012"
    relation: relates_to
  - target: "TASK-144"
    relation: relates_to
  - target: "NFR-008"
    relation: relates_to
  - target: "TASK-112"
    relation: relates_to
  - target: "TASK-100"
    relation: relates_to
tags: ["phase:review-2026-07", "cr:CR-006", "frontend", "performance"]
---

# TASK-145 — Route-level code splitting with a chunk-failure fallback and an initial-payload budget check

- **Software item / unit:** SI-FE-SHELL `app/App.tsx`, `core/error/AppErrorBoundary` (ADD-018).
- **PRB:** PRB-020. **CR:** CR-006 (D-8; change-analysis cause 11).
- **Depends on:** TASK-144 (both edit `App.tsx`; commit after it).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** S (`frontend/src/app/App.tsx`, `frontend/src/core/error/RouteChunkBoundary.tsx` (new),
  `frontend/scripts/check-bundle-budget.mjs` (new), `frontend/package.json` script; tests; records TS-012,
  TS-018).

## Objective

SR-026 AC 7: the initial JavaScript payload excludes the code of routes and modules the landing route does not
render; they load on first navigation. Measured at the Plan stage (2026-11-13, `npm run build`, vite 5.4.21):
one chunk `index-*.js` 559.07 kB minified / **172.55 kB gzip**; no `lazy(` anywhere. Source-map attribution of
that chunk: libraries ≈ 470 kB (MUI material 200.6, react-dom 126.9, TanStack query-core 37.5, react-router
36.6, MUI system 34.7), application route code ≈ 20 kB (admin 8.9, clinical 4.1, appointments 2.9, consent 1.9,
password 1.6, patients 0.8). The budget proposed for SR-026 AC 7 is in CR-006 finding P-2; the human writes it
into SR-026. SR-027 AC 3 and cause 11: a chunk that fails to load shows a clear message with a retry, never a
blank route.

## Implementation detail

- `React.lazy(() => import(...))` for every routed page except the sign-in, activation and the landing route
  (`/profile`) and the gates (`RequireAuth`, `ForcedPasswordGate`, `RequireRole`, `SessionActivityProvider`),
  which stay eager. Admin pages share one chunk.
- One `<Suspense>` inside `AppLayout` with an accessible progress indicator; a `RouteChunkBoundary` catches a
  failed dynamic import and shows "This page could not be loaded. Retry." with a retry that re-imports.
- `check-bundle-budget.mjs`: after `vite build`, reads the manifest (`build.manifest: true`), sums the gzip size of
  the entry chunk and its static imports, and fails if it exceeds the budget constant (the SR-026 AC 7 value once
  approved; until then the proposed value, flagged in the script).
- Record before/after sizes in this task and in TS-018.

## Tests (write first)

- `lazy route renders after its chunk loads` and `failed chunk shows the retry message, retry recovers`
  (SR-027 AC 3; SR-026 AC 7).
- `landing route does not import admin pages` (SR-026 AC 7): the budget script on the build output, and a
  manifest check that no lazy page is in the entry chunk's static import graph.
- Existing page tests green (lazy wrappers awaited).
- TS-012 (1.1 → 1.2, approval cleared) TC-012.x chunk failure; TS-018 TC-018.8 budget.

## Acceptance criteria

- [ ] SR-026 AC 7: separate chunks per route group; the initial payload within the approved budget.
- [ ] SR-027 AC 3: a failed chunk gives a clear message and a working retry.

## Definition of Done

- [ ] `npm run lint`, `typecheck`, `test -- --run`, `build` and the budget check green
- [ ] TS-012, TS-018, ADD-018 consistent; `traceability-check` no error for this record

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect). Re-based on SR-026 AC 7 and SR-027 AC 3; Plan-stage
  bundle measurement recorded; chunk-failure boundary and a build-time budget check added; `implements` SR-027
  and SR-020 added; `relates_to` RISK-007 (cause 11; RISK-007 has no row for it yet, finding P-9).
