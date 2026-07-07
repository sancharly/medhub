---
id: "TASK-145"
type: task
title: "Route-based code splitting"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-026"
    relation: implements
  - target: "NFR-008"
    relation: relates_to
  - target: "TASK-112"
    relation: relates_to
  - target: "TASK-100"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:low"]
---

- **Phase:** Review 2026-07 — performance
- **Implements:** SR-026 (performance budgets)
- **Depends on:** should land **before** TASK-112 (performance validation) runs
- **Branch:** `perf/route-code-splitting`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — finding S (Low)

## Objective

All pages are statically imported in `frontend/src/app/App.tsx` — zero `React.lazy`/dynamic imports
in the app. Every user downloads admin pages, clinical views, and (once TASK-102 lands)
Cornerstone3D machinery in one bundle. Initial-load budget (SR-026) will not survive the DICOM
module without splitting; TASK-100's lazy module chunks presuppose this pattern exists.

## Implementation detail

- Wrap route page components in `React.lazy(() => import(...))` + a `<Suspense>` fallback inside
  `AuthenticatedApp`; keep auth gates (`RequireAuth`, `ForcedPasswordGate`) eager.
- Group admin pages into their own chunk; DICOM viewer must be its own chunk (aligns with TASK-100
  module lazy-loading).
- Record before/after gzipped bundle sizes in the PR (`vite build` output).

## Acceptance criteria

- [ ] `vite build` emits separate chunks per route group; entry chunk shrinks measurably (report
  numbers).
- [ ] Navigation between routes shows the Suspense fallback at most briefly; no functional
  regressions in existing page tests.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Existing Vitest suite green (lazy wrappers mocked or awaited)
- [ ] Traceability row updated (SR-026 → TASK-145)
