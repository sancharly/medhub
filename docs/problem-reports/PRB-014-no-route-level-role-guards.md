---
id: "PRB-014"
type: problem-report
title: "Frontend mounts every route for any authenticated user"
status: resolved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-07"
criticality: major
links: []
tags: ["security", "hazard:privacy"]
---

# PRB-014 — Frontend mounts every route for any authenticated user

## Observed

`frontend/src/app/App.tsx` mounts all routes for any authenticated user; only navigation links are role-filtered, so the backend 403 is the sole gate.

## Impact

Defense in depth for SR-005 and SR-009 is missing: a mistyped or shared URL renders an admin or clinical view shell to the wrong role before the API refuses.

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role). **Present as reported.**

- `frontend/src/app/App.tsx:36-57` mounts `/patients`, `/patients/:patientId/clinical-entries`,
  `/appointments`, `/consent`, `/admin/accounts` and `/admin/groups` for every authenticated
  user, behind `RequireAuth` only (`App.tsx:72`). No `RequireRole` exists in `frontend/src`.
- Role filtering exists only for navigation: `frontend/src/core/nav/navConfig.ts` (role list per
  path) and `useNavItems`. The clinical-entries route is not in `navConfig.ts` at all.
- The server refuses every such request (SR-031 AC 5, TS-002), so no data reaches a wrong role.
  The defect is that the view shell mounts and its queries fire.

CR-004 Q-4 (decided 2026-10-31): no client-side AC is added to SR-005; the fix is defence in
depth under SR-005, and the server-side tests stay the evidence of the control.

## Safety evaluation

Contributes to RISK-001 (unauthorized disclosure) — the data itself is still protected server-side, which is why this is a hardening defect rather than a live leak.

## Resolution

Implemented by TASK-142 (CR-004, awaiting QA): one role table
`frontend/src/core/nav/routeRoles.ts` drives both the navigation (`navConfig.ts`) and the new
`RequireRole` route wrapper (`frontend/src/app/RequireRole.tsx`). Every JSX `<Route>` in the
production sources under `frontend/src` (all of them are in `App.tsx`; this includes
`/patients/:patientId/clinical-entries`, absent from the nav) is wrapped by it, except the public
pages and the structural wildcards, which a test pins. A role not in a route's list is redirected
to `/profile` and the page is never mounted, so none of its queries fire; nothing mounts while `me`
loads or if it fails. `/appointments` is open to all four roles (SR-010 AC 4, SR-011 AC 3), so
administrative personnel keep that page and gain a nav entry. Verification: TS-002 TC-002.9
(`App.test.tsx`: a hard-coded route x role matrix as deep links; `RequireRole.test.tsx`;
`routeRoles.test.ts`: a compiler-API scan fails a `<Route>` without a literal path, a table entry
or the guard, and rejects `useRoutes`, `createBrowserRouter` and `createRoutesFromElements`).
Status stays `open` until CR-004 closes the problem (D-8).

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding L.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
- 1.2 (2026-11-02) — TASK-142: `## Resolution` written (route-level role guard). Status stays `open` (D-8).
- 1.3 (2026-11-06) — TASK-142 round 2: Resolution reworded (scan scope, `/appointments` for all roles). Status stays `open` (D-8).
- 1.4 (2026-11-07) — QA approved TASK-142 (R3-1 check, CR-004 D-15): status `resolved` (CR-004 D-8).
