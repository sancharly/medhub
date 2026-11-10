---
id: "TASK-205"
type: task
title: "Close the session refresh race, prune expired members from the cap, report evictions"
status: approved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-11-06"
updated: "2026-11-10"
links:
  - target: "SR-030"
    relation: implements
  - target: "RISK-005"
    relation: mitigates
  - target: "PRB-064"
    relation: relates_to
  - target: "PRB-065"
    relation: relates_to
  - target: "PRB-066"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-199"
    relation: relates_to
  - target: "ADD-006"
    relation: relates_to
  - target: "TS-001"
    relation: relates_to
tags: ["security", "auth", "session", "cr:CR-004", "control:design"]
---

# TASK-205 — Close the session refresh race, prune expired members from the cap, report evictions

- **Software item / unit:** SI-AUTH `U-AUTH-Session` and the login flow (ADD-006); SI-API
  `U-API-Routers`, `U-API-ErrorHandler` (ADD-005).
- **PRBs:** PRB-064 (major), PRB-065 (minor), PRB-066 (minor). **CR:** CR-004 (D-11).
- **Depends on:** TASK-199 (committed, f254277). No other dependency.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (5 hand-written source files, `frontend/src/auth/LoginPage.tsx` among them; 2 generated
  files; 5 test files, `frontend/src/auth/LoginPage.test.tsx` among them; records TS-001, ADD-006,
  RISK-005, SOUP-013, SOUP-021, three PRBs). One task by the human's decision (2026-11-06); the three defects
  share `session.py` and its tests.
- **Needs:** a Docker daemon for the real-Redis tests.

### No shared files with the in-progress tasks

Checked on 2026-11-06 against the task texts and `git status`:

| Task | Its files | Overlap with TASK-205 |
|---|---|---|
| TASK-138 | `backend/app/core/logging.py`, `backend/app/workers/*`, `backend/tests/test_log_redaction.py`, `backend/tests/workers/*`, TS-017, PRB-011 | none |
| TASK-142 | `frontend/src/app/*`, `frontend/src/core/nav/*`, TS-002, PRB-014 | none (TASK-205's only frontend files are `frontend/src/auth/LoginPage.tsx` and its test, which are not TASK-142's) |
| TASK-204 | `backend/app/api/routers/attachments.py`, `backend/app/api/content_disposition.py`, `backend/app/attachments/service.py`, their tests, TS-007, ADD-012, RISK-007, PRB-063 | none |

`backend/openapi/openapi.json` and `frontend/src/api/generated/openapi.ts` are not modified in the working
tree and no in-progress task regenerates them. If one of those tasks starts to, TASK-205 regenerates last.

## Objective

SR-030 AC 5 (a logged-out token cannot be reused), AC 1 to AC 3 (a session ends on inactivity or at its
absolute lifetime and stays ended) and AC 7 (at most 3 active sessions; the oldest **active** one is
ended; the user is notified). Three defects found by QA in the TASK-199 review break them:

- **PRB-064:** `resolve()` refreshes with an unconditional `SETEX` (`session.py:186-188`), which
  re-creates a key that logout, eviction or the password-change loop deleted after the `GET`
  (`session.py:158`).
- **PRB-065:** members whose key expired stay in `account_sessions:{id}` and are counted and evicted by
  rank (`session.py:127-139`).
- **PRB-066:** `LoginSuccess` drops `evicted_session_id` (`login.py:126-138`) and the route hard-codes
  `evicted_session=False` (`routers/auth.py:86`).

Plus the four LOW findings of the TASK-199 QA review (1 to 3 in code, 4 in SOUP-013; orchestrator
decision 2026-11-06).

## Implementation detail

### 1. Refresh never re-creates a session (PRB-064)

- In `resolve()`, replace `self._redis.setex(key, ttl, payload)` with
  `self._redis.set(key, payload, ex=effective_ttl, xx=True)`. Redis `SET … EX … XX` writes only if the
  key exists, in one atomic command (Redis ≥ 2.6.12; redis-py `set(xx=True)`).
