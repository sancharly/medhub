---
id: "PRB-020"
type: problem-report
title: "No route-level code splitting, so the bundle cannot absorb the DICOM viewer"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-14"
criticality: minor
links: []
tags: ["performance"]
---

# PRB-020 — No route-level code splitting, so the bundle cannot absorb the DICOM viewer

## Observed

`app/App.tsx` imports every route statically; there is no `React.lazy` anywhere, so the single bundle will have to carry Cornerstone3D once the viewer lands.

## Impact

SR-026 performance budgets and SR-020 responsiveness on slower devices are at risk once the viewer module exists.

## Safety evaluation

No hazard today; the viewer is not implemented yet.

## Investigation

`frontend/src/app/App.tsx` imported all eight pages statically, so `vite build` produced one `index-*.js` of 558.87 kB raw, 172.68 kB gzip (172.55 kB at Plan time), of which about 470 kB is libraries (MUI, react-dom, TanStack Query, react-router) and about 20 kB page code. No `lazy(` or `Suspense` existed in `frontend/src`.

## Resolution

TASK-145 (CR-006), verified in the working tree on 2026-11-14: every routed page except sign-in, activation and the landing route is a `lazyRoute` chunk (`frontend/src/app/App.tsx`; admin pages share one chunk, `frontend/src/core/admin/index.ts`) under one `Suspense` and a `RouteChunkBoundary` in `AppLayout`; a failed chunk shows a message with a Retry that imports it again (`frontend/src/core/error/lazyRoute.tsx`, `RouteChunkBoundary.tsx`; SR-027 AC 3). `frontend/scripts/check-bundle-budget.mjs`, run by `npm run build`, keeps the initial JavaScript within 165 kB gzip (SR-026 AC 7): it is now 159.93 kB gzip (503.97 kB raw). Verified by TS-012 TC-012.6 and TS-018 TC-018.10 (frontend suite 386 passed; build and budget check green; with static imports the budget test fails at 173.00 kB gzip). The DICOM viewer is not part of this change; when it lands it must be its own lazy chunk, which the check enforces.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding S.
