---
id: "TASK-199"
type: task
title: "Enforce the concurrent-session cap atomically"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-06"
links:
  - target: "SR-030"
    relation: implements
  - target: "RISK-005"
    relation: mitigates
  - target: "PRB-023"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-006"
    relation: relates_to
tags: ["security", "auth", "cr:CR-004", "control:design"]
---

# TASK-199 — Enforce the concurrent-session cap atomically

- **Software item / unit:** SI-AUTH `U-AUTH-Session` (ADD-006).
- **PRB:** PRB-023. **CR:** CR-004.
- **Depends on:** none. Independent; can run in parallel with any CR-004 task (touches only
  `backend/app/auth/session.py`).
- **Branch:** `fix/review-2026-07-security`.
- **Size:** S (`backend/app/auth/session.py`; 2 test files; TS-001)
- **Needs:** a Docker daemon for the real-Redis concurrency test.

## Objective

SR-030 AC 7: at most `SESSION_MAX_CONCURRENT` (3) sessions per account, oldest evicted, under
concurrent logins. PRB-023 Investigation: six separate commands (`session.py:95-112`).

## Implementation detail

- One optimistic transaction with redis-py `Redis.transaction(fn, account_key)`: `WATCH` the
  account's sorted set; read it; in `MULTI`: `ZADD` the new id, `ZREMRANGEBYRANK` to keep the
  newest N, `DELETE` the evicted session keys, `SETEX` the new session, `EXPIRE` the set; `EXEC`;
  on `WatchError` retry (bounded, e.g. 5), then raise.
- Chosen over a Lua script: `fakeredis` runs Lua only with the `lupa` package, which is not a
  dependency; `WATCH`/`MULTI` needs no new dependency (CR-004 boundary) and is supported by both.
- `CreateSessionResult.evicted_session_id` keeps its meaning (first evicted id, if any).

## Tests (write first)

- `backend/tests/auth/test_session_service.py` (`fakeredis`): cap holds sequentially; eviction
  of the oldest; `WatchError` path retried (forced by a concurrent write between `WATCH` and
  `EXEC`); bounded retries then error.
- `backend/tests/auth/test_session_cap_concurrency.py` (real Redis via testcontainers'
  `DockerContainer` with the pinned `redis` image of `infra/docker-compose.yml`): 3 sessions
  exist; 10 threads log in at once → exactly 3 sessions remain in the set and as keys; every
  evicted key is gone. Repeat 20 times.

## Acceptance criteria

- [x] SR-030 AC 7: concurrent logins leave at most 3 sessions (`backend/tests/auth/test_session_cap_concurrency.py`).
- [x] Sequential behaviour unchanged (`backend/tests/auth/test_session_service.py`,
      `backend/tests/api/test_auth_router.py`).

## Verification

```sh
cd backend && uv run pytest tests/auth tests/api/test_auth_router.py -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
```

Negative control: run the concurrency test against the current code first; it must fail
(more than 3 sessions) at least once in 20 runs. Record the result.

## Records

- **TS-001**: TC-001.6 (atomic cap under concurrency), under TASK-140's 1.2, `verifies` SR-030.
- **SOUP-021** (Redis server), **SOUP-013** (redis-py): `WATCH`/`MULTI`/`EXEC` relied on; `in_review`.
- **PRB-023**: `## Resolution`, `resolved`.

## Definition of Done

- [x] Backend suite passes; coverage ≥ 85 %.
- [x] TS-001, SOUP-013, SOUP-021 `in_review`; PRB-023 `resolved`.
- [x] `traceability-check` shows no error for TASK-199, TS-001, SR-030, PRB-023.

## Implementation notes (2026-11-02, software developer)

Handed to QA as `in_review`. No checkbox is ticked. Nothing is staged or committed.

### Files

- `backend/app/auth/session.py`: new `SessionService._store_with_cap`, `SessionCapContentionError`,
  `_MAX_CAP_ATTEMPTS = 20`; `create_session` calls it.
- `backend/tests/auth/test_session_cap_concurrency.py` (new, real Redis, TC-001.6).
- `backend/tests/auth/test_session_service.py` (three added cases).
- Records: TS-001 (1.3, `in_review`), SOUP-013 (1.2, `in_review`), SOUP-021 (1.4, `in_review`),
  both without approval record; PRB-023 (1.2, `## Resolution`, still `open`).

### Mechanism

`pipeline()` loop: `WATCH account_sessions:{id}`; `ZRANGE … WITHSCORES` (immediate mode); `MULTI`;
`DEL` evicted keys, `ZREM` evicted ids, `SET … EX` the session, `ZADD`, `EXPIRE`; `EXEC`;
`WatchError` retries. Evicted = the oldest `len(existing) + 1 - cap` members. Eviction order and
`evicted_session_id` (first evicted id) are unchanged; eviction was not audited before and still
is not.

### Deviations from the task text

- Retry bound is 20, not "e.g. 5". Each failed attempt means a rival login committed, so a burst of
  N logins can force the last one through N attempts; 5 would raise under the 10-login test. A
  hand-written loop is used instead of `Redis.transaction()`, which retries without a bound.