- If the call returns `None` (the key was deleted after the `GET`), `resolve()` returns `None`: the
  session was ended by someone else and the request is answered 401, as for any ended session.
- No WATCH/MULTI is needed: the conditional write closes the window by itself. The payload's
  `last_seen_at` can still be overwritten by a concurrent refresh of the same session; that is
  harmless (both write "now").
- If `effective_ttl` is ≤ 0 (absolute expiry in this second) the existing absolute-expiry branch
  already returns `None` first; keep that order.

### 2. Expired members do not count toward the cap (PRB-065)

Inside the TASK-199 transaction in `_store_with_cap`, between `WATCH` and `MULTI`:

- After `ZRANGE … WITHSCORES`, read which member keys still exist in immediate mode (one pipelined
  `EXISTS session:{id}` per member, not inside `MULTI`). Dead ids are those whose key is gone.
- Count and evict over **live** ids only:
  `evicted = live_ids[: max(0, len(live_ids) + 1 - cap)]`.
- In `MULTI`, also `ZREM` the dead ids. Order of queued commands: `ZREM` dead, `DELETE`/`ZREM` evicted,
  `SET` new, `ZADD` new, `EXPIRE` set.
- The score rule stays as TASK-199 made it (`max(now, newest + 1e-6)`, newest over all members read).
- Why this is safe without watching the member keys: after part 1, a deleted session key is never
  written again, so a key found missing stays missing. A key that expires between the `EXISTS` and
  `EXEC` is counted live once more; at worst the transaction evicts a session that was already dead,
  which deletes nothing that is live. The cap on live sessions holds in both cases.
- Not changed: `list_account_session_ids()` and `invalidate_all()` may still see dead ids; deleting a
  missing key is a no-op.

### 3. Login reports the eviction (PRB-066)

- `LoginSuccess` (`login.py:31-35`) gains `evicted_session: bool = False`; `LoginService.login` sets it
  from `result.evicted_session_id is not None`.
