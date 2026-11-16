---
id: "TASK-144"
type: task
title: "One session query, client deadline from the server-reported session expiry"
status: approved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-14"
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
- A mutation's `AuthError` (the attachment upload, `uploadAttachment` through `request()`, included; TASK-143
  only raises it) goes through the same single path: cache cleared and one redirect to `/login?timeout=1`, with
  no per-component handling and no second redirect for concurrent failures.
- `SessionActivityProvider`: deadline = time the `me` / extend response was received + the reported seconds;
  re-derived on each `me` refetch and after extend; the role table is removed (no client constant).

## Tests (write first)

- `deadline follows the server-reported expiry, not 15 min` (SR-030 AC 8): mocked 30 min and 7 min values;
  warning appears 2 min before each (SR-030 AC 4), fake timers.
- `client clock skew does not move the deadline` (SR-030 AC 8, cause 9): `Date.now` shifted ±10 min between
  render and response.
- `expired session gives one redirect and no repeated me requests` (SR-030 AC 8): MSW 401 counter = 1.
- `only useMe reads the me query key` (static, SR-030 AC 8).
- `a mutation's AuthError redirects once` (SR-030 AC 8; RISK-005): an upload (`AttachmentUpload`) answered 401
  twice in a row gives one redirect to sign-in and clears the `me` cache.
- Backend: `test_me_reports_remaining_session_seconds` for clinical and administrative roles (SR-030 AC 1, AC 2,
  AC 3 near the absolute limit).
- TS-001 (1.4 → 1.5, approval cleared): TC-001.10 client deadline from server expiry.

## Acceptance criteria

- [x] SR-030 AC 8: deadline and countdown from the server value; one redirect, no repeated checks.
- [x] SR-030 AC 4 warning timing holds for both role timeouts.
- [x] Exactly one `useQuery` for `me`; OpenAPI and types regenerated and committed.

## Definition of Done

- [x] Backend and frontend suites, lint, type checks green; `openapi-lint` drift check clean
- [x] TS-001, ADD-019, ADD-006 consistent; `traceability-check` no error for this record

## QA review — round 1 (2026-11-14): CHANGES REQUESTED

What QA ran:
- Frontend: `npm run typecheck`, `npm run lint` and `npm run build` are green; `npm test -- --run` gives 34 files, 336 passed.
- Backend: `uv run pytest -q` gives 1696 passed, 10 skipped; `ruff check` and `mypy app` are clean. `ruff format --check` flags only
  the 3 known files; `tests/auth/test_session_service.py` was already flagged at HEAD.
- OpenAPI: the re-export is identical to `backend/openapi/openapi.json`, and `generate:types` adds nothing beyond the 7 lines in
  the working tree.
- Trace over TASK-144, TS-001, ADD-019, ADD-006, PRB-016, CR-006, SR-030 and RISK-005: 0 errors, 59 warnings (127 records).
  Negative control: removing `implements` SR-030 gives E8.
- QA ran its probes and mutants in temporary test files, then deleted them; edited files were restored byte-identical.

Findings:

- **R1-1 [HIGH] A mistyped current password now signs the user out.**
  - Cause: `POST /auth/password` answers a wrong current password with 401 `/errors/unauthenticated`
    (`backend/app/api/routers/auth.py:155`). `request()` turns that into `AuthError`, and `useChangePassword` is a mutation, so
    the new mutation-cache handler (`frontend/src/api/queryClient.ts:20-25`) clears the cache and redirects to
    `/login?timeout=1`.
  - QA probe (`SessionActivityProvider` around `ChangePasswordPage`, 401 "Current password is incorrect."): visited
    `/home` then `/login?timeout=1`. The user never sees the reason, and a forced password change becomes a sign-in loop.
  - Fix: the server should answer a wrong current password with a problem that is not a session failure, for example 400
    `validation-error` with `errors: [{field: "currentPassword", ...}]`, or 403 with its own type.
    - Update `extractChangePasswordError`, the OpenAPI document and the backend tests.
    - Add a frontend test: a wrong current password shows the message and does not redirect.
  - Also list the other non-session `UnauthenticatedError` uses (`identity/activation.py:69,80,83`,
    `identity/erasure.py:186`). Confirm that none is reached by a mutation while `SessionActivityProvider` is mounted.
