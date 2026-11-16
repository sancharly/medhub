---
id: "TASK-136"
type: task
title: "Blocking IO off the event loop, with thread and connection pools sized together"
status: approved
version: "1.6"
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
  - target: "TS-018"
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

- [x] No `async def` in `app/api` calls a blocking client (static test green, negative case fails).
- [x] Pool settings with the start-up invariant; values proposed with before/after evidence for the human.
- [x] Load test on the task head: 0 × 5xx and AC 1 / AC 2 p95 within 3 s at 20 clients (or the gap reported).
- [x] TS-001, TS-002 unchanged and green.

## Definition of Done

- [x] `ruff`, `mypy`, backend suite green
- [x] TS-018 created; ADD-005, ADD-016 consistent; SOUP relied-on text updated
- [x] `traceability-check` no error for this record

## Implementation record (Software Developer, 2026-11-13)

**State: implemented in the working tree, not committed. The pool values were approved by the human on
2026-11-13 (CR-006 D-24 to D-26) and are wired in `infra/`.** Status `in_review`.

### Decisions (CR-006, 2026-11-13)

- **D-24:** deployed `API_THREADPOOL_SIZE=20`, `DB_POOL_SIZE=20`, `DB_MAX_OVERFLOW=20`, `DB_POOL_TIMEOUT=10` s; Redis
  pool `max_connections` equals the thread limit (evidence below).
- **D-25:** code defaults 15 threads / pool 5 + overflow 10 / 30 s, per ADR-0022.
- **D-26:** PRB-072 joins CR-006 and is resolved by this task; PRB-009 resolved likewise.

### Files changed

`backend/app/api/deps.py`, `backend/app/api/routers/auth.py`, `backend/app/core/config.py`,
`backend/app/db/repositories/session.py`, `backend/app/main.py`, `backend/tests/test_log_redaction.py`,
`backend/tests/api/test_no_blocking_in_async.py` (new), `backend/tests/core/test_pool_settings.py` (new),
`backend/scripts/load_test.py` (new), `infra/.env.example`, `infra/docker-compose.yml`,
`docs/design-outputs/tests-specifications/TS-018-performance-budgets-and-data-access-cost.md` (new),
`docs/problem-reports/PRB-009-async-handlers-block-event-loop.md`, `docs/problem-reports/PRB-072-*.md`,
`docs/change-requests/CR-006-*.md`, this record.

### Step 1 — baseline ("before"), commit `8028685`

A separate `git worktree` at `8028685` (plan-time head: TASK-135 not yet committed), built and run as its
own Compose project on its own network and volumes, without the reverse proxy or the frontend, with the
backend published on a loopback port and fresh throw-away secrets. The user's running stack, its volumes
and the main checkout were not touched; the stack, volumes, images and the worktree were removed
afterwards. The proxy was bypassed because it refuses bodies above 1 MiB on that commit (PRB-078), and
the 1 MiB upload is at the limit. One Gunicorn worker (the Dockerfile `CMD`: no `-w`), the pool at
SQLAlchemy's defaults (5 + 10, 30 s), AnyIO's 40 threads, Redis unbounded.

Load: `backend/scripts/load_test.py` (new, httpx only; `seed` runs inside the backend container and
creates one doctor and one patient per client; `run` signs in 4 clients at a time, grants consent, creates
one appointment and one entry, then loops for 300 s over the mix GET /me 30 %, list appointments 20 %,
list clinical entries 20 %, create entry 15 %, upload 1 MiB 8 %, download 7 %, with no think time, plus
a `GET /healthz` probe every 100 ms). A transport error is a request that got no response (reset,
refused, timeout). Latencies are over answered requests only.