- `routers/auth.py:86` returns `evicted_session=result.evicted_session`.
- Frontend: SR-030 AC 7 says the system "presents a notification to the user". The login page already
  does so when `evictedSession` is true (`frontend/src/auth/LoginPage.tsx:34-37`, `:61-71`; test
  `frontend/src/auth/LoginPage.test.tsx:130`). Its text is wrong ("Your previous session was ended
  because you signed in elsewhere"): change it in `LoginPage.tsx` to say that the user's oldest session
  on another device was signed out because the limit of 3 sessions was reached, for example "Your
  oldest session on another device was signed out because you reached the limit of 3 sessions." The
  test at `LoginPage.test.tsx:130` asserts the new text. Telling the user on the ended session is not
  required by SR-030 AC 7 and is out of scope.
- The `LoginResponse` schema is unchanged (`evicted_session` exists, `schemas/auth.py:39`).

### 4. TASK-199 QA LOW items

- **Finding 1 (score):** a fakeredis test seeds the set with a member scored `now + 10` (and a live key),
  logs in, asserts the new member's score is above it, then logs in past the cap and asserts the seeded
  member is the one evicted.
- **Finding 2 (contention):** new `SessionCapContentionProblem(ProblemError)` in `backend/app/api/errors.py`:
  status 503, title "Service Unavailable", type slug `session-cap-contention`, a generic detail (no
  account id), and a `headers = {"Retry-After": "1"}` attribute. `problem_error_handler` passes
  `getattr(exc, "headers", None)` to the `JSONResponse` (one-line change; other problems have none). The
  login route catches `SessionCapContentionError` around `svc.login(...)` and raises the problem. No
  session is stored (TASK-199 already guarantees it) and no `LOGIN_SUCCESS` row is written. Document the
  503 in the route's `responses=` and regenerate the contract (CLAUDE.md "Backend/Frontend Contract"):
  `backend/openapi/openapi.json`, then `frontend/src/api/generated/openapi.ts` with
  `npm run generate:types`.
- **Finding 3 (docstring):** `session.py:6` says the score is "created_at timestamp"; change it to
  "score = commit order (never below the newest existing score)".

## Tests (write first)

- `backend/tests/auth/test_session_service.py` (fakeredis):
  - `test_resolve_does_not_recreate_a_deleted_session` — a client wrapper deletes the key right after
    the `GET` of `resolve()`; `resolve()` returns `None` and the key does not exist afterwards.
  - `test_resolve_after_invalidate_returns_none` and `test_resolve_refreshes_ttl_of_a_live_session`
    (sliding TTL unchanged).
  - `test_cap_ignores_expired_members` — 3 members, one key deleted (expiry simulated): a new login
    evicts nothing and the dead id is gone from the set.
  - `test_cap_evicts_oldest_live_not_dead` — A (oldest, live), B (dead), C (live), D (live, cap reached):
    the next login evicts A, prunes B, keeps C, D and the new session.
  - `test_new_member_score_above_a_future_scored_member` (finding 1).
- `backend/tests/auth/test_session_cap_concurrency.py` (real Redis, pinned image, existing fixture):
  - `test_refresh_racing_invalidate_never_recreates` — deterministic: a proxy client whose `get` returns
    and then deletes the key through a second connection; `resolve()` returns `None`, key absent.
    Plus a stochastic variant: one thread calls `resolve()` in a loop while another calls `invalidate()`
    once; after both stop the key is absent and `resolve()` returns `None`. 50 repetitions.
  - `test_concurrent_logins_with_expired_members_keep_cap_of_live` — 3 sessions, two given
    `PEXPIRE 50` and allowed to expire, then 10 simultaneous logins: exactly 3 members in the set, every
    member has a live key, no dead id remains. 20 repetitions.
  - `test_concurrent_logins_keep_exactly_the_cap` (TASK-199) unchanged and green.
- `backend/tests/auth/test_login_service.py`: `test_login_reports_eviction_when_cap_reached` and
  `test_login_reports_no_eviction_below_cap`.
- `backend/tests/api/test_auth_router.py`:
  - `test_fourth_login_reports_evicted_session` — three logins, the fourth answers
    `"evictedSession": true`; the first three answered `false`.
  - `test_session_cap_contention_returns_503_with_retry_after` — `create_session` patched to raise
    `SessionCapContentionError`: 503 `application/problem+json`, type `session-cap-contention`,
    `Retry-After: 1`, no `Set-Cookie` for the session, no `LOGIN_SUCCESS` audit call.
  - `TestLogoutEndpoint::test_logout_invalidates_session` (existing): unchanged and green.

Negative controls (record the results in this task):

1. The PRB-064 tests (deterministic fakeredis and real Redis) fail on f254277's `session.py`.
2. The PRB-065 tests fail on f254277's `session.py` (a live session evicted, a dead id left).
3. Remove `xx=True`: the deterministic tests fail. Remove the `ZREM` of dead ids: the "no dead id
   remains" assertions fail. Remove the `+ 1e-6`: the finding-1 test fails.
4. Return `evicted_session=False` again in the route: `test_fourth_login_reports_evicted_session` fails.

## Acceptance criteria

- [x] **AC-1 (SR-030 AC 5, AC 1–3; PRB-064):** a session key deleted by logout, eviction or the
      password-change loop is never written again by a refresh; `resolve()` then returns `None`
      (`backend/tests/auth/test_session_service.py::test_resolve_does_not_recreate_a_deleted_session`,
      `backend/tests/auth/test_session_cap_concurrency.py::test_refresh_racing_invalidate_never_recreates`
      *real Redis*, `backend/tests/api/test_auth_router.py::TestLogoutEndpoint::test_logout_invalidates_session` (existing)).
- [x] **AC-2 (SR-030 AC 7 "oldest active"; PRB-065):** members whose key has expired are pruned inside the
      cap transaction and are neither counted nor chosen for eviction; under concurrent logins the set
      holds exactly the cap of live sessions
      (`test_session_service.py::test_cap_ignores_expired_members`,
      `::test_cap_evicts_oldest_live_not_dead`,
      `test_session_cap_concurrency.py::test_concurrent_logins_with_expired_members_keep_cap_of_live`
      and `::test_one_login_with_the_newest_member_expired_evicts_nothing` *real Redis*, `::test_concurrent_logins_keep_exactly_the_cap` unchanged).
- [x] **AC-3 (SR-030 AC 7 notification; PRB-066):** a login that evicts a session answers
      `evictedSession: true`, any other login `false`, and the login page shows the notice
      (`backend/tests/auth/test_login_service.py::test_login_reports_eviction_when_cap_reached`,
      `backend/tests/api/test_auth_router.py::test_fourth_login_reports_evicted_session`,
      `frontend/src/auth/LoginPage.test.tsx` eviction case, updated to assert the notice "Your oldest active
      session was signed out because the limit of concurrent sessions was reached." (round-2 wording,
      orchestrator decision); the text lives in `frontend/src/auth/LoginPage.tsx`).
