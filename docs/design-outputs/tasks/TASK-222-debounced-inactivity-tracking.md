---
id: "TASK-222"
type: task
title: "Session deadline only from server responses, and the client timeout ends the session"
status: approved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-14"
links:
  - target: "SR-030"
    relation: implements
  - target: "SR-026"
    relation: implements
  - target: "RISK-005"
    relation: mitigates
  - target: "RISK-001"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-025"
    relation: relates_to
  - target: "PRB-087"
    relation: relates_to
  - target: "PRB-089"
    relation: relates_to
  - target: "ADD-019"
    relation: relates_to
  - target: "TS-001"
    relation: relates_to
  - target: "TS-018"
    relation: relates_to
  - target: "TASK-144"
    relation: relates_to
  - target: "TASK-221"
    relation: relates_to
tags: ["cr:CR-006", "frontend", "session", "control:design"]
---

# TASK-222 — Session deadline only from server responses, and the client timeout ends the session

- **Software item / units:** SI-FE-AUTH `U-FEA-IdleTimer` (`auth/useIdleTimer.ts`) and `U-FEA-IdleWarning`
  (`auth/SessionActivityProvider.tsx`) (ADD-019); SI-FE-APICLIENT `apiClient.logout` (unchanged).
- **PRBs:** PRB-087 (client re-arms on activity), PRB-089 (`major`: the timeout neither logs out nor clears the
  cache), PRB-025 (re-arm on every event; resolved by removing the listeners). **CR:** CR-006 D-33, change
  analysis causes 19 and 20. Cause 10 is superseded.
- **Depends on:** TASK-144 (provider, `useMe`), TASK-221 (committed `bce75e3`).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** S. Files: `frontend/src/auth/useIdleTimer.ts`, `useIdleTimer.test.ts`, `SessionActivityProvider.tsx`,
  `SessionActivityProvider.test.tsx`, maybe `RequireAuth.test.tsx`. Records: TS-001, TS-018, ADD-019, PRB-025,
  PRB-087, PRB-089, maybe SOUP-028.
- **The two fixes land in one commit.** Server-only re-arming without the PRB-089 fix makes a live server
  session after the client redirect the normal case (CR-006 D-33 analysis).

## Objective

- **PRB-087 (D-33, "Server responses only"):** the client deadline is set only from a server response:
  receipt time plus `sessionExpiresInSeconds` from `GET /me`, or plus `expiresInSeconds` from extend. Mouse,
  keyboard, click, touch and scroll events no longer re-arm or extend anything. To keep the session, the user
  makes a request that refreshes `me`, or presses Extend in the warning dialog (SR-030 AC 4, AC 8).
- **PRB-089 (D-33, "Major, in CR-006"):** when the client deadline passes, `handleExpired` ends the session:
  `apiClient.logout()` (best effort), `qc.clear()`, then one redirect to `/login?timeout=1` (SR-030 AC 1, AC 2,
  AC 5, AC 8).
- **PRB-025 and SR-026 AC 8:** the original goal, re-arming at most once per second, is moot because no
  activity tracking remains. With the listeners removed, input events do no session-timer work, so AC 8 is met
  with zero re-arms. The wording of AC 8 is left to the human (CR-006 P-20).

## Implementation detail

