---
id: "PRB-023"
type: problem-report
title: "Concurrent-session cap eviction is not atomic"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-06"
criticality: major
links: []
tags: ["correctness", "hazard:security"]
---

# PRB-023 — Concurrent-session cap eviction is not atomic

## Observed

`app/auth/session.py:97` implements the concurrency cap as a multi-step read-then-write sequence against Redis with no transaction, so two simultaneous logins can both pass the cap or evict the wrong session.

## Impact

The SR-030 concurrent-session limit is not reliably enforced.

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role). **Present as reported.**

- `SessionService.create_session` (`backend/app/auth/session.py:95-112`) runs six separate Redis
  commands: `ZRANGE` of the account's sessions, then, at the cap, `DELETE` and `ZREM` of the
  oldest, then `SETEX`, `ZADD` and `EXPIRE` for the new one. Nothing makes them one operation.
- Two logins for one account at the cap (3 sessions) both read the same three ids, both evict
  the same oldest one, and both add their own: 4 sessions remain, contrary to SR-030 AC 7. With a
  login and an eviction interleaved differently, an attacker's session can survive the eviction
  that should have removed it.
- No test runs concurrent logins; the unit tests use `fakeredis` sequentially
  (`backend/tests/auth/test_session_service.py`).

## Safety evaluation

Contributes to RISK-005 (account takeover: an attacker session survives an eviction meant to remove it).

## Resolution

Implemented in TASK-199 (CR-004), 2026-11-02, awaiting QA. `SessionService.create_session`
(`backend/app/auth/session.py`) now stores the session through `_store_with_cap`: one optimistic
Redis transaction. `WATCH` the account's sorted set; read it with scores; in `MULTI` queue `DEL`
of the evicted session keys, `ZREM` of the evicted ids, `SET … EX` of the new session, `ZADD` and
`EXPIRE` of the set; `EXEC`. If another login changed the set meanwhile `EXEC` raises `WatchError`
and the attempt is repeated, at most 20 times, then `SessionCapContentionError` is raised and
nothing is stored. The oldest sessions (lowest score) above the cap are evicted; the new one is
never evicted by its own login. The new session's score is never below the newest existing score,
so ranking follows commit order even when a login read its clock before a rival committed.
`CreateSessionResult.evicted_session_id` keeps its meaning. Eviction was not audited before and is
not now (the login success audit is unchanged).

Verification: `backend/tests/auth/test_session_cap_concurrency.py` (real `redis:7.4.12-bookworm`
container, 10 simultaneous logins at the cap of 3, 20 repetitions per run). On the previous code
all 20 repetitions failed in each of 5 runs (more than 3 sessions remained). On the new code 10
consecutive runs (200 repetitions) passed with no failure. Negative control: reverting `session.py`
to the previous version makes all 20 repetitions fail again (3 runs). TS-001 TC-001.6. QA approved TASK-199 on 2026-11-06 and set `status` to `resolved` (D-8).

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Performance.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
- 1.2 (2026-11-02) — TASK-199 (CR-004): `## Resolution` written (fix implemented, awaiting QA). Status and criticality unchanged.
- 1.2 (2026-11-06) — QA review (TASK-199): approved; status `open → resolved` (D-8). CR-004 `resolves` PRB-023. Criticality unchanged.