- [x] **AC-4 (TASK-199 QA findings 1–3):** the score rule is covered
      (`test_session_service.py::test_new_member_score_above_a_future_scored_member`); cap contention answers
      503 problem+json with `Retry-After: 1` and stores no session
      (`test_auth_router.py::test_session_cap_contention_returns_503_with_retry_after`); the module docstring
      states the commit-order score.

## Verification

```sh
cd backend && uv run pytest tests/auth tests/api/test_auth_router.py tests/api/test_lockout_integration.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
cd backend && uv run python -m app.export_openapi --output openapi/openapi.json
cd frontend && npm run generate:types && npm run typecheck && npm test -- --run src/auth
```

Run the real-Redis file 5 times (the TASK-199 practice) and record the pass counts. `git diff` of the two
generated files shows only the 503 response.

Started-stack check: not needed. The defects are in the Redis command sequence, which the real-Redis
tests exercise with the pinned production image; the HTTP path is covered by the router tests.

## Records

- **TS-001** 1.3 → 1.4 (content change: approval cleared, `in_review`): TC-001.8 refresh never
  re-creates an ended session (AC-1); TC-001.9 expired members pruned, oldest active evicted (AC-2);
  TC-001.10 eviction reported and contention answered 503 (AC-3, AC-4); TC-001.6 gains the finding-1
  test. All `verifies` SR-030 (existing link).
- **ADD-006** 1.1 → 1.2 (`in_review`): `U-AUTH-Session` refresh is a conditional write; the cap counts
  live members and prunes dead ones in the same transaction; the login flow reports the eviction.
  **ADD-005**: no change (one more `ProblemError` subclass inside `U-API-ErrorHandler`).
- **RISK-005** 1.2 → 1.3 (`in_review`): new cause in the sequence of events (an ended session brought back
  by a racing refresh, PRB-064) and one control row: "Session refresh is a conditional write (`SET … XX`),
  so logout, eviction and the password-change session kill cannot be undone by a concurrent request |
  Design | SR-030 AC 5, AC 7; TASK-205 | TS-001 TC-001.8". Residual unchanged (3 × 1, acceptable): the
  estimate already assumed revocable sessions; this makes the assumption true.
- **SOUP-021** (Redis server): relied-on behaviour adds `SET … EX … XX` and `EXISTS`, `in_review`.
  **SOUP-013** (redis-py): relied-on behaviour adds `set(..., ex=..., xx=True)` returning `None` when the
  key is absent; and TASK-199 QA finding 4 fixed (`SOUP-013-redis-py.md:36`: `ZRANGE … WITHSCORES` is an
  immediate-mode read after `WATCH`, before `MULTI`, not one of the commands in the transaction);
  `in_review`.
- **PRB-064, PRB-065, PRB-066**: `## Resolution` written; status `resolved` on QA approval (CR-004 D-8).

## Definition of Done