- `useIdleTimer`:
  - Remove `ACTIVITY_EVENTS`, the listener registration and its cleanup, and the activity-driven
    `resetDeadline`.
  - The hook schedules the warning and expiry timers from `deadlineOverride` only. With no deadline yet, it
    schedules nothing. A deadline in the past calls `onExpired` once.
  - Drop `timeoutSeconds` from the options if nothing else needs it. Fix the doc comment ("activity re-arms to
    this").
  - Keep the returned API only if a caller uses it.
- `SessionActivityProvider`:
  - The deadline stays "newest of the `me` response and the last extend response" (TASK-144). No other input.
  - `handleExpired`, in order:
    1. Hide the warning.
    2. Call `qc.clear()`, so no view can render cached data.
    3. Start `apiClient.logout()` without awaiting it. Catch and ignore its error, and never pass it to the
       `AuthError` handler, so no second redirect follows.
    4. Navigate to `/login?timeout=1` once.
  - Factor the shared part with `handleLogout` and the `AuthError` handler only if that stays simpler than
    three short handlers.
  - The cache is cleared and the navigation made in the same handler. Mounted `me` observers must not cause an
    extra session-check request or a second redirect (SR-030 AC 8).
- No backend change, no OpenAPI change.

## Tests (write first)

Vitest with fake timers, MSW for `/auth/logout` and `/me`.

- `useIdleTimer.test.ts`:
  - `activity events do not move the deadline` (PRB-087; SR-030 AC 8; SR-026 AC 8). Dispatch `mousemove`,
    `keydown`, `click`, `touchstart` and `scroll` at 10 minutes. The warning still fires at the reported time
    − 2 min and expiry at the reported time.
  - `no listeners registered` (PRB-025; SR-026 AC 8): `window.addEventListener` is not called for any of those
    events.
  - `a new deadline re-arms` (SR-030 AC 8): a later `deadlineOverride` reschedules both timers.
  - The existing past-deadline and no-deadline cases are kept.
- `SessionActivityProvider.test.tsx`:
  - `reading without requests is warned at 13 min and signed out at 15 min` (SR-030 AC 1, AC 4): DOCTOR,
    15 min reported, mouse activity only.
  - `Extend re-arms from expiresInSeconds` (SR-030 AC 4, AC 8): the warning is dismissed, and the new deadline
    is the receipt time plus the reported value.
  - `a refreshed me re-arms` (SR-030 AC 8): the `me` query is invalidated and refetched at 10 min with 15 min
    reported. The warning moves to 23 min.
  - `timeout logs out, clears the cache and redirects once` (PRB-089; SR-030 AC 1, AC 5, AC 8): at expiry
    `POST /auth/logout` is called once, `qc.getQueryCache().getAll()` is empty, `/login?timeout=1` is visited
    once, and no `GET /me` follows the expiry.
  - `timeout still clears and redirects when logout fails` (PRB-089, cause 20): run with logout answering 401
    and with a network error. Same assertions, and the `AuthError` handler is not invoked.
  - `Back after a timeout shows no clinical data` (PRB-089; RISK-001): render a route with a clinical query
    seeded in the cache, expire, then `navigate(-1)`. The seeded text is absent, and `RequireAuth` renders
    nothing until `me` answers.
- System level (TS-001, new case): after a client timeout the session cookie is refused (`GET /me` → 401).
  If the system-level run is not available in this task, record it as pending in TS-001.

## Negative controls (QA mutants; each must fail at least one test above)

- Re-add one activity listener that calls `resetDeadline` → `activity events do not move the deadline` fails.
- Remove `qc.clear()` from `handleExpired` → the empty-cache and Back tests fail.
- Remove the `apiClient.logout()` call → the logout-count assertion fails.
- Await logout and redirect only on success → the logout-fails test fails.
- Route the logout error to the `AuthError` handler → the logout-fails test sees two redirects.
- Clear the cache after the navigation, with the provider unmounted → the Back test fails, if the order
  matters there. If it does not, say so in the TS-001 note.

## Records to update

- **TS-001** (approved, so the edit rule applies: bump, `in_review`, approval record removed, change-log line).
  - TC-001.5 and TC-001.11: replace the PRB-087 limitation with the server-only deadline and the timeout
    session end.
  - Add the system-level case.
- **TS-018** (approved, same rule). The pending AC 8 row (TASK-222) becomes a TC for "no activity listener, no
  timer work". Reword it if the human retires or rewords SR-026 AC 8 (P-20).
- **ADD-019** (`in_review`): `U-FEA-IdleTimer` changes from "planned: re-arms at most once per second" to
  "deadline only from server responses; no activity listeners". The PRB-087 known limitation is removed, and
  the timeout's session end is added. Bump the version.
- **PRB-025, PRB-087, PRB-089:** Resolution sections and `resolved`, after QA. CR-006 already holds the
  `resolves` links.
- **SOUP-028:** check whether its functional requirements name `QueryClient.clear()`. If not, add it under the
  edit rule.
- **arc42:** check `docs/design/` (crosscutting session concept) for "activity re-arms" wording. The Document
  Writer updates it if present.

## Acceptance criteria

- [x] SR-030 AC 8: the deadline comes only from `me` and extend responses. Activity events do not move it.
- [x] SR-030 AC 4: the warning appears at the reported time − 2 min. Extend re-arms from the server's value.
- [x] SR-030 AC 1, AC 2, AC 5: at the client timeout the server session is logged out (best effort) and the
      cache is cleared. Back shows no cached clinical data (PRB-089).
- [x] SR-026 AC 8: input events do no session-timer work (no listeners).

## Definition of Done

- [x] Frontend lint, type check and build clean; suite green; every negative control fails a test.
- [x] TS-001, TS-018 and ADD-019 updated as above; PRB-025, PRB-087 and PRB-089 Resolutions written.
- [x] `traceability-check` shows no error for this record, CR-006, the PRBs, RISK-001, RISK-005 and SR-030.

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) for PRB-025.
- 1.1 (2026-11-14) — Reworked for CR-006 D-33 (Software Architect). PRB-087: deadline only from server
  responses. PRB-089: the timeout logs out and clears the cache. The debounce is superseded by removing the
  activity listeners, which still resolves PRB-025. Retitled (was "Inactivity tracking re-arms its timers at
  most once per second"). Links added: `mitigates` RISK-001; `relates_to` PRB-087, PRB-089, TS-001, TS-018,
  TASK-221. Size XS → S. Still `draft`.
- 1.2 (2026-11-14) — Implemented (Software Developer); `draft -> in_review` for QA. See "Implementation record".
- 1.2 (2026-11-14) — QA review round 1: CHANGES REQUESTED, `in_review` to `draft` (findings in "QA review round 1").

## Implementation record

- **Code:** `frontend/src/auth/useIdleTimer.ts` (listeners, `resetDeadline`, `timeoutSeconds` and the returned
  API removed; timers armed only from `deadlineOverride`), `SessionActivityProvider.tsx` (`handleExpired`).
  Tests: `useIdleTimer.test.ts` (rewritten, 7 tests), `SessionActivityProvider.test.tsx` (8 new tests).
- **Deviation 1 (order of the cache clear).** `handleExpired` does not call `qc.clear()` itself. Clearing while
  the `me` observers are mounted makes them recreate the query and send a second `GET /me` after the redirect
  (observed: `GET /me` count 2, one `me` query back in the cache), which breaks SR-030 AC 8. The provider's
  unmount cleanup clears the cache when the redirect removes the signed-in tree (`sessionEnded` ref). The
  logout call and the single redirect are in the handler as planned. The "clear after the navigation" mutant of
  the task is not separable: the clear is already after the navigation. The mutant that clears in the handler
  (before the unmount) fails 4 tests.
- **Note.** `RequireAuth.test.tsx` is unchanged: the Back test lives in `SessionActivityProvider.test.tsx`.
- **Negative controls (all run, each fails tests):** activity listener that re-arms (3 fail), no clear (5), no
  logout call (3), await logout and redirect on success (3), logout error routed to the `AuthError` handler (4),
  clear in the handler with observers mounted (4).
- **Finding outside the task:** PRB-090 (the idle dialog's own redirects do not clear the cache).
- **Pending:** TS-001 TC-001.14 (system level), not run.

## QA review round 1 (qa-engineer, 2026-11-14) — CHANGES REQUESTED

Typecheck, lint and build are clean. Frontend: 361 passed. Backend: 1708 passed, 10 skipped. Trace over the 13 records: 156 records, 0 errors.
QA negative controls, each restored and checked with `cmp`:
- An activity listener that re-arms the timers: 3 tests fail.
- No cache clear on unmount: 5 tests fail.

1. **HIGH: the warning dialog's countdown redirect can win the race against `handleExpired`. The session is then neither logged out nor cleared (AC 3; PRB-089 recurs).**
   - `IdleWarningDialog.tsx:41-50` navigates to `/login?timeout=1` as soon as one of its 500 ms ticks sees the deadline has passed.
   - After a wall-clock jump (laptop sleep, or a suspended tab), the overdue interval tick is due before the expiry timeout. It runs first, the redirect unmounts the provider, and `clearTimers` cancels `handleExpired`. `sessionEnded` stays false, so nothing is cleared.
   - QA probe: warning open at 13 min, `vi.setSystemTime(+5 min)`, then advance 600 ms. Result: `POST /auth/logout` count 0, the seeded clinical text still in the cache, one redirect.
   - The dialog is always open at the timeout, so the outcome depends on timer order every time.
   - Fix (small; QA tried it and then reverted):
     - Give the dialog an `onExpired` prop.
     - Replace both of its `navigate("/login?timeout=1")` calls with `onExpired()`, and drop its `useNavigate`.
     - Pass `onExpired={handleExpired}` from the provider.
     - Make `handleExpired` idempotent: `if (sessionEnded.current) return;` at the top.
   - With that change, the probe gives logout 1 and an empty cache. The extend-401 path gives logout 1, an empty cache and no PHI on Back. All other auth tests pass.
   - `IdleWarningDialog.test.tsx` "extend 401 redirects to login" must then assert that `onExpired` is called.
   - Add a provider test for the clock jump (the probe above) and one for extend 401 followed by Back. List both in TC-001.13.
   - This resolves PRB-090 as well, so it should come into CR-006 and this TASK (human decision; CR-006 `resolves` link).
2. **MEDIUM: four records say `in_review` in their history but carry an `approved` status and an approval record dated 2026-11-14.** They are TS-001 1.7, TS-018 1.4, ADD-019 1.3 and SOUP-028 1.3.
   - For example, the TS-001 1.7 history line says "`in_review`, no approval record on the file", but the frontmatter has `status: approved`, `approved_by` and `approved_digest`. TS-018 was also re-serialized (quotes and the tag list).
   - If these are the human's MedTrace approvals, they were given before QA. TS-001 and TS-018 are test records, which QA approves. They also approve content that finding 1 will change.
   - Fix: the coordinator confirms where the approvals came from. After the finding-1 changes, TS-001 goes back to `in_review` under the edit rule.
3. **LOW: the `AuthError` handler (`SessionActivityProvider.tsx:57-65`) and `handleLogout` call `qc.clear()` while observers are still mounted.**
   - QA probe: after a mutation `AuthError`, the mounted clinical query was recreated empty in the cache. No extra `GET /me` was observed, and no data was restored.
   - So there is no PHI exposure: the recreated queries are empty and the session has already ended. At most there are wasted requests that get 401.
   - Fix (optional): use the same clear-on-unmount through `sessionEnded`, or record it as known.

Checked and acceptable:
- **Deviation 1 (clear in the unmount cleanup).** `/login` is a sibling of the signed-in tree (`App.tsx:68` against `:70-83`). Every redirect therefore unmounts the provider, and the clear runs in the same commit's passive cleanup. Nothing between the navigate and the unmount reads the clinical cache, and Back can only happen after the unmount. "Back after a timeout shows no clinical data" fails without the clear.
- **The deadline comes only from server responses.** `useIdleTimer` has no listeners, and the `useIdleTimer` tests pin this (SR-030 AC 8; SR-026 AC 8 has zero re-arms).
- **PRB-090** is well formed and its extend-401 claim is confirmed: a QA probe showed the PHI rendered on Back while `me` was pending. Its view of the countdown case ("if the interval ever fires before the deadline timer") understates it: the clock-jump probe shows it does.
- 1.3 (2026-11-14) — QA round 1 findings addressed (Software Developer); `draft -> in_review`. See "Round 2 record".
- 1.3 (2026-11-14) — QA review round 2: APPROVED, `in_review` to `approved`; checkboxes ticked (see "QA review round 2").

## Round 2 record (Software Developer, 2026-11-14)

- **HIGH 1 / PRB-090 (in CR-006 and this TASK by human decision).** `IdleWarningDialog` has an `onExpired` prop and no
  `useNavigate`; its countdown and the extend-401 call it. The provider passes `onExpired={handleExpired}`, which now
  returns at once when `sessionEnded.current` is set. New tests: `clock jump with the warning open: one logout, an
  empty cache and one redirect`, `the dialog's tick and the expiry timer firing in one pass log out once`, `extend 401
  then Back shows no clinical data`; dialog tests `extend 401 reports the ended session through onExpired` (was
  "redirects to login") and `the countdown reaching zero reports the ended session through onExpired once`.
- **LOW 3.** The mutation `AuthError` handler and `handleLogout` set `sessionEnded` and leave the clear to the unmount
  cleanup. New tests: `Log out now logs out once, clears the cache and does not ask the server again`; the existing
  AuthError test now has a mounted clinical observer and asserts an empty cache and one `GET /me`. Honest limit: putting
  `qc.clear()` back in either handler (before or after the navigation) fails no test; in jsdom the navigation unmounts
  the tree before the observers react, as QA's probe found (no extra request, no data restored). The change is for
  consistency with the timeout path, not covered by a failing mutant.
- **Negative controls (round 2):** the dialog navigating directly fails 4 tests; no idempotence guard fails 1
  (the one-pass test); the round-1 controls still fail their tests.
- **MEDIUM 2 (records).** The 1.7/1.4/1.3 approvals of TS-001, TS-018, ADD-019 and SOUP-028 are the human's MedTrace
  approvals of 2026-11-14. TS-001 (1.8) and ADD-019 (1.4) changed again, so they are back in `in_review` with the
  approval fields cleared and their history lines corrected. **TS-018 1.4 and SOUP-028 1.3 are left untouched** (content
  approved as is); their history lines still say "`in_review`, no approval record" / "still `in_review`", which is
  wrong: the 1.4 and 1.3 statuses are the human's approvals. Noted here instead of re-versioning them.

## QA review round 2 (qa-engineer, 2026-11-14) — APPROVED

Every round-1 finding is closed.

- **HIGH 1 (CR-006 D-34, PRB-090).** The dialog reports both of its endings through `onExpired`, and `handleExpired` is idempotent. QA re-ran the round-1 probes:
  - Clock jump with the warning open: logout 1, empty cache, one redirect, one `GET /me`.
  - Extend 401 then Back: logout 1, empty cache, no PHI on Back.
- **MEDIUM 2.** The human confirmed these are MedTrace approvals.
- **LOW 3.** The `AuthError` handler and `handleLogout` now leave the clear to unmount.
  - The developer's gap: putting `qc.clear()` back in those handlers fails no test. This is acceptable. That variant only recreates empty queries, which get 401 after the session has ended. It exposes no PHI and is not a risk control.
  - The control itself is pinned: dropping `sessionEnded` from either handler fails "a mutation's AuthError redirects once and clears the cache (the upload included)" or "Log out now logs out once, clears the cache and does not ask the server again".

Verification:
- Frontend: typecheck, lint and build are clean; 366 passed.
- Backend: 1708 passed, 10 skipped.
- Trace: 0 errors.

QA negative controls, each restored and checked with `cmp`:
- The dialog's countdown navigates by itself: 2 tests fail.
- `handleExpired` not idempotent: 1 test fails.
- Extend 401 does not call `onExpired`: 2 tests fail.
- `sessionEnded` removed from the `AuthError` handler and `handleLogout`: 2 tests fail.

Pending outside this TASK: TC-001.14 (system level).
