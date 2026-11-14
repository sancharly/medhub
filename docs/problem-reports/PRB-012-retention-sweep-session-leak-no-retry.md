---
id: "PRB-012"
type: problem-report
title: "Retention sweep leaks database sessions and never retries"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-14"
criticality: major
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

Resolved by TASK-141 under CR-006 (SR-024 AC 5): `workers/retention_tasks.py` lists the expired ids in one session, then uses one session and transaction per dataset, closed on every path; a failure is rolled back and counted; the deadline is re-checked in the dataset's session; when any dataset failed the task calls `self.retry(countdown=300 * 2**retries)` up to `max_retries=3`, then logs the failed count at ERROR without personal data (SR-043). Verified by TS-004 TC-004.5 and TS-017 TC-017.8.

QA verification (TASK-141 round 1, 2026-11-14): the four sweep tests and the adapted isolation test pass; mutants (no `close()`, no rollback, no deadline re-check, one retry too many) are each killed; a probe on real PostgreSQL erased a dataset failing twice on the second retry with `pool.checkedout() == 0`. Backend suite 1670 passed, `mypy` and `ruff check` clean. Fixed and verified in the working tree, so `resolved`; `closed` once confirmed through a shipped release.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding H.
## Version history

- 1.0 (2026-09-17) — Created from the July 2026 code review. `open`.
- 1.1 (2026-11-14) — QA review of TASK-141 (round 1): APPROVED; Resolution names the fix and its evidence; `open → resolved` (CR-006 holds the `resolves` link).
