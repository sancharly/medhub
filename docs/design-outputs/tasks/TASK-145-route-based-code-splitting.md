---
id: "TASK-145"
type: task
title: "Route-level code splitting with a chunk-failure fallback and an initial-payload budget check"
status: approved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-14"
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
- TS-012 (1.1 → 1.2, approval cleared) TC-012.x chunk failure; TS-018 TC-018.10 budget (TC-018.8 was already used by TASK-220).

## Acceptance criteria

- [x] SR-026 AC 7: separate chunks per route group; the initial payload within the approved budget.
- [x] SR-027 AC 3: a failed chunk gives a clear message and a working retry.

## Definition of Done

- [x] `npm run lint`, `typecheck`, `test -- --run`, `build` and the budget check green
- [x] TS-012, TS-018, ADD-018 consistent; `traceability-check` no error for this record

## Implementation record (2026-11-14, software-developer)

Built: `frontend/src/core/error/lazyRoute.tsx` (`lazyRoute`, `ChunkLoadError`, `reloadFailedChunks`),
`RouteChunkBoundary.tsx`, `core/admin/index.ts` (one module, so the admin pages are one chunk), `AppLayout`
(Suspense with a "Loading page" progress indicator inside `RouteChunkBoundary`, reset on path change),
`App.tsx` (seven lazy pages; `/profile`, sign-in, activation and the gates eager), `vite.config.ts`
(`build.manifest`), `scripts/check-bundle-budget.mjs`, `package.json` (`check:budget`; `build` runs the check
after `vite build`).

| Chunk (after) | raw kB | gzip kB |
|---|---|---|
| index (entry, initial) | 503.97 | 159.93 |
| index (admin pages, shared) | 25.95 | 8.04 |
| index (consent) | 7.75 | 3.08 |
| StatusPill (shared by lazy pages) | 8.89 | 2.98 |
| ChangePasswordPage | 4.41 | 2.01 |
| index (patients / clinical / appointments, three chunks) | 3.19 + 2.33 + 0.95 | 1.38 + 1.16 + 0.57 |
| Divider, ListItem, listItemIconClasses, useConfirm (shared) | 3.59 + 3.59 + 0.17 + 0.19 | 1.23 + 1.35 + 0.16 + 0.17 |

Before: one chunk, 558.87 kB raw, 172.68 kB gzip. After: initial 159.93 kB gzip against the 165 kB budget
(SR-026 AC 7). Tests and negative controls: TS-012 TC-012.6, TS-018 TC-018.10. A failed chunk is wrapped in
`ChunkLoadError`; React caches a rejected `lazy` import, so Retry first rebuilds the failed lazy components
(`reloadFailedChunks`) and then re-renders. A browser may also cache a failed module fetch for the same URL
(Safari does); Retry then fails again and the message stays, and a page reload recovers.

## QA review (2026-11-14, round 1): APPROVED

Verified: typecheck and lint clean; frontend 386 passed (38 files); `npm run build` exit 0, initial JavaScript
159.93 kB gzip (503.97 kB raw) against 165 kB; backend 1708 passed, 10 skipped; trace 0 errors. Negative
controls rerun: `PatientListPage` statically imported in `App.tsx` fails `landing route does not import admin
pages or any other lazy page` and the three `App.lazy` tests; Retry without `reloadFailedChunks()` fails the two
retry tests. Probe (deleted): the client timeout with a lazy chunk pending and with a chunk failed gives one
logout, one `/login?timeout=1`, one `me` request and an empty cache.

Carried findings (not blocking):

- MEDIUM: `scripts/check-bundle-budget.mjs` (the step `npm run build` and the Docker build run) does not detect a
  page made eager. With `PatientListPage` statically imported (in `App.tsx`, or in `main.tsx` next to the lazy
  import) the build passes at 160.61 / 160.72 kB: Rollup merges the page into the entry, so no `isDynamicEntry`
  chunk enters the static graph and the lazy-in-graph branch never fires on real output. Only the Vitest
  production-build test catches it. Fix: move the expected lazy-group list into the script and fail when any of
  them is not its own dynamic-entry chunk outside the initial set; add the real-build negative control.
- MEDIUM: after a deployment removes the old chunks, nginx `try_files` serves `index.html` for the missing
  `/assets/*.js` and the import fails every time. Retry cannot recover, and the message gives no other action
  (the same applies to the Safari cached-failure case). Fix: when a retry fails again, show "The application may
  have been updated. Reload the page." with a Reload button (`window.location.reload()`); add a test.
- LOW: `RouteChunkBoundary.componentDidUpdate` retries automatically when the error is caught in the same
  commit as a path change, so navigating to a failing chunk imports it twice before the message shows. Fix:
  record the `resetKey` at failure (`componentDidCatch`) and reset only when the key differs from it; or document
  the extra attempt.
