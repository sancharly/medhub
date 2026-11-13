---
id: "TASK-144"
type: task
title: "One session query, client deadline from the server-reported session expiry"
status: draft
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-13"
links:
  - target: "SR-030"
    relation: implements
  - target: "RISK-005"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-016"
    relation: relates_to
  - target: "ADD-019"
    relation: relates_to
  - target: "ADD-006"
    relation: relates_to
  - target: "TS-001"
    relation: relates_to
  - target: "TASK-221"
    relation: relates_to
  - target: "TASK-088"
    relation: relates_to
  - target: "TASK-101"
    relation: relates_to
tags: ["phase:review-2026-07", "cr:CR-006", "frontend", "session", "control:design"]
---

# TASK-144 — One session query, client deadline from the server-reported session expiry

- **Software item / unit:** SI-FE-AUTH `auth/useMe.ts` (new), `SessionActivityProvider`, the ten `["me"]`
  readers (ADD-019); SI-AUTH session resolve and the `me` / extend schemas (ADD-006, additive fields).
- **PRB:** PRB-016. The module-list part of the 1.0 task (PRB-015) moves to TASK-221. **CR:** CR-006
  (change-analysis cause 9).
- **Depends on:** none (parallel). TASK-222, TASK-145 and TASK-146 follow it (shared files).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** M by risk, L by file count: two backend files (`backend/app/api/schemas/auth.py` or the `me`
  schema, `backend/app/api/routers/me.py` with `auth/session.py` exposing the remaining TTL), two generated
  files, `frontend/src/auth/useMe.ts` (new), `SessionActivityProvider.tsx`, and ten mechanical call-site
  replacements (`RequireAuth`, `RequireRole`, `ForcedPasswordGate`, `ChangePasswordPage`, `useLogin`,
  `ProfilePage`, `AccountsPage`, `AppointmentsPage`, `App`, `SessionActivityProvider`); tests; records
  TS-001, ADD-019, ADD-006. Kept as one task: the call sites must switch together for "one source" to hold.
- **Contract change (additive, "ask first" for the human at the plan gate):** `GET /me` gains
  `sessionExpiresInSeconds`; the session-extend response gains `expiresInSeconds` next to `expiresAt`.

## Objective

SR-030 AC 8: the client derives its inactivity deadline and the AC 4 countdown from the session expiry the
server reports, not from a client constant; an expired or invalid session gives one redirect to sign-in and no
repeated session checks. Today `SessionActivityProvider.tsx:18-20` seeds `Date.now() + 15 * 60 * 1000`, and
`["me"]` is read from ten files with different retry options (an expired session can take three retried 401s).
CR-006 A-5 assumed the server already reports the expiry: it does only on extend (`expires_at`,
`api/schemas/auth.py:49`); `GET /me` and login do not (finding P-5). Server enforcement of SR-030 AC 1 to AC 3
is unchanged.

## Implementation detail

- **Backend:** session resolution already computes the effective TTL (min of idle and absolute remaining);
  make it available to the `me` route and return it as an integer `sessionExpiresInSeconds` (relative, so the
  client clock does not matter; cause 9). Extend returns `expiresInSeconds` too. Regenerate
  `openapi.json` and `openapi.ts`; import aliases from `types.ts`.
- **Frontend:** `useMe()` = `useQuery({ queryKey: queryKeys.me, queryFn, retry: false, staleTime })`; on a
  401 the shared `AuthError` path clears the cache and redirects once (`/login?timeout=1`), with no refetch
  loop. `queryKeys.ts` holds the key. Every reader uses `useMe()`; a test fails if `["me"]` appears elsewhere.
- `SessionActivityProvider`: deadline = time the `me` / extend response was received + the reported seconds;
  re-derived on each `me` refetch and after extend; the role table is removed (no client constant).

## Tests (write first)

- `deadline follows the server-reported expiry, not 15 min` (SR-030 AC 8): mocked 30 min and 7 min values;
  warning appears 2 min before each (SR-030 AC 4), fake timers.
- `client clock skew does not move the deadline` (SR-030 AC 8, cause 9): `Date.now` shifted ±10 min between
  render and response.
- `expired session gives one redirect and no repeated me requests` (SR-030 AC 8): MSW 401 counter = 1.
- `only useMe reads the me query key` (static, SR-030 AC 8).
- Backend: `test_me_reports_remaining_session_seconds` for clinical and administrative roles (SR-030 AC 1, AC 2,
  AC 3 near the absolute limit).
- TS-001 (1.4 → 1.5, approval cleared): TC-001.10 client deadline from server expiry.

## Acceptance criteria

- [ ] SR-030 AC 8: deadline and countdown from the server value; one redirect, no repeated checks.
- [ ] SR-030 AC 4 warning timing holds for both role timeouts.
- [ ] Exactly one `useQuery` for `me`; OpenAPI and types regenerated and committed.

## Definition of Done

- [ ] Backend and frontend suites, lint, type checks green; `openapi-lint` drift check clean
- [ ] TS-001, ADD-019, ADD-006 consistent; `traceability-check` no error for this record

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect). Re-based on SR-030 AC 8 and AC 4; the module-list
  invalidation (PRB-015, SR-015 AC 5) moved to TASK-221, and `relates_to` SR-015 dropped; the server expiry is
  a new additive field (A-5 did not hold); `mitigates` RISK-005 added.
