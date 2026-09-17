---
id: "PRB-012"
type: problem-report
title: "Retention sweep leaks database sessions and never retries"
status: open
criticality: major
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["correctness", "hazard:availability"]
---

# PRB-012 — Retention sweep leaks database sessions and never retries

## Observed

`workers/retention_tasks.py:82-92` reassigns `db = next(get_db())` per dataset failure without closing the previous session, so the `finally` closes only the last one. `erase_expired_anonymized_datasets` declares `max_retries=3` and a retry delay but has neither `autoretry_for` nor a `self.retry()` call, so it never retries.

## Impact

Pooled connections leak on every failing sweep, and expired data is not erased when a transient error occurs (SR-024).

## Safety evaluation

Contributes to RISK-007 (unavailability, pool exhaustion) and RISK-008 (retention not executed).

## Resolution

TASK-141 (draft) — use a context-managed session per dataset and align retry configuration with the other tasks.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding H.
