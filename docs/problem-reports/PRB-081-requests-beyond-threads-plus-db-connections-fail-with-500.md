---
id: "PRB-081"
type: problem-report
title: "Concurrent requests beyond threads plus database connections per worker fail with 500"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
criticality: minor
links: []
tags: ["performance","hazard:availability","found-in:TASK-136-qa"]
---

# PRB-081 — Concurrent requests beyond threads plus database connections per worker fail with 500

## Observed

Found by QA in round 1 of TASK-136 (2026-11-13) while testing the claim "threads <= connections, so no request
waits for a connection". QA probe (FastAPI 0.138, the `get_db` -> `get_current_user` -> guard -> handler shape,
SQLAlchemy `QueuePool`; `/private/tmp/claude-501/-Users-carlos-santiago--claude-spares-spare-VaVpDG/8f1dc588-ebf1-4b95-82da-0fbffafee938/scratchpad/pool_probe.py`,
session scratchpad, not in the repository):

| Threads / connections | Concurrent requests that pass | First count that fails |
|---|---|---|
| 4 / 4 | 7 | 8 |
| 4 / 8 | 11 | 12 |
| 15 / 15 (code defaults) | 29 | 30 |
| 20 / 40 (deployed) | 59 | 60 (QA round 2 re-run) |

The failing requests wait `DB_POOL_TIMEOUT` and answer 500 (`sqlalchemy.exc.TimeoutError`).

## Impact

One API worker serves about threads + connections concurrent requests, not threads. Beyond that, a burst of
requests answers 500 after the pool timeout (10 s deployed) while the others complete; the worker is not killed
(PRB-072 is not reproduced) and recovers when the burst ends. SR-026 AC 5 (20 clients, one request each) is met
with wide margin. Long downloads count against the connections for the whole transfer.

## Investigation

A database connection belongs to the request, not to the thread: the `get_db` session takes its connection at
the first query and keeps it until `get_db` exits after the response has been sent (`fastapi/routing.py:131-137`,
see PRB-080). Between dependency steps a request releases its thread token but keeps its connection, and a
`StreamingResponse` keeps it through the transfer. When the in-flight requests reach threads + connections,
every thread can be blocked in a checkout while every connection belongs to a request waiting for a thread: all of
them wait the pool timeout. The start-up invariant (threads <= connections, ADR-0022) bounds the threads only.
The earlier wording "no request waits for a connection" was wrong and is corrected in SOUP-008, TASK-136,
`config.py`, `.env.example`, PRB-072 and ADR-0022.

Candidate fixes:

- Cap concurrent requests per worker below the bound: uvicorn `--limit-concurrency` (the excess answers 503
  at once) or a proxy limit.
- End the request transaction before streaming a download (see PRB-080's `scope="function"`), so a long transfer
  does not hold a connection.

## Safety evaluation

Availability only (RISK-007): no data is disclosed or altered; a request that fails with 500 changes nothing.
The load needed (more than 59 concurrent requests on one deployed worker) is beyond SR-026 AC 5 and a clinic's
normal use. Criticality **minor**: a bounded burst of 500s with self-recovery. No release exists (CR-004 A-1), so
no notification is needed. The human sets the final criticality.

## Resolution

Not started. Out of CR-006 scope until the human decides.

## Version history

- 1.0 (2026-11-13) — Created from TASK-136 QA round 1 finding 1. `open`, `minor`.