| Clients | Duration | Requests | 5xx | Transport errors | Gunicorn `WORKER TIMEOUT` | Answered p50 / p95 (GET /me) |
|---|---|---|---|---|---|---|
| 8 | 60 s | 6338 | 0 | 0 | 0 | 0.052 / 0.110 s |
| 16 | 60 s | 128 | 0 | 51 | 3 | 0.282 / 3.238 s |
| **20** | 300 s | 456 | 0 | **210** | **10** | 2.045 / 2.167 s |

20 clients, per operation (count, transport errors, p50 / p95 / max of the answered ones, seconds):
GET /me 121, 38, 2.045 / 2.167 / 2.204; list appointments 91, 39, 0.460 / 2.196 / 2.221; list clinical
entries 90, 41, 2.089 / 2.200 / 2.208; create clinical entry 60, 28, 2.146 / 2.317 / 2.347; upload 1 MiB
54, 54 (none answered); download: none issued (no upload succeeded); `/healthz` probe 40, 10,
0.129 / 2.000 / 2.025.

The stall is exactly the PRB-072 report: 8 clients pass, 20 fail, and the failure threshold lies between
8 and 16, where the 15 connections of the default pool are used up. The server log shows no `QueuePool
limit` line because the worker is killed (`WORKER TIMEOUT` at 30 s, the gunicorn default) before the
pool's own 30 s timeout raises. Every request in flight at a kill is lost, including the ones of clients
that wait for nothing on the database; the answered requests at 2.0 s are the ones that were queued
behind a blocked loop. The static test and the slow-call test fail on `8028685` as TC-018.1 and TC-018.2
say (seven calls named; `/healthz` waited 1.73 s).

### Changes

- `backend/app/api/deps.py`: `get_session`, `get_current_user` and `require_module_enabled._dependency`
  are plain `def` (they awaited nothing); `get_redis` returns one process-wide client (`functools.lru_cache`)
  with `max_connections = API_THREADPOOL_SIZE` instead of a client, and so a connection pool, per request.
- `backend/app/api/routers/auth.py`: `logout` and `extend_session` are plain `def`.
- `backend/app/api/routers/attachments.py`: unchanged. `upload_attachment` already stays `async` and calls
  `svc.store` through `run_in_threadpool` (TASK-135); the static test covers it.
- `backend/app/core/config.py`: `api_threadpool_size`, `db_pool_size`, `db_max_overflow`,
  `db_pool_timeout`, and a validator that refuses values below 1 (overflow below 0) and a thread limit above
  `db_pool_size + db_max_overflow`. Because it is a `Settings` validator, the API lifespan, the workers and
  the migration job all refuse a bad pair when they load settings.
- `backend/app/db/repositories/session.py`: the engine takes `pool_size`, `max_overflow`, `pool_timeout`.
- `backend/app/main.py`: the lifespan sets `anyio.to_thread.current_default_thread_limiter().total_tokens`
  and logs the four values.
- `backend/scripts/load_test.py`: new (see above); `backend/tests/api/test_no_blocking_in_async.py`,
  `backend/tests/core/test_pool_settings.py`: new; `backend/tests/test_log_redaction.py`: the one
  test that builds the engine from a stub settings object on in-memory SQLite now gives it the pool
  attributes and a file database (a `QueuePool` is not used by in-memory SQLite). OpenAPI unchanged.
- `docs/design-outputs/tests-specifications/TS-018-...md`: new, `in_review` (TC-018.1 to TC-018.4).

**Code defaults are 15 / 5 / 10 / 30 s, not the 40 / 20 / 20 / 10 s of step 4.** ADR-0022 says the defaults
equal today's effective behaviour "except for the invariant": today's 5 + 10 connections can serve at most
15 threads, so 15 is the largest thread limit that starts. The candidate values are applied only through
environment variables in the throw-away stack. This is still a default change in code (the thread limit
40 → 15) and is part of what the human is asked to approve below.

### Working tree, "after" (same load, same host, one worker, 300 s, 20 clients)

Runs were made in sequence on one stack; the data set grows with every run (about 4 000 entries and 2 000
attachments per run), so list and download get slower with each run and **throughput is not comparable
between runs**. The default configuration was therefore run twice, first and again after the others.