- [x] AC-1 to AC-4 met; the negative controls recorded; real-Redis pass counts recorded.
- [x] Backend suite passes with coverage ≥ 85 %; frontend `src/auth` tests and typecheck green; `ruff`,
      `mypy` clean; generated contract files regenerated, not hand-edited.
- [x] TS-001 1.4, ADD-006 1.2, RISK-005 1.3, SOUP-013, SOUP-021 `in_review`.
- [x] On QA approval: this task `approved`; PRB-064, PRB-065, PRB-066 `resolved` (CR-004 D-8).
- [x] `traceability-check` shows no error for TASK-205, TS-001, SR-030, ADD-006, RISK-005, SOUP-013,
      SOUP-021, PRB-064, PRB-065, PRB-066.
- [x] `graphify update .` run after the code change.

## Version history

- 1.0 (2026-11-06) — Created by the Software Architect role for PRB-064, PRB-065 and PRB-066 (CR-004
  D-11). `draft`.
- 1.1 (2026-11-06) — Implemented by the Software Developer role; `draft → in_review`. See "Implementation notes".
- 1.1 (2026-11-06) — QA review round 1: CHANGES REQUESTED (finding 1 blocking; 2 and 3 LOW). `in_review → draft`.
- 1.2 (2026-11-07) — Round 2: QA findings 1 to 3 addressed (see "Implementation notes — round 2"); `draft → in_review`.
- 1.2 (2026-11-07) — QA review round 2: APPROVED. `in_review → approved`; AC-1 to AC-4 ticked, AC-2/AC-3 test references aligned with round 2. TS-001 approved; PRB-064, PRB-065, PRB-066 `resolved` (CR-004 D-8).
- 1.3 (2026-11-10) — Six Definition of Done boxes ticked after checking the evidence: QA review 2 (real-Redis file 111/111 three times, 0 traceability errors); developer full suite 1467 passed, coverage 94.41 %; hosted CI green on d53eb7f; TS-001, ADD-006, RISK-005, SOUP-013 and SOUP-021 are now `approved` and PRB-064 to PRB-066 `resolved`; `graphify update .` was run on 2026-11-10, with no run recorded at the time. Status unchanged.

## Implementation notes (Software Developer, 2026-11-06)

**Files.** `backend/app/auth/session.py`, `backend/app/auth/login.py`, `backend/app/api/errors.py`,
`backend/app/api/routers/auth.py`, `frontend/src/auth/LoginPage.tsx`; generated
`backend/openapi/openapi.json` and `frontend/src/api/generated/openapi.ts` (diff: only the 503
response); tests `backend/tests/auth/test_session_service.py`, `test_session_cap_concurrency.py`,
`test_login_service.py`, `backend/tests/api/test_auth_router.py`, `frontend/src/auth/LoginPage.test.tsx`.

**Deviations and assumptions.**

- Notice text (orchestrator decision): "Your oldest session on another device was signed out because the
  limit of 3 concurrent sessions was reached."
- `ProblemError` gained a class attribute `headers: dict[str, str] | None = None` read by
  `problem_error_handler`; `SessionCapContentionProblem.headers = {"Retry-After": "1"}`.
- The existing `_interfere_on_zrange` helper in `test_session_service.py` now also creates a live key for
  each rival (a rival without a key is a dead member and is pruned); `..._gives_up_after_bounded_attempts`
  therefore checks that only rival keys exist.
- Real-Redis racing test: 50 parametrised repetitions (`REPETITIONS * 5 // 2`), each with a refresh
  thread looping against one `invalidate()`.
- RISK-005: the TC-001.6 / TC-001.7 "(planned)" marker of the TC-001.6 row was dropped (the case exists).
- Nothing in `list_account_session_ids()` / `invalidate_all()` changed (as designed).

**Results.**

- `uv run pytest --cov=app --cov-fail-under=85`: 1467 passed, 6 skipped, coverage 94.41 %.
  `uv run pytest modules/dicom_viewer/tests`: 25 passed. `ruff check .`, `black --check .`, `mypy app`
  clean. Frontend `npm run typecheck` clean; `npm test -- --run`: 30 files, 209 tests passed.
