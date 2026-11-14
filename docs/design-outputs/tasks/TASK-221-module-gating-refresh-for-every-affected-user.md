---
id: "TASK-221"
type: task
title: "Module gating in the UI refreshes for every affected user within 60 seconds"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-14"
links:
  - target: "SR-015"
    relation: implements
  - target: "RISK-004"
    relation: mitigates
  - target: "SR-030"
    relation: implements
  - target: "RISK-005"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-015"
    relation: relates_to
  - target: "ADD-020"
    relation: relates_to
  - target: "ADD-021"
    relation: relates_to
  - target: "TS-005"
    relation: relates_to
  - target: "TASK-144"
    relation: relates_to
tags: ["cr:CR-006", "frontend", "modules", "control:design"]
---

# TASK-221 — Module gating in the UI refreshes for every affected user within 60 seconds

- **Software item / unit:** SI-FE-CORE `core/clinical/AttachmentItem.tsx` (ADD-020); SI-FE-MODREG module query
  (ADD-021).
- **PRB:** PRB-015 (split from TASK-144 1.0). **CR:** CR-006 (D-4; change-analysis cause 8).
- **Depends on:** TASK-144 (`queryKeys.ts`). TASK-146 adds the unit tests of `AttachmentItem`.
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** S (`frontend/src/modules/useMyModules.ts` (new) or the registry's existing hook,
  `frontend/src/core/clinical/AttachmentItem.tsx`, `frontend/src/api/queryKeys.ts`, admin group/module
  mutation hooks; tests; records TS-005).

## Objective

SR-015 AC 5 (D-4): a change of a module's enablement reaches the module-dependent UI of every affected user
without a reload, within 60 s or on the next navigation to the affected view, including users who did not make
the change. `["myModules"]` (`AttachmentItem.tsx:18-19`) is never invalidated or refetched. A failed refetch
keeps the last known value (RISK-004, cause 8); the server guard (SR-015 AC 3) stays the authority.

## Implementation detail

- `useMyModules()`: `queryKey: queryKeys.myModules`, `staleTime: 30_000`, `refetchInterval: 50_000`,
  `refetchOnWindowFocus: true`, `refetchOnMount: "always"` (next navigation), `retry: 1`; TanStack Query keeps
  the previous `data` on error (no `placeholderData` reset). Every module-dependent reader uses it.
