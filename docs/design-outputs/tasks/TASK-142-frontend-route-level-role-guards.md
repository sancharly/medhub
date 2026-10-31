---
id: "TASK-142"
type: task
title: "Frontend route-level role guards"
status: draft
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-10-31"
links:
  - target: "RISK-001"
    relation: mitigates
  - target: "SR-005"
    relation: implements
  - target: "SR-009"
    relation: implements
  - target: "PRB-014"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-018"
    relation: relates_to
  - target: "TASK-082"
    relation: relates_to
  - target: "TASK-101"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium", "control:protective", "cr:CR-004"]
---

# TASK-142 — Frontend route-level role guards

- **Software item / unit:** SI-FE-SHELL `U-FE-RouteGuard` (new, ADD-018); `frontend/src/app/App.tsx`,
  `frontend/src/core/nav/`.
- **Resolves (through CR-004):** PRB-014. Source: `docs/reports/CODE-REVIEW-2026-07.md` finding L.
- **Depends on:** none. Independent of every backend task; can run in parallel.
- **Branch:** `fix/review-2026-07-security` (CR-004).
- **Size:** M (`App.tsx`, `navConfig.ts`/`types.ts`, new `RequireRole.tsx`, 2 test files; TS-002)
- **Scope decision:** CR-004 Q-4 (2026-10-31): no new AC on SR-005. This is defence in depth
  under SR-005 and SR-009; the server-side tests stay the evidence of the control.

## Objective

A role never mounts a view it cannot use. Today `App.tsx:36-57` mounts every route behind
`RequireAuth` only, and role filtering exists only in navigation (`navConfig.ts`).

## Implementation detail

- One role table: extend `navConfig.ts` (or a sibling `routeRoles.ts` that `navConfig` derives
  from) so every role-scoped path, including `/patients/:patientId/clinical-entries` (not in the
  nav today), has its role list. Use the uppercase `UserType` constants (`CLAUDE.md`).
- `RequireRole` (sibling of `RequireAuth`): reads `me.userType`; if it is not in the route's
  role list, renders `<Navigate to="/profile" replace />` and does not mount the child. While
  `me` is loading, render nothing (no query of the child fires).
- Wrap every role-scoped route in `App.tsx` with it.

## Tests (write first)

- `frontend/src/app/RequireRole.test.tsx` (Vitest + Testing Library): allowed role renders the
  child; denied role redirects and the child's query hook is never called; `me` undefined or
  loading renders nothing; unknown role string is denied.
- `frontend/src/core/nav/routeRoles.test.ts`: every role-scoped `<Route>` in `App.tsx` is wrapped
  and its path is in the role table; a nav entry whose route is unguarded fails.
- Existing `useNavItems.test.ts` and `AppNavigation.test.tsx` pass.

## Acceptance criteria

- [ ] SR-005, SR-009 (defence in depth): PATIENT or DOCTOR at `/admin/accounts` is redirected to
      `/profile` without mounting the page or firing admin queries (`frontend/src/app/RequireRole.test.tsx`).
- [ ] ADMIN and SYSADMIN flows unchanged (existing frontend suite).
- [ ] Guard and navigation share one table; an unguarded role-scoped route fails a test
      (`frontend/src/core/nav/routeRoles.test.ts`).

## Verification

```sh
cd frontend && npx tsc --noEmit && npm run lint && npm test
```

Negative control: remove the wrapper from `/admin/accounts`; both new test files fail.

## Records

- **TS-002** → 1.2 (`in_review`; TASK-187 bumps it first if it lands first, then this task adds
  under that version): TC-002.9 (client route guard, defence in depth), `verifies` SR-005, SR-009.
- **ADD-018** 1.1: confirm the `U-FE-RouteGuard` unit text.
- **PRB-014**: `## Resolution`, `resolved`.

## Definition of Done

- [ ] `tsc`, lint and the frontend suite pass.
- [ ] TS-002 `in_review` with TC-002.9; PRB-014 `resolved`.
- [ ] `traceability-check` shows no error for TASK-142, TS-002, SR-005, SR-009, PRB-014.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-001 (risk register bootstrap, TASK-147).
  Traceability only: the requirement content is unchanged, so the existing approval stands.
- 1.2 (2026-10-21) — Tagged `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.3 (2026-10-31) — CR-004 Plan stage (Software Architect role): Q-4 recorded; clinical-entries
  route added to scope (absent from the nav table). Links `implements` SR-009, `relates_to` PRB-014,
  CR-004, ADD-018 added. Tests named by path, TS-002 TC-002.9 planned. Still `draft`.