- Real-Redis file (`test_session_cap_concurrency.py`, 91 cases each) run 5 times: 91 passed, 91 passed,
  91 passed, 91 passed, 91 passed.

**Negative controls** (`test_session_service.py` + `test_session_cap_concurrency.py`):

1. f254277 `session.py`: 28 failed. `test_resolve_does_not_recreate_a_deleted_session`,
   `test_refresh_racing_invalidate_never_recreates` and 24 of 50 racing repetitions fail.
2. Same file: `test_cap_ignores_expired_members` and `test_cap_evicts_oldest_live_not_dead` fail. The
   real-Redis expired-members test does not fail on the old code (the dead ids are the oldest, so
   10 logins evict them anyway); it fails with control 3b.
3. a) `xx=True` removed: 26 failed (deterministic fakeredis, deterministic real Redis, 24 racing).
   b) `ZREM` of dead ids removed: 22 failed (2 fakeredis, 20 of 20 real-Redis expired-members).
   c) `+ 1e-6` removed: `test_new_member_score_above_a_future_scored_member` fails (1 failed).
4. `evicted_session=False` in the route: `test_fourth_login_reports_evicted_session` fails.

## Implementation notes — round 2 (Software Developer, 2026-11-07)

1. **[MEDIUM] Real-Redis PRB-065 test.** `test_session_cap_concurrency.py`: new helper `_expire_newest` (three
   sessions, the newest one expired). `test_concurrent_logins_with_expired_members_keep_cap_of_live`
   (20 repetitions) now collects each `CreateSessionResult` and asserts `dead not in evicted` and
   `len(evicted) == 2 + LOGINS - CAP`, besides the unchanged set and key assertions. New
   `test_one_login_with_the_newest_member_expired_evicts_nothing` (20 repetitions): `evicted_session_id is None`,
   set == {oldest, middle, new}, oldest key live. Negative controls on these 40 cases: f254277 `session.py`
   40 failed (20 + 20); dead-as-live mutant (`alive = [True for sid in ids]`) 40 failed (20 + 20); `ZREM` of dead
   ids removed 40 failed (20 + 20). Fixed `session.py` restored and diffed afterwards. TS-001 TC-001.9 and the
   PRB-065 Resolution updated.
2. **[LOW] 503 at login.** `LoginPage.tsx` shows "Sign-in is busy. Please try again." when the error is an
   `ApiError` with `problem.status === 503`; new test in `LoginPage.test.tsx`.
3. **[LOW] Notice text.** Now "Your oldest active session was signed out because the limit of concurrent
   sessions was reached."; test and TS-001 TC-001.10 updated. (Supersedes the wording in round 1.)

## QA review — round 1 (2026-11-06): CHANGES REQUESTED

Reviewed the TASK-205 files only (`git diff` on f254277, shared tree). The production code is correct; the
blocking finding is a test that cannot tell the old code from the new one.

### Findings