- LOW: `build.manifest` writes `dist/.vite/manifest.json`, which the frontend image copies and nginx serves (source
  module paths). Fix: delete `dist/.vite` after the check in the `build` script, or deny dot-paths in
  `frontend/nginx.conf`.
- LOW: `frontend/scripts/` is neither linted nor typechecked (`eslint src`). Fix: add `scripts` to the lint glob.

## QA round 1 fixes (2026-11-14, software-developer)

- MEDIUM 1: `check-bundle-budget.mjs` now holds `LAZY_GROUPS` and fails unless each is a dynamic-entry chunk
  outside the initial set and none of its source modules is inside an initial chunk. Rollup keeps a tiny
  re-export chunk for an eagerly imported page, so the manifest alone does not show it; `vite.config.ts` has a
  `chunk-modules` plugin that writes `.vite/chunk-modules.json` (modules per chunk) beside the manifest. Real-build
  negative control: `a lazy page imported eagerly fails the check` (160.4 kB, under budget, still fails).
- MEDIUM 2: after a failed retry `RouteChunkBoundary` shows "The application may have been updated. Reload the
  page." with a Reload button (`window.location.reload()`); test mocks `reload`.
- LOW 1: the boundary records the path at which the failure was caught (`getDerivedStateFromProps`) and resets
  only when the path differs; test counts the imports (one).
- LOW 2: `npm run build` runs the check with `--clean`, which removes `dist/.vite` after a pass (tested; absent
  after the build). `check:budget` alone does not clean.
- LOW 3: `npm run lint` covers `src scripts` (`.mjs` included); it reported one unused import, fixed.
- Result: initial 160.06 kB gzip (504.51 kB raw; +0.13 kB from the boundary text).

## QA review (2026-11-14, round 2): APPROVED

Verified from a clean `dist`: typecheck and lint (`src scripts`) clean; frontend 391 passed (38 files);
`npm run build` exit 0, initial JavaScript 160.06 kB gzip (504.51 kB raw), and `dist` holds only `assets/`,
`index.html` and `mockServiceWorker.js` (no `.vite`); backend 1708 passed, 10 skipped; trace 0 errors. The round 1
change to `core/error/index.ts` is intact (the other round 1 `core/error` files are untracked, so `git checkout`
could not touch them). Negative controls: `PatientListPage` imported statically in `App.tsx` (160.75 kB) and in
`main.tsx` next to the lazy import (160.86 kB) both fail `npm run build` with "not a lazy chunk of its own" and
leave `dist/.vite` in place. Probe on the full `App` (deleted): navigating to a failing chunk imports it once,
Retry imports it a second time and then offers Reload, and leaving and returning gives a fresh Retry. With the
`getDerivedStateFromProps` line removed, the probe sees two imports again. Retry with `retried` never set fails
`a retry that fails again offers a page reload`.

Carried findings (not blocking):

- LOW: `navigating to a failing route imports its chunk once` (`RouteChunkBoundary.test.tsx:101`) still passes
  with `getDerivedStateFromProps` returning `null`. The rerender commits the Suspense fallback at `/bad` before the
  rejection, so the error never meets the path change in one commit. The real router navigates in a transition,
  and there it does. Fix: drive the case through `App` with a `popstate` navigation (as in `App.lazy.test.tsx`), or
  wrap the rerender in `startTransition`.
- LOW: the `chunk-modules` plugin (`vite.config.ts`) makes module ids relative to `process.cwd()`. A build run from
  another directory (`vite build frontend` from the repository root) writes `frontend/src/...`, so the
  module-prefix branch of the check never matches. The manifest branch still caught both negative controls. Fix:
  make the ids relative to the resolved `config.root` (`configResolved`).
- LOW: the round 1 fixes note says the manifest alone does not show an eagerly imported page. In both negative
  controls the manifest has no `src/core/patients/index.ts` entry, so the manifest branch fails the build on its
  own; the module list is defence in depth. Reword when the record is next edited.

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect). Re-based on SR-026 AC 7 and SR-027 AC 3; Plan-stage
  bundle measurement recorded; chunk-failure boundary and a build-time budget check added; `implements` SR-027
  and SR-020 added; `relates_to` RISK-007 (cause 11; RISK-007 has no row for it yet, finding P-9).
- 1.2 (2026-11-14) — Implemented (Software Developer). Budget check wired into `npm run build`; TC-018.10 used for the budget case; record `in_review`.
- 1.2 (2026-11-14) — QA review round 1 (QA Engineer): `approved`; carried findings recorded above.
- 1.3 (2026-11-14) — QA round 1 findings fixed (Software Developer); record back to `in_review`.
- 1.3 (2026-11-14) — QA review round 2 (QA Engineer): `approved`; carried LOW findings recorded above.
