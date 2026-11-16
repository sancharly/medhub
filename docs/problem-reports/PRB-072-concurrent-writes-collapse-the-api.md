---
id: "PRB-072"
type: problem-report
title: "Twenty parallel writes on a healthy stack answer 502 and the API worker is killed"
status: resolved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-11-07"
updated: "2026-11-15"
criticality: major
links:
  - target: "PRB-009"
    relation: relates_to
tags: ["performance", "hazard:availability", "found-in:TASK-206-qa"]
---

# PRB-072 — Twenty parallel writes on a healthy stack answer 502 and the API worker is killed

## Observed

Found by QA while reviewing TASK-206 (2026-11-07, committed as 75fbd6d). 20 parallel `POST /accounts` on a
healthy stack all answered 502, and gunicorn logged `WORKER TIMEOUT`. It reproduced with HEAD's
`backend/app/main.py` without `set_default()` and with `task_ignore_result=True`, so neither TASK-206 nor
TASK-207 causes it. A thread dump showed a request waiting on the SQLAlchemy pool checkout at
`backend/app/api/deps.py:81`. With `-w 3`, 20 of 120 parallel requests answered 502. 8 parallel clients ran at
about 100 requests/s without error.

## Impact

A modest burst of concurrent requests makes every request in flight fail, and the worker that served them
is killed. With the default single worker (`backend/Dockerfile:24` has no `-w`), all users, not only the ones
writing, lose the API until it restarts. Clinical information is unavailable for that time (RISK-007). QA
observed `POST /accounts` only; other routes were not measured.

## Investigation

**Root cause established (TASK-136, 2026-11-13).** PRB-072 is a consequence of PRB-009 (`async def`
dependencies doing synchronous SQLAlchemy and Redis IO on the event loop) and of unsized pools (SQLAlchemy 5 + 10,
30 s `pool_timeout`, Gunicorn 30 s worker timeout, redis-py unbounded). Once the connections are held, the next
request blocks the loop at `get_current_user` waiting for a checkout; the requests that hold connections cannot
release them while the loop is blocked, so the loop stays blocked until the pool timeout, the worker misses its
heartbeat and Gunicorn kills it.

Measured on the pre-CR-006 commit `8028685` with the TASK-136 load-test script: 8 clients pass, 16 fail
(3 worker kills), 20 fail (10 kills; 456 requests, 210 transport errors). This reproduces the threshold the
hypothesis predicted. With the event-loop fix alone (default pools, 15 threads) the same 20-client load passes
with no error and no pool wait. `POST /accounts` was not run directly; the mix has create-entry, upload and
consent writes, which collapsed before and pass now.

## Safety evaluation

Availability only: no data is disclosed or altered; a write in flight is rolled back or never started.
Contributes to RISK-007 and to the SR-026 budgets. Criticality **major**: a small burst, within what a
clinic's normal use or an authenticated client can produce, stops the whole API. Not `critical`: the
service returns after the worker restarts, and no wrong clinical information is shown. No release exists
(CR-004 A-1), so no notification is needed. The human sets the final criticality.

## Resolution

Resolved by TASK-136 (CR-006, D-26; ADR-0022): the five `async` dependencies and routes that did synchronous IO
are plain `def` (see PRB-009), the thread limit, database pool and Redis pool are sized and checked at start-up
(threads <= pool + overflow; this bounds the threads, not the requests: a connection belongs to the request, so a worker
serves about threads + connections concurrent requests and answers 500 beyond that, a bounded burst and not a worker
kill, PRB-081), and the deployed values are `API_THREADPOOL_SIZE=20`, `DB_POOL_SIZE=20`,
`DB_MAX_OVERFLOW=20`, `DB_POOL_TIMEOUT=10` (CR-006 D-24, approved by the human 2026-11-13).

Verification: `backend/scripts/load_test.py` against a started stack, 20 concurrent clients on one worker: 0 5xx,
0 transport errors, 0 worker kills, p95 0.17-1.12 s across configurations (TASK-136 "Implementation record"); tests
TC-018.1 to TC-018.4 in TS-018 and `backend/tests/core/test_pool_settings.py`. The final run through the reverse
proxy with the approved values is TASK-226.

**TASK-226 verification (2026-11-15):** the failure is gone. On the branch head, through the reverse proxy, 20 clients on one worker ran 300 s with 0 × 5xx, 0 transport errors (the captured backend log was empty, 0 bytes, so no `WORKER TIMEOUT` or `QueuePool limit` line could be counted; the verdict rests on 0 × 5xx and 0 transport errors) (before, on `8028685`: 210 transport errors and 10 worker kills in 456 requests). TS-018 TC-018.3.

## Source

TASK-206 QA review, "Pre-existing issues"; human decision 2026-11-07 (CR-004 D-18).

## Version history

- 1.0 (2026-11-07) — Created from the TASK-206 QA review. `open`, `major`.
- 1.1 (2026-11-13) — Root cause established, resolved by TASK-136 (CR-006 D-26). `resolved`, `major`.
- 1.2 (2026-11-13) — TASK-136 round 2: Resolution wording corrected (the invariant bounds threads, not requests; residual limit raised as PRB-081). Stays `resolved`.
- 1.3 (2026-11-15) — TASK-226: final load run recorded; the 8-ok / 20-fail pattern no longer reproduces. Stays `resolved`.
- 1.4 (2026-11-15) — TASK-226 round 2 (QA L-4): the log counts qualified. Stays `resolved`.