1. **[MEDIUM, blocking] The real-Redis PRB-065 test does not distinguish f254277 from the fix** —
   `backend/tests/auth/test_session_cap_concurrency.py:188-226`
   (`test_concurrent_logins_with_expired_members_keep_cap_of_live`). The dead ids are the two oldest, so
   the old rank-based eviction removes them anyway and every assertion holds: 0 of 20 repetitions fail on
   f254277's `session.py`. Negative control 2 of this task ("the PRB-065 tests fail on f254277") is
   therefore unmet for this test, and the mutant "count dead members as live"
   (`alive = [True for sid in ids]`) is killed only by the two fakeredis tests. QA re-ran the developer's
   assertions with the **newest** member expired instead (older two live): still 20 of 20 pass on f254277.
   QA probes that do discriminate (scratch copy, real Redis `redis:7.4.12-bookworm`):
   - single login after the newest member expired: `evicted_session_id is None`, the oldest member is
     still live, and the set is {oldest, middle, new}. Result: 5 of 5 fail on f254277, 5 of 5 pass on
     the fix;
   - 10 simultaneous logins after the newest member expired: collect each `CreateSessionResult` and
     assert `dead not in evicted` and `len(evicted) == 2 + LOGINS - CAP` (9). Result: 20 of 20 fail on
     f254277, 20 of 20 fail on the dead-as-live mutant, 20 of 20 pass on the fix.

   → Change the arrangement to expire the newest member (`dead = original[-1]`), keep the existing set
   and key assertions, and add the evicted-id assertions above. Optionally add the single-login case.
   Re-run the negative controls (f254277 and the dead-as-live mutant must fail) and record the results here.
   Update TS-001 TC-001.9 (arrangement and pass criterion) and the PRB-065 Resolution ("the real-Redis case
   fails on f254277 ...").
2. **[LOW] A 503 at login is shown as "Invalid email or password."** — `frontend/src/auth/LoginPage.tsx:75-79`.
   The page renders the same alert for every error, so a user with the right password who hits cap
   contention is told the credentials are wrong. The 503 is rare (20 failed optimistic attempts) and a
   retry succeeds. → Branch on the error status: for 503, show "Sign-in is busy. Please try again." Add one
   test to `LoginPage.test.tsx`. Can be carried to TASK-202 if the orchestrator prefers.
3. **[LOW] The notice text can be inaccurate** — `frontend/src/auth/LoginPage.tsx:71`. The limit "3" is
   hard-coded, but the cap is configurable (`SESSION_MAX_CONCURRENT`). "On another device" is not always
   true: a re-login in the same browser without logout leaves the earlier session live in Redis, and that
   session can be the one evicted. The text was the orchestrator's decision, so this is not blocking. →
   Either say "Your oldest active session was signed out because the limit of concurrent sessions was
   reached", or record that the deployed cap is fixed at 3 (SR-030 AC 7 states 3).

### Judged and accepted (no finding)

- **EXISTS outside MULTI.** If a key expires between `EXISTS` and `EXEC`, it is counted live once more.
  At worst this one login evicts one more session than needed (the cap is one stricter), or it reports
  `evicted_session: true` for a session that had just expired. Nothing live is kept above the cap. A
  member is ended between `EXISTS` and `EXEC` by `invalidate()`, which runs `ZREM` on the watched set
  before `DEL`, so `EXEC` aborts and the attempt retries. No code path writes `session:{id}` for an
  existing id except `resolve()`, which is now `SET … XX`, so a dead id cannot come back alive before
  `EXEC`.
- **PRB-064.** `resolve()` races a `ZREM`+`DEL` (eviction, `invalidate()`): the `SET … XX` after the
  `DEL` writes nothing and `resolve()` returns `None`. QA checked on the pinned real Redis that
  `set(..., ex=10, xx=True)` returns `None` and creates no key when the key is absent, and returns
  `True` with the TTL set when the key exists. That confirms the SOUP-013/021 text. The deterministic
  and racing tests fail on f254277 (1/1 and 25/50).
- **503 path.** `ProblemError.headers` defaults to `None` and only `SessionCapContentionProblem`
  overrides it; there is no other `ProblemError` subclass in `backend/app`. The generic handler is
  unchanged. The OpenAPI diff is the 503 entry only. The export and `openapi-typescript` reproduce both
  committed files byte for byte, and `tsc` is clean.
- **Notice.** It is shown only when `result.evictedSession` is true (`LoginPage.tsx:34-37`). The router
  test with the real services shows `[False, False, False, True]`.
- **Records.** SOUP-013/021 are accurate (the `setex` grep over `backend/app` is empty).
  The "(planned)" removal in the RISK-005 TC-001.6 row is justified: TC-001.6 exists and TS-001 1.3 was
  QA-approved. ADD-006 1.2 is consistent with the code. The PRB-064 and PRB-066 Resolutions are
  reproducible; for PRB-065 see finding 1.

### Pre-existing (not blocking)

- `ruff format --check` reformats `backend/tests/auth/test_session_service.py:186-187`
  (`_interfere_on_zrange` signature, from TASK-199; the same at f254277). CI runs `ruff check` only.

### Verification run (QA)

- `uv run pytest tests/auth tests/api/test_auth_router.py tests/api/test_error_handlers.py`: 192 passed.
- `tests/auth/test_session_cap_concurrency.py` 3 times: 91, 91 and 91 passed.
- `uv run mypy app/auth app/api`: no issues (37 files). `ruff check` on the 8 changed Python files:
  clean.
- OpenAPI export: identical to `backend/openapi/openapi.json`. Types regenerated to scratch: identical to
  `frontend/src/api/generated/openapi.ts`. `npm run typecheck` clean. `npx vitest run src/auth`: 7 files,
  28 tests passed.
- Mutants (auth + router + error-handler suites, 192 tests). Each was killed:

  | Mutant | Failing tests |
  |---|---|
  | no `xx=True` | 35 |
  | dead-id `ZREM` removed | 22 |
  | dead counted live | 2 (fakeredis only) |
  | no `+1e-6` | 1 |
  | route `False` | 1 |
  | handler drops headers | 1 |
  | `if not refreshed` removed | 2 |
  | 503 mapping removed | 1 |
  | evict newest live | 25 |

- Old `session.py` (f254277) on the real-Redis file: 26 developer tests fail (25 racing, 1 deterministic).
  0 of the TC-001.9 tests fail.
- `traceability-check` (TASK-205, TS-001, ADD-006, RISK-005, SOUP-013, SOUP-021, PRB-064, PRB-065, PRB-066,
  SR-030, CR-004): 0 errors, 1 warning (W5 SR-030 → RISK-005 `in_review`, awaiting the human).

## QA review — round 2 (2026-11-07): APPROVED

Round-1 findings 1 to 3 are closed. The backend source is unchanged since round 1: `session.py`, `errors.py`
and `routers/auth.py` are byte-identical to the versions reviewed then.

- **Finding 1 (closed).** `_expire_newest` expires the newest member. Both real-Redis TC-001.9 tests now
  discriminate. QA re-ran them together with its own round-1 probes (scratch copy, real Redis):
  - f254277 `session.py`: 20/20 concurrent and 20/20 single-login fail (QA probes 20/20 and 5/5);
  - dead-as-live mutant: 20/20 and 20/20 fail (QA probes 20/20 and 5/5);
  - dead-id `ZREM` removed: 20/20 and 20/20 fail;
  - fix: 157 of 157 pass (the file plus the QA probes).
- **Finding 2 (closed).** On a 503 `ApiError`, `LoginPage.tsx` shows "Sign-in is busy. Please try again.".
  Mutant `=== 599`: the new test fails (1 of 7).
- **Finding 3 (closed).** The notice is now neutral and does not hard-code the limit. It is still shown only
  when `evictedSession` is true. Mutant `if (true)`: 2 of 7 fail.
- **Record hygiene (QA edits, no finding).** In this task, AC-2 now lists the single-login test and AC-3
  quotes the round-2 notice text. The developer's 1.2 history line was moved into "Version history". PRB-065's
  frontmatter `version`/`updated` were aligned with its 1.2 history line.

Verification (QA, 2026-11-07):

- real-Redis file 3 times: 111, 111 and 111 passed;
- `uv run pytest tests/auth tests/api/test_auth_router.py tests/api/test_error_handlers.py`: 212 passed;
- `uv run mypy app/auth app/api`: clean; `ruff check` on `app/auth`, `app/api`, `tests/auth` and the router
  test: clean;
- `npx vitest run src/auth`: 29 passed; `npm run typecheck` and eslint on both LoginPage files clean;
- `traceability-check` (TASK-205, TS-001, ADD-006, RISK-005, SOUP-013, SOUP-021, PRB-064 to PRB-066, SR-030,
  CR-004): 0 errors.

Carried: the pre-existing `ruff format` diff at `test_session_service.py:186-187` (TASK-199).