| Configuration (threads / DB pool + overflow / timeout) | Requests | 5xx | Transport errors | Worker kills | Pool-wait lines | p95 s: me / appts / entries / create / upload / download | Probe p95 / max |
|---|---|---|---|---|---|---|---|
| default 15 / 5 + 10 / 30 s (first run) | 41 448 | 0 | 0 | 0 | 0 | 0.168 / 0.186 / 0.212 / 0.216 / 0.368 / 0.633 | 0.061 / 0.230 |
| candidate 40 / 20 + 20 / 10 s | 34 704 | 0 | 0 | 0 | 0 | 0.188 / 0.212 / 0.254 / 0.243 / 0.467 / 0.797 | 0.079 / 0.968 |
| alternative 20 / 10 + 10 / 10 s | 30 008 | 0 | 0 | 0 | 0 | 0.217 / 0.244 / 0.298 / 0.284 / 0.555 / 0.920 | 0.084 / 0.241 |
| default 15 / 5 + 10 / 30 s (re-run, last) | 26 906 | 0 | 0 | 0 | 0 | 0.247 / 0.271 / 0.340 / 0.312 / 0.572 / 0.999 | 0.088 / 1.210 |
| proposal 20 / 20 + 20 / 10 s | 25 218 | 0 | 0 | 0 | 0 | 0.256 / 0.288 / 0.377 / 0.341 / 0.652 / 1.117 | 0.100 / 0.282 |

p50 of GET /me and of create entry: 0.087 / 0.127 s (first default) to 0.143 / 0.223 s (last run); the
slowest single request in any run was a 1 MiB upload at 4.5 s (a one-off per run, no 5xx; upload time is
excluded from AC 2). One download answered 4xx in the last run (1 of 1 463; cause not established, not a 5xx;
no access log was captured). Every p95 is far below the 3 s of SR-026 AC 1 and AC 2, with nothing near
the pools: no `QueuePool limit` line in any run.

### Reading of the measurement

1. **The event-loop change is what removes the failure.** Same load, same stack: 210 transport errors and 10
   worker kills before; 0 5xx, 0 errors, 0 kills after, with today's pool (5 + 10) and a 15-thread limit.
   The pool values do not decide AC 5 on this host.
2. **Larger pools bought no latency here.** The one worker is a single process on one core of the test
   host, so more than a handful of threads only add contention; the order of the p95s follows the run
   order (data growth), not the thread limit, so the data do not separate the configurations. They also
   show no queueing at any of them (no pool-wait line, probe p95 under 0.1 s), so the "second alternative
   if queueing is seen" of step 5 was not needed.
3. **What the pool must still cover is not in the closed-loop mix:** a failure audit row takes a second pooled
   connection in its own transaction (ADR-0016, PRB-058), so a request on a failure path holds two. With
   threads = connections, 20 such requests at once would need 40.

### Values proposed for the human (D-14), approved as D-24/D-25

`API_THREADPOOL_SIZE=20`, `DB_POOL_SIZE=20`, `DB_MAX_OVERFLOW=20` (up to 40 connections),
`DB_POOL_TIMEOUT=10` (Redis `max_connections` follows the thread limit: 20).

- 20 threads = the 20 clients of SR-026 AC 5 (D-3): every client can have a request in a thread, and the
  invariant gives the margin; 40 threads (the P-3 candidate) measured no better and cost memory and GIL
  contention.
- 20 + 20 connections = twice the threads, for the failure-audit second connection (point 3); well under
  PostgreSQL's `max_connections` of 100.
- 10 s pool timeout: a request that cannot get a connection fails in 10 s with a 500, well before Gunicorn's
  30 s kill of the whole worker (PRB-072). The timeout is reached only when the requests in flight on one
  worker exceed about threads + connections (a connection belongs to the request, not to the thread; QA round 1
  finding 1, PRB-081): then a bounded burst of 500s, not a worker kill.