- **R1-2 [MEDIUM] Nothing checks that the client session actually ends at the reported deadline.**
  - The tests check only when the warning appears.
  - Mutant: `meDeadline = Date.now() + reported * 1000` (computed at render, `SessionActivityProvider.tsx:27-28`). It passes
    all 85 `src/auth` and `src/app` tests, but it is a real defect: opening the warning re-renders the provider, the deadline
    moves 13 minutes later, and the client never expires.
  - QA's test kills it: 15 min reported → advance 13 min + 1 s → dialog shown → advance 2 min →
    `visited` contains `/login?timeout=1`. It passes on the real code and fails on the mutant.
  - Fix: add that test to `SessionActivityProvider.test.tsx` and to TC-001.11.
- **R1-3 [MEDIUM] New PRB needed: client activity and server sliding drift apart.**
  - The divergence: `useIdleTimer` re-arms the client deadline on every mouse, key or scroll event
    (`useIdleTimer.ts:54-60`, `now + reported`), but the server slides the session only on requests.
  - Effect: a user who moves the mouse without making requests for longer than the timeout gets no warning (SR-030 AC 4).
    Their next action is answered 401 and redirected. Near the absolute limit the re-arm also runs past the absolute end.
  - This predates the task (the old code re-armed to the 15-minute constant). It is not covered by PRB-017 (missing unit
    tests) or TASK-222 (re-arming at most once per second).
  - It does qualify this task's SR-030 AC 8 claim ("deadline from the server value") once activity occurs.
  - Fix: raise a PRB (minor; the server control of RISK-005 still holds). A human decides the design: re-arm only from
    server responses, or have activity make a throttled extend call (coordinate with TASK-222).
  - Until then, name the limitation in TC-001.11 and ADD-019.
- **R1-4 [LOW] What a reported 0 means.**
  - `sessionExpiresInSeconds` defaults to 0 (`backend/app/api/schemas/me.py:29`). The FastAPI output schema still makes it
    required, so the TypeScript type is `number`.
  - A 0 does not sign the user out at once. The deadline equals the receipt time, so `scheduleTimers` sets no timers
    (`expireIn <= 0`), and `resetDeadline` skips re-arming. The client timer just stops, and the next request's 401 ends the
    session.
  - An unauthenticated `me` is a 401 with no data, so no deadline is derived from it.
  - Fix: drop the default (the route always sets the field), and treat a deadline already in the past as expired (call
    `onExpired`). Add a test for it.
- **R1-5 [LOW] Records.** PRB-016's Resolution says "334 passed"; QA counted 336. Correct the count.

Judgment points:

- **`App.test.tsx` 4 → 1:** the change is intended. The plan sets `retry: false`, and SR-030 AC 8 asks for "no repeated
  session-check requests". No availability AC requires automatic retries. After a transient 500 the user now presses
  "Try again" (SR-027 AC 3), where before the client retried by itself. Acceptable.
