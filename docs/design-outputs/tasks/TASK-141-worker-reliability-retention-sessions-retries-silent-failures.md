---
id: "TASK-141"
type: task
title: "Retention sweep isolation and retries; erasure rolled back when its code e-mail cannot be queued"
status: draft
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-13"
links:
  - target: "SR-024"
    relation: implements
  - target: "SR-043"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "RISK-008"
    relation: mitigates
  - target: "RISK-009"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-012"
    relation: relates_to
  - target: "PRB-013"
    relation: relates_to
  - target: "ADD-008"
    relation: relates_to
  - target: "ADD-017"
    relation: relates_to
  - target: "TS-004"
    relation: relates_to
  - target: "SR-035"
    relation: relates_to
  - target: "TASK-207"
    relation: relates_to
  - target: "TASK-036"
    relation: relates_to
  - target: "TASK-124"
    relation: relates_to
tags: ["phase:review-2026-07", "cr:CR-006", "control:design", "control:protective"]
---

# TASK-141 — Retention sweep isolation and retries; erasure rolled back when its code e-mail cannot be queued

- **Software item / unit:** SI-WORKER `workers/retention_tasks.py` (ADD-017); SI-IDENTITY
  `identity/erasure.py` `ErasureService._erase` and its router (ADD-008).
- **PRBs:** PRB-012; PRB-013 (remainder after TASK-207: the D-5 policy). PRB-013 is folded into this task
  rather than given its own, because its only remaining change is the erasure path, whose verification
  (TS-004) and records (RISK-008, SR-024) this task already carries. **CR:** CR-006 (D-5, D-11).
- **Depends on:** none (parallel).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** M (`backend/app/workers/retention_tasks.py`, `backend/app/identity/erasure.py`, the erasure route
  in `backend/app/api/routers/` and `backend/app/api/errors.py` if a new problem class is needed; tests
  `backend/tests/workers/test_retention_tasks.py`, `backend/tests/identity/test_erasure.py`; generated
  OpenAPI and frontend types if the erasure route gains a 503 response; records TS-004, TS-017, ADD-008,
  ADD-017, SOUP-014 relied-on text).

## Objective

- **SR-024 AC 5 (PRB-012):** the retention sweep isolates a failure to its dataset, releases every session it
  opens, retries a transient failure at most 3 times, never skips an expired dataset silently, and logs the
  failed count without personal data (SR-043). Today `retention_tasks.py:92` reassigns `db = next(get_db())`
  without closing the previous session, and `:22-26` declare `max_retries=3` with no `autoretry_for` and no
  `self.retry()`.
- **SR-024 AC 6 (PRB-013, D-5, D-11):** an erasure whose retrieval-code e-mail cannot be enqueued fails and is
  rolled back as a whole; the request never reports success; the requester gets a retryable error. Today
  `erasure.py:135-142` logs a WARNING and returns success. Activation and appointment paths stay best effort
  with the TASK-207 WARNING (D-5), not changed here.

## Implementation detail

- **Retention:** one session per dataset in a `with` block (or `try/finally: db.close()`); per-dataset
  `try/except` that counts failures and continues; a dataset is deleted only if `retention_deadline < now`
  re-checked inside its own session (idempotent, cause 7). If any dataset failed with a transient error,
  `raise self.retry(countdown=...)` after the loop, bounded by `max_retries=3`; after the last retry the task
  logs the failed count (an integer, no dataset content) at ERROR. Match the backoff style of `email_tasks`.
- **Erasure:** move the enqueue **before** `self._session_svc.invalidate_all(account_id)` (so a failed
  enqueue leaves sessions and account unchanged), and raise a retryable problem on failure (HTTP 503,
  `Retry-After`, a problem type `erasure-notification-unavailable`, no address or code in the message). The
  exception propagates through the request's transaction, so the anonymized dataset, the PII severance and
  the two SUCCESS audit rows are rolled back. The converse case (enqueued, then the commit fails) sends a code
  that matches no dataset: harmless, noted in TS-004.
- The 503 is an additive response on the erasure route: regenerate `backend/openapi/openapi.json` and the
  frontend types (CLAUDE.md contract steps); this is a contract change the plan names for the human.

## Tests (write first)

- `test_sweep_failing_dataset_closes_every_session` (SR-024 AC 5): a dataset whose delete raises; count
  sessions opened = closed; later datasets erased.
- `test_sweep_retries_at_most_three_times_then_logs_count` (SR-024 AC 5, SR-043): transient error each run;
  `retry` called 3 times; final ERROR log holds the count and no dataset field.
- `test_sweep_dataset_failing_once_then_succeeding_is_erased` (SR-024 AC 5).
- `test_sweep_never_deletes_before_deadline_across_retries` (SR-024 AC 4, AC 5; RISK-008 cause 7).
- `test_erasure_enqueue_failure_rolls_back_and_returns_503` (SR-024 AC 6): broker raises; response 503
  problem; account row, PII and sessions unchanged; no anonymized dataset; no SUCCESS audit row.
- `test_erasure_enqueue_failure_logs_warning_without_personal_data` (SR-043; the RISK-009 erasure-site
  log-capture test).
- Recorded in TS-004 (1.1 → 1.2, approval cleared) and TS-017 (failed-count log).

## Acceptance criteria

- [ ] SR-024 AC 5: isolation, every session released, ≤ 3 retries, failed count logged without personal data.
- [ ] SR-024 AC 6: enqueue failure → retryable error, nothing committed, account unchanged.
- [ ] SR-024 AC 1 to AC 4 tests unchanged and green.

## Definition of Done

- [ ] `ruff`, `mypy`, backend suite green; OpenAPI and types regenerated and committed if the 503 is added
- [ ] TS-004, TS-017, ADD-008, ADD-017 consistent; `traceability-check` no error for this record

## Version history

- 1.1 (2026-09-17) — Added `mitigates` RISK-007, RISK-008, RISK-009 (TASK-147).
- 1.2 (2026-10-21) — Tagged `control:design`, `control:protective`.
- 1.3 (2026-11-13) — CR-006 Plan stage (Software Architect). Re-based on SR-024 AC 5 and AC 6 (D-5, D-11);
  PRB-013 narrowed to the erasure path (the two silent sites were logged by TASK-207); SR-035 changed from
  `implements` to `relates_to` (its paths stay best effort); `implements` SR-043 added (failed-count log).