- This exact combination ("proposal" row) ran with 0 5xx, 0 errors, 0 kills, p95 ≤ 1.12 s. Applied: the same
  four variables in `infra/docker-compose.yml` (backend `environment:`) and `infra/.env.example`; the
  `Settings` defaults stay 15 / 5 + 10 / 30 s (D-25).
- If the human prefers the P-3 candidate (40 / 20 + 20 / 10 s) it also passed; the alternative of
  keeping today's pool with 15 threads also passed but has no headroom for the 20 clients.

TASK-226 runs the final measurement with the approved values.

### PRB-072 (decision input for D-1)

PRB-072 **follows from PRB-009 and the unsized pools**, as its own hypothesis said. At `8028685` the
thresholds are 8 clients pass, 16 fail (3 worker kills), 20 fail (10 kills), reproducing the report; with
step 2 alone (default pools, 15 threads) the same 20-client load passes with no error and no pool wait.
The mechanism fits the thread dump: an `async` `get_current_user` waits for a pool connection on the loop
thread, and the requests that hold connections cannot release them (the dependency teardown also needs the
loop) until the 30 s pool timeout, by which time Gunicorn kills the worker. The `POST /accounts` route of
the report was not run; the load-test mix has create-entry, upload and consent writes, which collapsed
and now pass. So PRB-072 can join CR-006 under TASK-136 (D-1); its `resolves` link and the human's decision
are not mine to record.

### Verification

- `uv run pytest -q`: 1641 passed, 10 skipped, 0 failed (baseline 1622 passed / 10 skipped; 19 new tests);
  `python3 -m unittest discover -s infra/tests`: 178 OK. (The version 1.2 text recorded one failure in each,
  expected until the `infra/` wiring was approved; the wiring is in place and both pass.)
- `modules/dicom_viewer/tests`: 31 passed. `uv run ruff check .`: clean. `uv run mypy app`: clean (and clean on
  the new test and script files). `ruff format --check` clean on the touched files (three untouched files
  need formatting, as before). OpenAPI export unchanged.
- Negative controls: the static test and the slow-call test fail on `8028685` (TC-018.1, TC-018.2).
- TS-001 and TS-002 suites: unchanged and green.

### Open points

- SOUP-003, SOUP-008 and SOUP-013 relied-on text is edited (`in_review`, change-log lines added). ADD-005 and
  ADD-016 already describe this design and are consistent; ADD-016 does not mention the Redis pool size
  (ADD-006 or ADD-016 may carry one line).
- RISK-007's TASK-136 row is updated in round 2 (names PRB-072 and TS-018).
- `get_redis` used to open a Redis pool per request that was never closed explicitly; it is now one pool.
  Tests override `get_redis`, so none depended on the old shape.
- Not measured: the `POST /accounts` route of PRB-072; the 20-client load through the reverse proxy (PRB-078
  fixed in TASK-135; TASK-226); a run with a real think time (the mix is closed-loop, harsher than a clinic).
- The raw result files of every run are in the session scratchpad, not in the repository.

## QA review round 1 (qa-engineer, 2026-11-13) — APPROVED

Run by QA: `uv run pytest -q` 1641 passed, 10 skipped (object-store integration only), 0 failed; TS-001/TS-002
directories (`tests/auth`, `tests/authz`, `tests/api`, `tests/integration`, Docker up) 659 passed, 10 skipped;
`modules/dicom_viewer/tests` 31 passed; `ruff check .` clean; `mypy app` clean (and on the two new tests and
the script); `python3 -m unittest discover -s infra/tests` 178 OK; new tests 19 passed. `ruff format --check`:
the three files it reports (`tests/api/test_openapi_contract.py`, `tests/auth/test_session_service.py`,
`tests/test_env_example.py`) are unchanged against HEAD and fail the same check at HEAD and at `8028685`
(pre-existing). Negative controls: the static scan run on the `8028685` `app/api` names the seven calls of
TC-018.1 (on HEAD `f56216c` six: TASK-135 already moved the upload); the TASK-136 test file run against the
`8028685` app fails both the static test and `test_slow_db_call_does_not_block_unrelated_request`
(`/healthz waited 1.73 s`). `traceability-check` (TASK-136, TS-018, CR-006, PRB-009, PRB-072, SOUP-003/008/013,
SR-026, RISK-007, and one hop): 0 errors; warnings W5/W6 only (in-review targets of approved records).

