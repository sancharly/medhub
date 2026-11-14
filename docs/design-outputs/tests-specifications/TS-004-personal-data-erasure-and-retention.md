---
id: TS-004
type: test-specification
title: Personal data erasure and retention verification
status: approved
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-14"
links:
  - target: SR-024
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-004 — Personal data erasure and retention verification

## Scope

Software requirements covered: SR-024.
Software items under test: SI-IDENTITY, SI-WORKER, SI-PERSIST.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24) with `frontend/package-lock.json`.
Unit and service tests run with no external services (in-memory repositories; frozen clock for deadlines). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-004.1 | SR-024 | `backend/tests/identity/test_erasure.py` | Deletion anonymizes the account and re-keys clinical data into the anonymized dataset | No identifying field survives; clinical rows are not dropped |
| TC-004.2 | SR-024 | `backend/tests/api/test_anonymized_retrieve.py` | Retrieval with the correct code works before the deadline and is refused after it | Only the salted hash of the code is stored |
| TC-004.3 | SR-024 AC 4 | `backend/tests/workers/test_retention_erase.py` | The scheduled job erases datasets past the five-year deadline | Erasure recorded; datasets before the deadline untouched |
| TC-004.4 | SR-024 AC 6 | `backend/tests/identity/test_erasure.py`: `test_erasure_enqueue_failure_raises_retryable_problem_and_keeps_sessions`; `backend/tests/api/test_erasure_rollback.py`: `test_erasure_enqueue_failure_rolls_back_and_returns_503` (control: `test_erasure_with_a_working_broker_commits_before_the_response`); `backend/tests/workers/test_celery_results.py::test_enqueue_with_unreachable_redis_raises` | With the broker raising, `DELETE /accounts/{id}` answers 503 `application/problem+json`, type `erasure-notification-unavailable`, with `Retry-After`; the account row, its PII and password hash, its sessions are unchanged; no anonymized dataset and no `ACCOUNT_DELETED` / `DATA_ANONYMIZED` audit row exists; the request transaction (`DbSession`, `scope="function"`, ADR-0023) rolled back before the response started. Converse case (enqueued, then the commit fails): a code that matches no dataset is e-mailed, which is harmless and not tested | Both tests pass; moving the enqueue after `invalidate_all`, or swallowing the failure, fails them (negative control, TASK-141 "Verification results") |
| TC-004.5 | SR-024 AC 5 | `backend/tests/workers/test_retention_tasks.py`: `test_sweep_failing_dataset_closes_every_session`, `test_sweep_retries_at_most_three_times_then_logs_count`, `test_sweep_dataset_failing_once_then_succeeding_is_erased`, `test_sweep_never_deletes_before_deadline_across_retries`; `backend/tests/workers/test_retention_erase.py::test_erase_per_dataset_failure_isolation` | A dataset whose delete raises is rolled back alone; sessions opened = sessions closed; later datasets are erased; the task runs once and retries 3 times (4 runs) and then logs the failed count; a dataset that fails once is erased by the retry; a dataset whose deadline is in the future is never deleted, in any run | All listed tests pass |

## Acceptance criteria (class B unit level, §5.5.3)

- Boundary: retrieval exactly at the deadline, one second before and one second after.
- Fault handling: a failure mid-sweep must not leave a partially erased dataset or leak a session (TC-004.5).
- Fault handling: an erasure whose code e-mail cannot be enqueued is rolled back as a whole and reports a retryable error (TC-004.4).

## Notes

PRB-012 (session leak and missing retry in the sweep; TC-004.5, TASK-141) and TASK-116 (re-keying) are open; the re-keying criterion is therefore specified here but not yet verified. The sweep tests use an in-memory fake of the session (counting opens and closes), not PostgreSQL; the erasure rollback test (TC-004.4) uses PostgreSQL through testcontainers and therefore a working Docker daemon.

## Version history

- 1.1 (2026-10-30): approved baseline.
- 1.2 (2026-11-14): TASK-141 (CR-006). TC-004.4 (erasure rolled back when the code e-mail cannot be enqueued, SR-024 AC 6) and TC-004.5 (sweep isolation, session release, at most 3 retries, SR-024 AC 5) added; TC-004.3 names AC 4; fault-handling criteria extended. Approval cleared, `in_review`.
- 1.2 (2026-11-14): QA review of TASK-141 (round 1): `approved` (status only; content unchanged).