- **RISK-005:** TASK-144 should not edit it. The control row covers TASK-143, TASK-144, TASK-222 and TASK-146, and RISK-005 is
  `approved`. Fill in the verification cell (TC-011.7, TC-001.11, TASK-146's cases) and re-score at TASK-226, the CR-006
  end-to-end check. Editing it now would reopen an approved record twice.
- **Approved-record edit rule:** followed. ADD-006 (1.4 → 1.5), ADD-019 (1.1 → 1.2) and TS-001 (1.4 → 1.5) have their approval
  records cleared and are `in_review`. PRB-016 is `resolved`, with CR-006 `resolves` PRB-016.

## QA review — round 2 (2026-11-14): APPROVED

What QA re-ran:
- Frontend: typecheck, lint and build are green; tests give 34 files, 340 passed.
- Backend: pytest gives 1698 passed, 10 skipped; `ruff check` and `mypy app` are clean. `ruff format --check` flags only the
  3 known files.
- OpenAPI: the re-export is identical, and `generate:types` leaves `openapi.ts` byte-identical. `sessionExpiresInSeconds`
  and `expiresInSeconds` are required, with no default.
- Trace over TASK-144, TS-001, ADD-019, ADD-006, PRB-016, PRB-087, CR-006, SR-025, SR-030 and RISK-005: 0 errors,
  64 warnings (134 records).

Mutants (each file restored byte-identical):
- Render-time deadline: fails the session-end test.
- Past-deadline branch removed in `useIdleTimer`: fails 2 tests.
- Route back to 401 for a wrong current password: fails both `TestChangePasswordWrongCurrentPassword` tests.

R1-1: the other non-session 401s are not reachable from a mounted `SessionActivityProvider`.
- `ActivationPage` is routed outside it (`App.tsx`).
- No frontend code calls the anonymized-data retrieval endpoint.

R1-3: PRB-087 is well formed (open, minor).

Audit and brute-force (judgment):
- The status change does not alter audit or security behaviour. At HEAD a wrong current password wrote no audit row either.
- SR-029's lockout covers login only, and SR-042 rate-limits only the retrieval endpoint. No SR requires a lockout or rate
  limit on `POST /auth/password`.
- The contract change is recorded in ADD-006 1.5 and TS-001 1.5.

Carried LOWs, not blocking:
- **L-1 (new PRB suggested).** A failed current-password check is neither audited nor attempt-limited. SR-023 AC 1
  ("authentication attempts (success and failure) are recorded") can be read as covering this re-authentication. This
  predates the task and the 401 to 400 change does not alter it. `test_wrong_current_password_changes_nothing_and_audits_nothing`
  fixes today's behaviour in place: update it when that PRB is decided.
- **L-2.** In the same test, `mock_svc.invalidate.assert_not_called()` cannot fail: the spec'd mock's
  `list_account_session_ids` iterates as empty, so `invalidate` is never reached even on success. Assert
  `mock_svc.list_account_session_ids.assert_not_called()` instead.

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect). Re-based on SR-030 AC 8 and AC 4; the module-list
  invalidation (PRB-015, SR-015 AC 5) moved to TASK-221, and `relates_to` SR-015 dropped; the server expiry is
  a new additive field (A-5 did not hold); `mitigates` RISK-005 added.
- 1.2 (2026-11-14) — TASK-143 QA round 1 (R1-2): explicit step and test that a mutation's `AuthError` (the upload included) redirects once; TASK-143 only raises `AuthError`.
- 1.3 (2026-11-14) — Implemented (Software Developer), handed to QA (`draft → in_review`). Deviations: the new TS-001 case is TC-001.11 (TC-001.10 already exists); the
  mutation redirect is a handler in the query client's mutation cache, registered by `SessionActivityProvider` (a 401 on the `me` query keeps its
  `RequireAuth` redirect, which preserves `next`); `useMe` has a 30-second stale time; `useLogin` resets the `me` query instead of seeding it with the
  login response (which carries no expiry), and `ChangePasswordPage` keeps the receipt time when it patches `me`; `useIdleTimer` takes
  `timeoutSeconds` (the last reported length) instead of minutes and `roleTimeouts` keeps only the 2-minute warning lead; `App.test.tsx` now expects
  one `/me` request on a 500 instead of four (no retries by design); the consent keys moved to `queryKeys.myConsents`. PRB-015 and SR-015 AC 5 are TASK-221's.
  Records touched: TS-001 1.5, ADD-019 1.2, ADD-006 1.5, PRB-016 resolved (approval records cleared on the three approved ones).
- 1.3 (2026-11-14) — QA review round 1: CHANGES REQUESTED (`in_review → draft`); findings R1-1 to R1-5 above.
- 1.4 (2026-11-14) — QA round 1 fixed, handed back (`draft → in_review`). R1-1: no SR or ADD requires 401 for a wrong current password (SR-025, SR-030 and
  ADD-006 checked), so the server answers 400 `validation-error` with an error on `currentPassword`; `extractChangePasswordError` already reads
  `errors[0]` and needed no change; tests: backend `TestChangePasswordWrongCurrentPassword` (also proves no password change, audit row, commit or
  session invalidation; the route has no lockout counter) and a frontend case showing the message with no redirect. The other `UnauthenticatedError`
  uses (`activation.py:69,80,83`, `erasure.py:186`) are on public routes (activation by token; erasure retrieval by code) that no mounted
  `SessionActivityProvider` page calls, so none can fire the handler. R1-2: session-end test added; the render-time mutant fails it. R1-3: PRB-087
  raised, not fixed. R1-4: `session_expires_in_seconds` has no default (the route builds `MeResponse` explicitly) and a deadline already in the past
  is expired (`useIdleTimer`). R1-5: PRB-016 counts corrected. OpenAPI regenerated: the field is now `required` in the document.
- 1.4 (2026-11-14) — QA review round 2: APPROVED (`in_review → approved`, status only).