Checked and found correct: no `async def` under `app/`, `app/modules` or `modules/` other than middleware,
error handlers, `healthz`, `require_csrf` and `upload_attachment` (none blocks); the lifespan sets the AnyIO
limiter on the serving loop; the invariant is a `Settings` validator; the deployed values and code defaults
match D-24/D-25. SOUP-013's "each request thread uses at most one Redis connection at a time" holds:
`_store_with_cap` issues every command through the WATCH pipeline's own connection, the other pipelines are
buffered (one connection at `execute`), no generator dependency uses Redis in its teardown, and redis-py 8.0.0
raises `MaxConnectionsError` (a `ConnectionError`) past `max_connections`. SOUP-003's anyio default of 40 tokens
(4.14.2) is accurate.

### Findings

1. **[MEDIUM] "Threads ≤ connections, so no request waits for a connection" is not true.** —
   `docs/soup/SOUP-008-sqlalchemy.md` relied-on paragraph ("every running request thread can hold a
   connection without waiting"), this record ("With threads ≤ connections it should never be reached"),
   `backend/app/core/config.py:90-97`, `infra/.env.example:114-116`, PRB-072 "Resolution", ADR-0022
   "Consequences" ("the PRB-072 shape cannot be configured silently"). A database connection is held by the
   *request* (its `get_db` session, from the first query until `get_db` exits after the response has been
   sent, FastAPI 0.138 `routing.py:131-137`), not by the thread: between dependency steps the request
   releases its thread token but keeps its connection, and a `StreamingResponse` download keeps it for the
   whole transfer. When the in-flight requests of one worker reach threads + connections, every thread can
   be blocked in a pool checkout while every connection belongs to a request waiting for a thread: all of
   them wait `DB_POOL_TIMEOUT` and answer 500. QA probe (FastAPI 0.138, the `get_db` → `get_current_user` →
   guard → handler shape, SQLAlchemy `QueuePool`): 4 threads / 4 connections fails at 8 concurrent requests,
   4 / 8 at 12 (11 passes), 15 / 15 (code defaults) at 30, 20 / 40 (deployed) passes 59 and fails at 70.
   SR-026 AC 5 (20 clients, one request each) is met, and the failure is a bounded 500 burst, not the
   worker kill of PRB-072. → Correct the wording in SOUP-008, this record, the two comments and PRB-072
   to the real bound (no pool timeout below threads + connections concurrent requests per worker; long
   downloads count against connections); raise a PRB for the residual (RISK-007; options: cap concurrent
   requests per worker below that bound with uvicorn `--limit-concurrency` or the proxy, or end the
   request transaction before streaming) and bring ADR-0022's consequence in line.
2. **[LOW] Stale text from version 1.2 in this record and the code comment.** — this record's "Proposed values
   for the human (D-14) — nothing in `infra/` … is changed yet" and "change the `Settings` defaults to the
   approved values" (contradicts D-25), "Verification" (1 failed / 1 failure, now 0), "Open points"
   (SOUP-003 edit refused, SOUP-008/013 not edited; all three are now edited); `backend/app/core/config.py:96-97`
   ("proposed … take effect only once approved"). → Mark them as superseded by 1.3 and update the comment.
3. **[LOW] RISK-007's TASK-136 row is stale** — `docs/risks/RISK-007-clinical-information-unavailable.md:82`
   still reads "PRB-072 if added" and verification "none yet (planned …)". → Name PRB-072 and TS-018
   (TC-018.1, .2, .4; TC-018.3 final run in TASK-226) when RISK-007 is next revised.
4. **[LOW] The static guard covers `app/api` only, with a closed deny list.** —
   `backend/tests/api/test_no_blocking_in_async.py:23`. Module routers (`app/modules`, `modules/*`) are not
   scanned, and a call such as `guard.is_module_enabled(...)` (a query, `8028685` `deps.py:152`) is not on the
   list; today nothing is missed. → Scan `app/` and `modules/` as well, or record the scope in TC-018.1.

### Download 4xx (1 of 1 463 in the last run): a real, pre-existing defect, not a script artefact

The script downloads only the attachment its own client uploaded under its own entry and deletes nothing,
so no other client or deletion can race it; consent is granted once at setup and the session cannot expire
in 300 s. The likely cause is that **`get_db` commits after the response has been sent**: FastAPI 0.138 runs
the teardown of a `Depends` with `yield` (default scope "request") after `await response(...)`
(`fastapi/routing.py:131-137`), so the client receives the upload's 201 before the attachment row is
committed, and a download issued at once can get 404 from `_authorized_attachment`. QA probe on a real
uvicorn server, same FastAPI version and `get_db` shape: "POST 201 → immediate GET sees committed row:
False; after 0.3 s: True". The 4xx itself was not captured (no access log), so the status and the cause of
that one request are not proven; this is the only 4xx path the script can reach that fits a one-off. Not
caused by TASK-136 (FastAPI 0.138 since TASK-001). It also means a commit failure after a 201 loses a write
the user saw acknowledged (clinical entry, attachment metadata), and a download's SUCCESS audit row is
committed only after the transfer. → Raise a PRB (problem-report-resolution; RISK-007 and the clinical-data
risks); the fix is `Depends(get_db, scope="function")` or an explicit commit before the handler returns.

## Round 2 (Software Developer, 2026-11-13) — wording and records only, no behaviour change

Response to QA round 1 findings 1-3 and the download 4xx:

1. The false claim "threads ≤ connections, so no request waits for a connection" is corrected in SOUP-008,
   this record, `backend/app/core/config.py`, `infra/.env.example`, PRB-072 "Resolution", CR-006 D-24 and ADR-0022
   "Consequences". The real limit: a connection belongs to the request (its `get_db` session, held between
   dependency steps, through a whole streaming download and until `get_db` exits after the response is sent), so
   one worker serves about **threads + connections** concurrent requests; beyond that the requests wait
   `DB_POOL_TIMEOUT` and answer 500 (`sqlalchemy.exc.TimeoutError`), a bounded burst, not the PRB-072 worker
   kill. QA probe: 4 / 4 fails at 8; 4 / 8 passes 11, fails 12; 15 / 15 (code defaults) fails at 30; 20 / 40
   (deployed) passes 59, fails at 70. SR-026 AC 5 (20 clients) is still met; the approved values stand.
   Residual raised as PRB-081.
2. Version 1.2 text superseded: the "nothing in `infra/` is changed yet" heading, "change the `Settings`
   defaults", the "1 failed" verification and the open points about the SOUP edits were rewritten above.
3. RISK-007's TASK-136 row names PRB-072 and TS-018 (TC-018.1 to TC-018.4).
4. The download 4xx is raised as PRB-080 (request transaction commits after the response is sent).

## QA review round 2 (qa-engineer, 2026-11-13) — APPROVED

Run by QA: `uv run pytest -q` 1641 passed, 10 skipped, 0 failed; `ruff check .` clean; `mypy app` clean (134
files); `python3 -m unittest discover -s infra/tests` 178 OK. `traceability-check` (TASK-136, TS-018, CR-006,
PRB-072, PRB-080, PRB-081, RISK-007, SOUP-008): 0 errors, 0 warnings; with one hop (110 records) 0 errors,
W5 (approved records pointing at the in-review RISK-007 and SOUP items) and W6 (CR-002/TASK-175 to obsolete
SOUP-022/023) only.

Checked: findings 1-3 are fixed in SOUP-008, `config.py`, `infra/.env.example`, PRB-072, CR-006 D-24, ADR-0022,
RISK-007 (1.13, `in_review`) and this record; no remaining "no request waits" claim in SOUP-003/008/013, TS-018,
PRB-009, PRB-072, ADR-0022, RISK-007, CR-006 or `app/`. SOUP-013 and TS-018's Redis wording ("a worker thread
never finds the pool empty") is correct (one Redis connection per command). Since round 1 only `config.py` (a
comment; the validator and defaults are unchanged) and `infra/.env.example` (comment) changed under `backend/`
and `infra/`. PRB-080 and PRB-081 follow the PRB body contract (Investigation with references, Safety evaluation
with criticality and notification, Resolution "not started", `links: []`); FastAPI 0.138.0 in every lock since the
first, `routing.py:131-137` and `params.py:749` (`scope`) confirmed. Probes re-run: 4/4 passes 7, fails 8; 4/8
passes 11, fails 12; 15/15 passes 29, fails 30; 20/40 passes 59, **fails 60**; commit-order probe "POST 201 ->
immediate GET False; after 0.3 s True". TS-018 unchanged since its round 1 approval; stays `approved`.