- Admin group and module mutations also invalidate `queryKeys.myModules` (the administrator's own UI).

## Implementation notes (Software Developer, 2026-11-14)

- `frontend/src/modules/useMyModules.ts` (new) is the only caller of `apiClient.listMyModules()`; `queryKeys.myModules` is the only spelling of the key (both pinned by a static test). `AttachmentItem` uses the hook.
- Invalidation of `queryKeys.myModules` is added to `GroupModules` (toggle) and to `GroupMembers` (add and remove member), because a membership change alters the administrator's own effective modules as well. `CreateGroupForm` is unchanged: a new group has no modules.
- Round 2 adds a backend change (non-sliding session check for `GET /me/modules`, D-32) that leaves the OpenAPI schema unchanged (QA-verified: the exported schema is identical). No SOUP added: TanStack Query is SOUP-028 (1.2 lists the relied-on behaviours).
- Tests: `frontend/src/modules/useMyModules.test.tsx` (11 tests), TC-005.5 in TS-005 1.4; `backend/tests/auth/test_session_no_slide.py` (10 tests), TC-001.12 in TS-001 1.6.

## Tests (write first)

- `module disabled elsewhere disappears within 60 s` (SR-015 AC 5): fake timers, MSW returns the new list after
  the change; the viewer link is gone by 60 s.
- `remount (next navigation) refetches` (SR-015 AC 5).
- `failed refetch keeps the last known modules` (SR-015 AC 5; RISK-004).
- `admin mutation invalidates myModules` (SR-015 AC 5).
- TS-005 (version raised by TASK-220): TC-005.y module refresh.

## Acceptance criteria

- [x] SR-015 AC 5: refresh within 60 s or next navigation for a user who did not make the change.
- [x] A failed refetch never hides an enabled module.

## Definition of Done

- [x] Frontend lint, type check, suite green
- [x] TS-005, ADD-020/ADD-021 consistent; `traceability-check` no error for this record

## QA review round 1 (qa-engineer, 2026-11-14) — CHANGES REQUESTED

Typecheck, lint and build are clean. The suite is green: frontend 350 passed, backend 1698 passed and 10 skipped. Trace: 101 records, 0 errors.
The interval bound is tight: with `refetchInterval` set to 61 s, three tests fail. Removing the remove-member invalidation fails one test.
The changes requested are below.

1. **HIGH: the 60 s poll stops the server-side inactivity timeout (SR-030 AC 1 and AC 2; RISK-005).**
   - Every authenticated request slides the session TTL. `GET /me/modules` resolves the session through `get_current_user` and `get_session` (`backend/app/api/deps.py:71`), which calls `SessionService.resolve` (`backend/app/auth/session.py:168-205`).
   - `useMyModules.ts:17` sends that request every 60 s while the tab is visible, with no user activity. As long as a view with an attachment stays open, the server never sees inactivity.
   - The client timer still fires. But `handleExpired` (`frontend/src/auth/SessionActivityProvider.tsx:39-42`) only navigates to `/login?timeout=1`. It does not log out on the server and does not clear the cache.
   - Result on an unattended doctor's workstation: the client times out at 15 min, but the server session lives until 15 min after the last poll. Going Back, or to `/`, restores the clinical UI with no re-authentication.
   - This breaks three claims in the records: RISK-005 row "Opaque server-side sessions with … idle expiry", the row 82 statement "Server enforcement of SR-030 AC 1 to AC 3 is unchanged", and PRB-087's "the server control of RISK-005 still holds".
   - Fix, either:
     - (a) Preferred, because it keeps the server as the authority: `GET /me/modules` checks the session without refreshing its TTL, for example `resolve(..., slide=False)` through its own dependency.
     - (b) Poll only when there has been user activity since the last fetch, and make the client's expiry call `apiClient.logout()` and `qc.clear()`.
   - Add a test that polling does not extend the session. For (a), `remaining_seconds` does not grow after `GET /me/modules`.
   - Record the change analysis in RISK-005 (Software Architect role; it touches SR-030). Add the interval to RISK-004's "risks introduced by controls" (`RISK-004…md:107` mentions only focus and navigation).
2. **MEDIUM: the 60 s bound is exceeded by one round trip.**
   - TanStack Query 5.101.0 restarts the interval on every query update (`query-core/build/modern/queryObserver.js:220-223`, called from `onQueryUpdate`).
   - So the next request leaves 60 s after the previous response arrives. A change committed just after the server read for that response is shown after 60 s plus the network round trip plus server time, or more if a retry is needed (1 s delay).
   - SR-015 AC 5 says "no later than 60 seconds". The tests use MSW with zero latency, so they cannot see the overshoot.
   - Fix: set `refetchInterval` to about 50 s, with `staleTime` no larger, so the bound holds with a margin for the round trip and one retry. Add a test with an MSW `delay()` (for example 2 s) where the change lands right after the server read, and assert the link is gone 60 s after the change.
   - Update "every 60 s" in ADD-021, TS-005, PRB-015 and this TASK.
3. **MEDIUM: the component-level failed-refetch test can pass vacuously (TASK AC 2; RISK-004).**
   - `useMyModules.test.tsx:113-116` asserts as soon as the first failed request has been counted, while the 1 s retry is still pending.
   - QA mutant: `AttachmentItem.tsx:21` changed to `!isError && (…)`, which hides an enabled module on error. All 23 tests in `useMyModules.test.tsx` and `core/clinical` still passed.
   - Fix: wait for `client.getQueryState(queryKeys.myModules)?.status === "error"` with `vi.waitFor(…, { timeout: 4000 })` inside `act`, and check `calls === callsBefore + 2` before asserting the link.
   - QA ran this version: it passes on the real code and fails on the mutant.
4. **LOW: the add-member invalidation is untested.** `GroupMembers.tsx:37` is never exercised; only remove is tested. TC-005.5 claims both "member add or remove". Fix: add a test, or narrow TC-005.5.
5. **LOW: wrong SOUP ID in the implementation notes.** The notes say TanStack Query is SOUP-025. It is SOUP-028; SOUP-025 is React. Fix the note.
6. **LOW: SOUP-028 does not list the behaviours this control relies on (§5.3.3).**
   - SOUP-028 states "caching and invalidation" only. The RISK-004 control now also relies on these TanStack Query behaviours: interval refetch paused while the tab is hidden, focus refetch, `refetchOnMount: "always"`, and `data` kept on error.
   - Fix: extend SOUP-028's functional requirements by one line. It is a content change, so SOUP-028 goes back to review for the human's re-approval. Tests at the exact version already pin these behaviours, so this alone would not block.

Checked and acceptable:

- **Load:** each visible tab with an attachment mounted sends at most 1 request per minute. All readers share one key, and the poll pauses in hidden tabs. `GET /me/modules` costs a constant 3 queries (TC-005.4). At 20 clients (CR-006 D-3) that is about 0.33 requests per second, negligible against SR-026 AC 5.
- **Stale data on a failed refetch is acceptable.** "Open in viewer" points at the same attachment URL as "Download" (`AttachmentItem.tsx:26-31`), so a stale link discloses nothing. Module routes are gated on the server by `RouterRegistry.mount` (`backend/app/modules/router_registry.py:30-36`, `require_module_enabled`).
- **Server-side changes:** module availability depends only on group membership and group modules (`me.py:40-50`), not on consent. No group-delete endpoint exists. The poll covers any server-side change; the remaining issue is the bound in finding 2.
- **Records:** the edits to the approved records ADD-021 (1.2) and TS-005 (1.3) followed the approved-record rule: version raised, approval record removed, status `in_review`. PRB-015 is `resolved`, and CR-006 has a `resolves` link to it. PRB-088 is well formed: required fields, `criticality: minor`, a safety evaluation, the open decision left to the human, and correct line references (`auth.py:138`, `:155`).

## QA review round 2 (qa-engineer, 2026-11-14) — APPROVED

Every round-1 finding is closed.

- **HIGH 1 (D-32).** `resolve(..., slide=False)` returns early only after the missing-key check and the absolute-lifetime check. An ended session has no key, so it gives 401. Only the TTL and `last_seen_at` write is skipped.
  - `get_current_user_no_slide` shares `_active_account`, so the active-account re-check still runs.
  - CSRF does not apply to a GET.
  - Grep: `get_*_no_slide` and `slide=False` are used only by `me.py:50`.
  - The `test_no_blocking_in_async.py` stub gained only the `slide` keyword. It still sleeps 2 s on the `/me` route and the assertions are unchanged, so the test is not weakened.
- **MEDIUM 2.** The interval is 50 s and `staleTime` 30 s. Worst case: 50 s plus three round trips plus a 1 s retry, which is within 60 s for a round trip of up to 3 s. A latency test is added.
- **MEDIUM 3.** The `!isError &&` mutant now fails `failed refetch keeps the last known modules`.
- **LOW 4.** The add-member test is added; removing that invalidation fails it.
- **LOW 5.** The SOUP ID in the notes is fixed.
- **LOW 6.** SOUP-028 1.2 lists the relied-on behaviours.

Records:
- RISK-005 1.9 (new row "Background polls do not extend the session", corrected row 82) and RISK-004 1.6 match the code.
- QA corrected one stale note in this TASK: "No backend change". The OpenAPI schema is still unchanged.

Verification:
- Backend: 1708 passed, 10 skipped. Ruff check and mypy (strict) are clean.
- `ruff format --check`: 3 files would be reformatted, all pre-existing and untouched here (`tests/api/test_openapi_contract.py`, `tests/auth/test_session_service.py`, `tests/test_env_example.py`).
- The exported OpenAPI matches the committed `openapi.json`.
- Frontend: typecheck, lint and build are clean; 352 passed.
- Trace over the 12 records: 149 records scanned, 0 errors.

Negative controls, each restored and checked with `cmp`:
- `/me/modules` back on `get_current_user` (sliding): `test_polling_my_modules_does_not_extend_the_session` fails.
- Interval at 60 s: 4 tests fail.
- `slide=False` returning before the absolute-lifetime check: the 2 absolute-lifetime tests fail.
- The `isError` mutant: 1 test fails.
- Add-member invalidation removed: 1 test fails.

Not blocking: P-18 (`handleExpired` neither logs out nor clears the cache) stays with the human, as CR-006 D-32 records.

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) from the PRB-015 part of TASK-144 1.0.
- 1.0 (2026-11-14) — Implemented by the Software Developer; handed to QA, `draft` to `in_review` (no content change to the contract; implementation notes added).
- 1.0 (2026-11-14) — QA review round 1: CHANGES REQUESTED, `in_review` to `draft` (findings above).
- 1.0 (2026-11-14) — Round 2 (Software Developer), `draft` to `in_review`: HIGH 1 (option (a), chosen by the human): `SessionService.resolve(..., slide=False)`, `get_session_no_slide` and `get_current_user_no_slide` in `backend/app/api/deps.py`, used only by `GET /me/modules`; links `implements` SR-030 and `mitigates` RISK-005 added. MEDIUM 2: `refetchInterval` 50 s (`staleTime` 30 s), test with a 1 s MSW `delay()`. MEDIUM 3: the failed-refetch test waits for the final `error` and checks `calls === callsBefore + 2`; it fails on the `!isError &&` mutant. LOW 4: add-member test. LOW 5: SOUP-028 in the notes. LOW 6: SOUP-028 functional-requirements line. Backend tests: `backend/tests/auth/test_session_no_slide.py`. TS-001 TC-001.12, TS-005 1.4, ADD-006, ADD-021, SOUP-028 updated.
- 1.0 (2026-11-14) — QA review round 2: APPROVED, `approved`; checkboxes ticked; one stale implementation note corrected (backend change, test counts).
