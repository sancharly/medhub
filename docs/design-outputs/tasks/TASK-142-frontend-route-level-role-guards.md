---
id: "TASK-142"
type: task
title: "Frontend route-level role guards"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-005"
    relation: implements
  - target: "TASK-082"
    relation: relates_to
  - target: "TASK-101"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium"]
---

- **Phase:** Review 2026-07 — frontend
- **Implements:** SR-005 (RBAC enforcement — defense-in-depth, UI tier)
- **Depends on:** —
- **Branch:** `fix/route-role-guards`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — finding L (Medium)

## Objective

`AuthenticatedApp` (`frontend/src/app/App.tsx`) registers every route for every authenticated user;
only the **nav links** are role-filtered (`core/nav/navConfig.ts` + `useNavItems`). A PATIENT can
type `/admin/accounts` and the admin page mounts, fires its queries, and renders error states from
backend 403s. Backend authorization is authoritative (correct), but the UI tier should not mount
screens the role can never use — information-architecture leak and poor failure UX.

## Implementation detail

- Add a `RequireRole` route wrapper (sibling to `RequireAuth`) that checks `me.userType` against an
  allowed-roles prop and redirects to `/profile` otherwise.
- Drive allowed roles from the same `navConfig.ts` role→path table so nav filtering and route
  guarding cannot drift apart (single source of truth).
- Wrap `/admin/accounts`, `/admin/groups`, `/patients` (doctor-only roster) and any other
  role-scoped routes.

## Acceptance criteria

- [ ] Direct navigation to `/admin/accounts` as PATIENT/DOCTOR redirects to `/profile` without
  mounting the page or firing admin queries.
- [ ] SYSADMIN/ADMIN flows unchanged.
- [ ] Guard and nav filtering share one config; a route in nav but unguarded fails a unit test.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Vitest coverage for `RequireRole` (allowed, denied, undefined `me`)
- [ ] Traceability row updated (SR-005 → TASK-142 → tests)
