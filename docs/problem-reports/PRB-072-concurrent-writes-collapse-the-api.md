---
id: "PRB-072"
type: problem-report
title: "Twenty parallel writes on a healthy stack answer 502 and the API worker is killed"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-07"
updated: "2026-11-07"
criticality: major
links: []
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

**Root cause not established.** The thread dump shows one waiting request, not why the pool does not
drain. What is known from the code:

- `backend/app/db/repositories/session.py:16` calls `create_engine` with no pool settings, so the pool is the
  default 5 + 10 overflow with a 30 s `pool_timeout`. Gunicorn's `--timeout` is not set either, so it is the
  default 30 s (`backend/Dockerfile:24`).
- `get_current_user` is `async def` and does the synchronous query at `deps.py:81` on the event-loop thread.
  `get_session` (`deps.py:43-62`) does synchronous Redis the same way. This is PRB-009 (open, major, TASK-136
  draft).
- `create_account` (`backend/app/api/routers/accounts.py:46`) and `get_db` are synchronous, so they run in the
  threadpool, and `get_db` keeps its connection until it exits (`session.py:24-34`).

**Hypothesis, not tested:** once 15 connections are held, the next request blocks the event loop at
`deps.py:81`. The requests holding connections cannot finish while the loop is blocked, so none is
returned. The loop stays blocked for up to the 30 s pool timeout, the worker stops sending its heartbeat,
and gunicorn kills it at 30 s. This fits the 8-clients-pass, 20-clients-fail result and predicts a threshold
at 16 concurrent requests per worker. If it holds, this PRB is a consequence of PRB-009 and the pool sizes.
Failure audit rows, which take a second pooled connection (ADR-0016, PRB-058), may add to the pressure. Each
of these needs a measurement in the CR that takes this PRB.

## Safety evaluation

Availability only: no data is disclosed or altered; a write in flight is rolled back or never started.
Contributes to RISK-007 and to the SR-026 budgets. Criticality **major**: a small burst, within what a
clinic's normal use or an authenticated client can produce, stops the whole API. Not `critical`: the
service returns after the worker restarts, and no wrong clinical information is shown. No release exists
(CR-004 A-1), so no notification is needed. The human sets the final criticality.

## Resolution

Not fixed. Known anomaly outside CR-004 (D-18); a separate CR comes later. It has no `resolves` link yet.

## Source

TASK-206 QA review, "Pre-existing issues"; human decision 2026-11-07 (CR-004 D-18).

## Version history

- 1.0 (2026-11-07) — Created from the TASK-206 QA review. `open`, `major`.
