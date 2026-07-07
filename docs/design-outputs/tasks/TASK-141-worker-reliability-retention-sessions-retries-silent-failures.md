---
id: "TASK-141"
type: task
title: "Worker reliability: retention session handling, retry parity, silent enqueue failures"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-024"
    relation: relates_to
  - target: "SR-035"
    relation: relates_to
  - target: "TASK-036"
    relation: relates_to
  - target: "TASK-124"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:medium"]
---

- **Phase:** Review 2026-07 — backend security/robustness
- **Depends on:** —
- **Branch:** `fix/worker-reliability`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — findings H + I (Medium)

## Objective

Three worker-reliability defects:

1. **DB session leak** — `workers/retention_tasks.py:82-92`: on per-dataset failure the loop
   reassigns `db = next(get_db())` without closing the previous session; the `finally: db.close()`
   only closes the last one. N failures leak N-1 pooled connections per sweep.
2. **Retry parity** — `erase_expired_anonymized_datasets` declares `max_retries=3,
   default_retry_delay=300` but has no `autoretry_for` and never calls `self.retry()`, so it never
   retries at all; every other task uses `autoretry_for=(Exception,)` + backoff.
3. **Silent enqueue swallow** — `identity/lifecycle.py:57` and `appointments/service.py:71` wrap
   `.delay()` in `except Exception: pass` with **no log**: a dead broker silently drops
   session-kill propagation and appointment notifications (SR-035).

## Implementation detail

- Restructure the retention loop with per-dataset `try/except` around a context-managed session, or
  `db.close()` before reassignment; assert pool checkout count in a test.
- Add `autoretry_for=(Exception,)`, `retry_backoff=True` to the retention task, matching
  `email_tasks`/`session_tasks`.
- Replace both `pass` bodies with `logger.warning("enqueue failed", exc_info=True)` (+ audit row for
  the notification path if required by SR-035 acceptance criteria). Keep best-effort semantics.

## Acceptance criteria

- [ ] A sweep with 3 induced per-dataset failures leaves zero leaked checked-out connections.
- [ ] Retention task auto-retries on transient exception (unit test with raising session).
- [ ] Broker-down enqueue failure emits a warning log; request still succeeds.

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Worker tests extended for all three behaviors
- [ ] Traceability rows updated (SR-024/SR-035 references)
