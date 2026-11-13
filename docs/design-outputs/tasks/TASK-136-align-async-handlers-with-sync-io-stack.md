---
id: "TASK-136"
type: task
title: "Blocking IO off the event loop, with thread and connection pools sized together"
status: draft
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-13"
links:
  - target: "SR-026"
    relation: implements
  - target: "NFR-008"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-009"
    relation: relates_to
  - target: "PRB-072"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
  - target: "ADD-016"
    relation: relates_to
  - target: "TASK-217"
    relation: relates_to
  - target: "TASK-025"
    relation: relates_to
tags: ["phase:review-2026-07", "cr:CR-006", "performance", "control:design"]
---

# TASK-136 — Blocking IO off the event loop, with thread and connection pools sized together

- **Software item / unit:** SI-API `api/deps.py`, routers (ADD-005); SI-PERSIST engine (ADD-016); SI-AUTH
  Redis client (ADD-006, no behaviour change).
- **PRB:** PRB-009; PRB-072 joins CR-006 only if the step 5 measurement shows it follows from PRB-009
  (D-1). **CR:** CR-006 (D-3, D-14; ADR-0022).
- **Depends on:** TASK-217 (same router). **Step 1 runs at the start of the Build stage** on the
  plan-time head, before TASK-135 is committed (baseline).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** M (`backend/app/api/deps.py`, `backend/app/api/routers/auth.py`,
  `backend/app/api/routers/attachments.py`, `backend/app/db/repositories/session.py`,
  `backend/app/core/config.py`, `backend/app/main.py` (lifespan); new `backend/scripts/load_test.py`; tests
  `backend/tests/api/test_no_blocking_in_async.py`, `backend/tests/core/test_pool_settings.py`; records
  TS-018 new, ADD-005, ADD-016, SOUP-003/008/013 relied-on text).
- **Ask first:** changing pool or thread values in `infra/docker-compose.yml` or `.env.example` (D-14).

## Objective

SR-026 AC 5: 20 authenticated clients, mixed reads and writes, one API worker: no 5xx, SR-026 AC 1 and AC 2
budgets hold, and a slow call for one request does not delay unrelated ones. Today `get_session`,
`get_current_user` (`deps.py:43,70`), `require_module_enabled._dependency` (`:138`), `upload_attachment`,
`logout` and `extend_session` (`routers/auth.py:102,125`) are `async def` over sync Redis, SQLAlchemy and
boto3 (PRB-009). Moving them to threads must not create the PRB-072 shape (40 threads, 15 DB connections,
30 s pool timeout).

## Steps

1. **Load script and baseline (first).** `backend/scripts/load_test.py` (httpx, already a dependency; no new
   package): N clients (default 20) sign in with seeded accounts and loop over a mix: `GET /me`, list
   appointments, list clinical entries, create a clinical entry, 1 MiB attachment upload, attachment
   download; fixed duration (5 min); reports count, 5xx count, p50/p95/max per operation, and pool
   timeouts from the log. Run on a started stack (`infra/docker-compose.yml`, one Gunicorn worker) on the
   plan-time head; record the result here as "before".
2. **Sync dependencies.** `get_session`, `get_current_user`, `require_module_enabled._dependency`, `logout`,
   `extend_session` become plain `def` (they await nothing). `upload_attachment` stays `async` and calls the
   blocking service via `run_in_threadpool` (already done by TASK-135; verify).
3. **Static guard:** `test_no_blocking_in_async.py` walks `app/api` with `ast`; any `async def` that calls a
   name from a deny list (`.query`, `.execute`, `.get`/`.set`/`.setex` on a Redis client, service methods
   known to block, `put_object`/`get_object`) without `run_in_threadpool`/`await` fails. Planted negative case.
4. **Pool settings (ADR-0022):** `API_THREADPOOL_SIZE` (lifespan sets
   `anyio.to_thread.current_default_thread_limiter().total_tokens`), `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`,
   `DB_POOL_TIMEOUT` on the engine, Redis `max_connections` = thread-pool size. Start-up refuses
   `API_THREADPOOL_SIZE > DB_POOL_SIZE + DB_MAX_OVERFLOW`. Code defaults: 40 / 20 / 20 / 10 s (candidate).
5. **Measure and propose.** Re-run the load test on the task head with the candidate values and with one
   alternative if the first shows queueing (pool wait in the log or p95 over budget). Record both runs here
   ("after") and the **proposed values for the human (D-14)**. The deployed configuration is not changed
   until the human approves; TASK-226 runs the final measurement. If PRB-072's 20-client failure disappears
   with step 2 and the pool settings, say so for D-1.
6. Update SOUP-003 (AnyIO default limiter), SOUP-008 (`QueuePool` sizing and `pool_timeout`), SOUP-013
   (`max_connections`) relied-on text.

## Tests (write first)

- `test_no_async_def_calls_blocking_client` and its planted negative (SR-026 AC 5, NFR-008).
- `test_startup_refuses_threadpool_larger_than_db_pool` (SR-026 AC 5, ADR-0022).
- `test_slow_db_call_does_not_block_unrelated_request` (SR-026 AC 5): with a dependency patched to sleep
  2 s in a thread, a concurrent `GET /healthz` returns in < 200 ms.
- TS-001 and TS-002 suites run unchanged (authorization and session decisions unchanged; RISK-001,
  RISK-005).
- Load test before/after (SR-026 AC 1, AC 2, AC 5) recorded in a new TS-018 "Performance budgets and
  data-access cost verification" (`verifies` SR-026), TC-018.1 (static), TC-018.2 (slow call isolation),
  TC-018.3 (load test, final run in TASK-226).

## Acceptance criteria

- [ ] No `async def` in `app/api` calls a blocking client (static test green, negative case fails).
- [ ] Pool settings with the start-up invariant; values proposed with before/after evidence for the human.
- [ ] Load test on the task head: 0 × 5xx and AC 1 / AC 2 p95 within 3 s at 20 clients (or the gap reported).
- [ ] TS-001, TS-002 unchanged and green.

## Definition of Done

- [ ] `ruff`, `mypy`, backend suite green
- [ ] TS-018 created; ADD-005, ADD-016 consistent; SOUP relied-on text updated
- [ ] `traceability-check` no error for this record

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect). Re-based on SR-026 AC 5 (D-3) and ADR-0022: line
  numbers refreshed (PRB-009's `:126,198` sites no longer exist; `routers/auth.py` `logout` and
  `extend_session` added), pool settings with a start-up invariant, load-test baseline first and the
  pool-value proposal for the human (D-14), PRB-072 decision input (D-1). `mitigates` RISK-007 added.
