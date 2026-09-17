---
id: "PRB-009"
type: problem-report
title: "Async dependencies and handlers perform sync IO on the event loop"
status: open
criticality: major
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
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

TASK-136 (draft) — make those handlers and dependencies sync so Starlette runs them in the threadpool, or make the IO genuinely async.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding B.
