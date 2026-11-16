---
id: "PRB-009"
type: problem-report
title: "Async dependencies and handlers perform sync IO on the event loop"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-15"
criticality: major
links: []
tags: ["performance", "hazard:availability"]
---

# PRB-009 — Async dependencies and handlers perform sync IO on the event loop

## Observed

`api/deps.py:44,71,126,198` and `api/routers/attachments.py` declare `async def` while doing synchronous Redis, SQLAlchemy and boto3 IO, so blocking calls run on the event loop instead of the threadpool — including on every authenticated request.

## Impact

Throughput collapses under concurrency and SR-026 budgets are missed; a slow database stalls unrelated requests.

## Safety evaluation

Contributes to RISK-007 (clinical information unavailable).

## Resolution

TASK-136 (CR-006, ADR-0022), Build stage 2026-11-13, working tree, not committed. The five `async def`
dependencies and routes that called Redis, SQLAlchemy and the audit service on the event loop
(`get_session`, `get_current_user`, `require_module_enabled._dependency`, `logout`, `extend_session`) are plain
`def`; the upload stays `async` and uses `run_in_threadpool`. A static test (TS-018 TC-018.1) and a slow-call
test (TC-018.2) guard it and fail on the pre-fix code.

Evidence (TASK-136 "Implementation record"): on the pre-CR-006 commit `8028685`, 20 concurrent clients on one
worker lose 210 of 456 requests and Gunicorn kills the worker 10 times in 5 minutes; 8 clients pass. On the
fixed tree the same load gives 0 × 5xx, 0 transport errors and 0 worker kills with today's pool (5 + 10) and
with four other thread and pool sizes, every p95 under 1.2 s.

The pool and thread values were approved by the human on 2026-11-13 (CR-006 D-24) and are wired in `infra/`
(`docker-compose.yml`, `.env.example`). CR-006 carries the `resolves` link. TASK-226 repeats the 20-client
measurement through the reverse proxy with the deployed values at the end of the CR.

**TASK-226 verification (2026-11-15):** the 20-client run through the reverse proxy with the deployed values (20 / 20 / 20 / 10), 300 s, one worker: 29 601 requests, 0 × 5xx, 0 transport errors, 0 worker kills, p95 at most 1.05 s for every operation (TS-018 TC-018.3).

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding B.

## Version history

- 1.0 (2026-09-17) — Created.
- 1.1 (2026-11-13) — Resolved by TASK-136 (CR-006): Resolution recorded, pool values approved (D-24). `resolved`, `major`.
- 1.2 (2026-11-15) — TASK-226: final load run recorded. Stays `resolved`.
