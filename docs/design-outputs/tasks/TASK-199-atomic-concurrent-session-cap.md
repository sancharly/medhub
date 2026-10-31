---
id: "TASK-199"
type: task
title: "Enforce the concurrent-session cap atomically"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
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

- [ ] SR-030 AC 7: concurrent logins leave at most 3 sessions (`backend/tests/auth/test_session_cap_concurrency.py`).
- [ ] Sequential behaviour unchanged (`backend/tests/auth/test_session_service.py`,
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

- [ ] Backend suite passes; coverage ≥ 85 %.
- [ ] TS-001, SOUP-013, SOUP-021 `in_review`; PRB-023 `resolved`.
- [ ] `traceability-check` shows no error for TASK-199, TS-001, SR-030, PRB-023.
