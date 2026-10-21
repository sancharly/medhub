---
id: "TASK-144"
type: task
title: "Shared useMe() hook, session TTL reconciliation, module-cache invalidation"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-030"
    relation: implements
  - target: "SR-015"
    relation: relates_to
  - target: "TASK-088"
    relation: relates_to
  - target: "TASK-101"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium"]
---

- **Phase:** Review 2026-07 — frontend
- **Implements:** SR-030 (session management, client tier)
- **Depends on:** —
- **Branch:** `fix/me-session-state`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — findings P + R (Medium)

## Objective

Three related client-state defects:

1. The `["me"]` query is issued from **9 files** (App, RequireAuth, ForcedPasswordGate,
   SessionActivityProvider, useLogin, ChangePasswordPage, ProfilePage, AppointmentsPage,
   AccountsPage) with inconsistent options — `RequireAuth` sets `retry:false`, the rest inherit the
   3-retry default, so an expired session can take 3 retried 401s before redirect.
2. `SessionActivityProvider.tsx` seeds `expiresAt` with a hard-coded 15-minute default not
   reconciled with the server session TTL — the idle countdown can disagree with actual server
   expiry (warns too late or too early per role).
3. `["myModules"]` (`core/clinical/AttachmentItem.tsx:19`) is never invalidated after admin
   group/module changes — DICOM "open in viewer" gating stays stale until hard reload (SR-015).

## Implementation detail

- Add `auth/useMe.ts` wrapping `useQuery({queryKey:["me"], retry:false, staleTime:...})`; replace
  all 9 call sites.
- Have the session-establishing responses (`login`, `extendSession`, or `GET /me`) expose the
  server-side session deadline; seed/refresh `expiresAt` from it instead of the constant. Fall back
  to role timeout table only when absent.
- Invalidate `["myModules"]` on group/module admin mutations, and set a modest `staleTime` +
  `refetchOnWindowFocus` for it; move the key into a shared `queryKeys.ts` to prevent stringly
  drift.

## Acceptance criteria

- [ ] Exactly one `useQuery(["me"])` definition in the codebase; expired session redirects after a
  single 401.
- [ ] Idle warning fires relative to the server-reported expiry (test with mocked TTL ≠ 15 min).
- [ ] After an admin disables the DICOM module, the attachment viewer link disappears on next
  focus/refetch without full reload.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Vitest coverage: useMe retry behavior, SessionActivityProvider TTL seeding, myModules
  invalidation
- [ ] Traceability rows updated (SR-030/SR-015)