- `ZREM` of the computed ids instead of `ZREMRANGEBYRANK`, so the login's own new session can never
  be the one evicted.
- Score of the new member is `max(now, newest existing score + 1e-6)`. Without it, a login that read
  its clock before a rival committed was ranked older than the rival, and a strict "oldest evicted"
  check failed in 11 to 18 of 20 repetitions even though the count was right.
- `SET … EX` replaces `SETEX` in the new code (redis-py deprecates `setex`).

### Evidence

- Before the fix, concurrency test: 5 full runs, 20 of 20 failed each (more than 3 sessions).
- After: 10 consecutive runs, 200 of 200 repetitions passed (plus 9 earlier runs, all passing).
- Negative control: `session.py` reverted to HEAD, 3 runs, 20 of 20 failed each; restored.
- `uv run pytest tests/auth tests/api/test_auth_router.py`: 103 passed.
- `uv run pytest --cov=app --cov-fail-under=85`: 1322 passed, 6 skipped, coverage 94.15 %.
- `ruff check .`, `black --check .`, `mypy app`: clean.

## QA review — round 1 (2026-11-06): APPROVED

QA Engineer role. Reviewed `git diff` of `backend/app/auth/session.py`,
`backend/tests/auth/test_session_service.py`, the new `backend/tests/auth/test_session_cap_concurrency.py`,
TS-001, PRB-023, SOUP-013 and SOUP-021. HEAD moved to 944ef24 (TASK-200, TASK-139) during the
review; none of these files changed between ed22a70 and 944ef24, and the working-tree `session.py`
was confirmed identical to the reviewed copy before the records were updated.

Evidence (run by QA):

- Concurrency test on the working tree: 5 runs, 100 of 100 repetitions passed.
- Negative control (scratch copy, `session.py` from HEAD): 3 runs, 20 of 20 failed each (11 or 12
  sessions left in the set).
- Mutation, WATCH on an unrelated key (reads stay immediate, set unprotected): 3 runs, 20 of 20
  failed each (4 to 12 sessions); the fakeredis retry tests also fail (2 of 16).
- Mutation, WATCH removed entirely: 20 of 20 failed, 15 of 16 unit tests failed.
- Mutation, score adjustment `+ 1e-6` removed: survives (all tests pass). See finding 1.
- Probe, 40 simultaneous logins: `SessionCapContentionError` raised, nothing stored (fails closed).
- `uv run pytest tests/auth tests/api/test_auth_router.py`: 103 passed. `uv run mypy app/auth` and
  `mypy app`: clean. `ruff check` and `black --check` on the three files: clean.
  `session.py` coverage 96 % (the uncovered lines are the existing `invalidate_all`).
- Full suite: 1344 passed, 6 skipped, 3 failed, coverage 94 %. The 3 failures are in
  `tests/workers/test_email_tasks_logging.py`, an untracked file of another task in the shared
  tree; it passes on its own (5 passed). Not TASK-199.
- `traceability-check` (fallback parser, whole project, 411 records): 0 errors.

Findings (all LOW, not blocking; carry them to a later task):

1. LOW — `backend/app/auth/session.py:134` — the `max(now, newest + 1e-6)` score is not covered by any
   test (mutation survives). Add a fakeredis test: seed the set with a member scored `now + 10`, log
   in, assert the new member's score is above it and that the next login past the cap evicts the
   seeded member.
2. LOW — `backend/app/auth/login.py:126` / `backend/app/api/errors.py:171` —
   `SessionCapContentionError` reaches the generic handler: RFC 7807 500 `internal-error`, traceback
   only in the server log, no audit row. Safe (no session stored), but map it to a `ProblemError`
   503 with `Retry-After` so a client can retry.
3. LOW — `backend/app/auth/session.py:6` — module docstring still says "score = created_at
   timestamp"; it is now commit order (never below the newest existing score).
4. LOW — `docs/soup/SOUP-013-redis-py.md:36` — lists `ZRANGE … WITHSCORES` among "the commands in
   the transaction"; it is an immediate-mode read after `WATCH`, before `MULTI` (SOUP-021:34 has it
   right). Fix the wording when the human reviews SOUP-013.

Not introduced here (pre-existing, raise as PRBs):

- `SessionService.resolve` (`session.py`, GET then `SETEX`) can re-create a session key that a
  concurrent eviction or logout deleted between the two calls. The session is then live, outside the
  account set, beyond the cap, and missed by the password-change "invalidate others" loop. Reproduced
  deterministically with fakeredis. Fix: `SET … EX … XX` in `resolve`. Relates to RISK-005 and SR-030.
- A member whose key expired by inactivity stays in the set and counts toward the cap; a later login
  can evict an older live session while the dead member stays (SR-030 AC 7 says "oldest active").
  Same behaviour as before TASK-199.
- The login route always returns `evicted_session: false`, so SR-030 AC 7's "presents a notification"
  is not met. Unchanged by this task.