### Findings (not blocking)

1. **[LOW] The 20 / 40 failure point is 60, not 70.** — PRB-081 "Observed" table (row "20 / 40 (deployed)"),
   CR-006 D-24 ("59 pass, 70 fail with 20 / 40"), this record's round 2 note 1. The QA round 1 text said "fails at
   70"; re-measured, 60 concurrent requests (= threads + connections) already give 20 × 500. → Change "70 (not run
   between)" / "70 fail" to "60" when these records are next revised.
2. **[LOW] PRB-080 and PRB-081 cite their probe scripts in a session scratchpad** (`.../scratchpad/pool_probe.py`,
   `commit_order_probe.py`), which does not survive the session, so the investigation evidence is not
   reproducible from the repository. → Inline the probe's shape (the 30-line app and the command) in each PRB's
   Investigation, or have the resolving CR turn them into tests.
3. Round 1 LOW 4 (static guard scope) stands as accepted.

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect). Re-based on SR-026 AC 5 (D-3) and ADR-0022: line
  numbers refreshed (PRB-009's `:126,198` sites no longer exist; `routers/auth.py` `logout` and
  `extend_session` added), pool settings with a start-up invariant, load-test baseline first and the
  pool-value proposal for the human (D-14), PRB-072 decision input (D-1). `mitigates` RISK-007 added.
- 1.2 (2026-11-13) — Build stage (Software Developer): implementation record, load-test "before" at `8028685`
  and "after" on the working tree, pool values proposed for D-14, PRB-072 decision input. Stays `draft`: the pool
  values and the `infra/` wiring await the human.
- 1.3 (2026-11-13) — Pool values approved by the human (CR-006 D-24 to D-26); `infra/` wiring added; the two infra
  tests now pass; PRB-009 and PRB-072 resolved. `draft` to `in_review`.
- 1.4 (2026-11-13) — QA review round 1: APPROVED (1 MEDIUM, 3 LOW, one pre-existing defect for a new PRB; see "QA review round 1"); checkboxes ticked; `in_review → approved`.
- 1.5 (2026-11-13) — round 2: wording corrections from QA round 1 findings 1–3 (real concurrency limit, stale 1.2 text, RISK-007 row); PRB-080 and PRB-081 raised. `approved → in_review`.
- 1.6 (2026-11-13) — QA review round 2: APPROVED (2 LOW: 20 / 40 fails at 60, not 70; probe scripts not in the repository). `in_review → approved`.
