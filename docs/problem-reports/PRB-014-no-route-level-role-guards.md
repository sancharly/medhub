---
id: "PRB-014"
type: problem-report
title: "Frontend mounts every route for any authenticated user"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-31"
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

Planned in CR-004: TASK-142 (route-level role guard driven by the same role table as the
navigation). Not yet fixed.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding L.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
