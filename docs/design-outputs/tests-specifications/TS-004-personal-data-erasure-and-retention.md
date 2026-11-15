---
id: TS-004
type: test-specification
title: Personal data erasure and retention verification
status: approved
version: "1.4"
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
| TC-004.4 | SR-024 AC 6 | `backend/tests/identity/test_erasure.py`: `test_erasure_enqueue_failure_raises_retryable_problem_and_keeps_sessions`; `backend/tests/api/test_erasure_rollback.py`: `test_erasure_enqueue_failure_rolls_back_and_returns_503` (control: `test_erasure_with_a_working_broker_commits_before_the_response`); `backend/tests/workers/test_celery_results.py::test_enqueue_with_unreachable_redis_raises` | With the broker raising, `DELETE /accounts/{id}` answers 503 `application/problem+json`, type `erasure-notification-unavailable`, with `Retry-After`; the account row, its PII and password hash, its sessions are unchanged; no anonymized dataset and no `ACCOUNT_DELETED` / `DATA_ANONYMIZED` audit row exists; the request transaction (`DbSession`, `scope="function"`, ADR-0023) rolled back before the response started. Converse case (enqueued, then the commit fails): no e-mail is sent for an erasure that did not commit (TC-004.6; PRB-083) | Both tests pass; moving the enqueue after `invalidate_all`, or swallowing the failure, fails them (negative control, TASK-141 "Verification results") |
| TC-004.5 | SR-024 AC 5 | `backend/tests/workers/test_retention_tasks.py`: `test_sweep_failing_dataset_closes_every_session`, `test_sweep_retries_at_most_three_times_then_logs_count`, `test_sweep_dataset_failing_once_then_succeeding_is_erased`, `test_sweep_never_deletes_before_deadline_across_retries`; `backend/tests/workers/test_retention_erase.py::test_erase_per_dataset_failure_isolation` | A dataset whose delete raises is rolled back alone; sessions opened = sessions closed; later datasets are erased; the task runs once and retries 3 times (4 runs) and then logs the failed count; a dataset that fails once is erased by the retry; a dataset whose deadline is in the future is never deleted, in any run | All listed tests pass |
| TC-004.6 | SR-024 AC 6 | `backend/tests/workers/test_erasure_code_email_gate.py`: `test_sends_when_the_dataset_is_committed`, `test_rechecks_until_the_dataset_is_committed`, `test_drops_the_e_mail_when_the_erasure_never_commits`, `test_sends_when_the_commit_cannot_be_confirmed`, `test_smtp_retry_budget_unchanged_after_commit_checks`, `test_commit_check_session_closed_on_every_path`, `test_gate_does_not_see_an_uncommitted_erasure` (real DB); `backend/tests/identity/test_erasure.py::test_erase_enqueues_email_with_pre_erasure_address` (the task receives the dataset id) | The retrieval-code e-mail is sent only when the erasure's `anonymized_dataset` row is visible to the worker's own session: present on the first check, one send and no retry; absent, `self.retry` with countdowns 2, 4, 8, 16, 32 s then 60 s (14 re-checks, about 10 minutes) and `commit_checks` counted apart from the 3 SMTP retries (60, 120, 240 s); absent at the last check, no send, one WARNING naming only the dataset id, the task returns; the check raising at every attempt, the e-mail is sent after the last re-check with a WARNING; every check session is closed; on PostgreSQL an open erasure transaction with its dataset flushed is reported absent and, after the commit, present | All listed tests pass. Negative control: sending without the check fails `test_drops_the_e_mail_when_the_erasure_never_commits` and 8 more of the gate tests (TASK-228 "Verification results") |
| TC-004.7 | SR-024 AC 3, AC 5 | `backend/tests/workers/test_retention_lock.py` (real DB): `test_second_sweep_waits_and_writes_no_audit_row`, `test_second_sweep_erases_after_the_first_rolls_back`, `test_locked_select_rechecks_the_deadline`; the TC-004.3 and TC-004.5 tests unchanged in assertions (their fake session answers `execute` for the locked select) | A sweep that reaches a dataset another sweep has deleted but not committed waits on the row lock (seen as `wait_event_type = 'Lock'` in `pg_stat_activity`); when the other commits, it finds no row: `erased == 0`, `failed == 0`, one `ANONYMIZED_DATASET_ERASED` row for the dataset; when the other rolls back, it erases the dataset and writes exactly one row; the statement is `FOR UPDATE` without `SKIP LOCKED` and carries the deadline, so a dataset not yet due is not returned | All listed tests pass. Negative control: removing `.with_for_update()` fails `test_second_sweep_waits_and_writes_no_audit_row` and `test_locked_select_rechecks_the_deadline` (TASK-228 "Verification results") |

## Acceptance criteria (class B unit level, §5.5.3)

- Boundary: retrieval exactly at the deadline, one second before and one second after.
- Fault handling: a failure mid-sweep must not leave a partially erased dataset or leak a session (TC-004.5).
- Fault handling: an erasure whose code e-mail cannot be enqueued is rolled back as a whole and reports a retryable error (TC-004.4).
- Fault handling: the code e-mail of an erasure that did not commit is not sent, and the code of a committed erasure is never dropped on an unknown state (TC-004.6).
- Concurrency: two overlapping sweeps erase a dataset once and write one audit row (TC-004.7).

## Notes

TASK-116 (re-keying) is open (PRB-012 was resolved by TASK-141); the re-keying criterion is therefore specified here but not yet verified. The sweep tests use an in-memory fake of the session (counting opens and closes), not PostgreSQL; the erasure rollback test (TC-004.4), the commit visibility test (TC-004.6) and the lock tests (TC-004.7) use PostgreSQL through testcontainers and therefore a working Docker daemon.

## Version history

- 1.1 (2026-10-30): approved baseline.
- 1.2 (2026-11-14): TASK-141 (CR-006). TC-004.4 (erasure rolled back when the code e-mail cannot be enqueued, SR-024 AC 6) and TC-004.5 (sweep isolation, session release, at most 3 retries, SR-024 AC 5) added; TC-004.3 names AC 4; fault-handling criteria extended. Approval cleared, `in_review`.
- 1.2 (2026-11-14): QA review of TASK-141 (round 1): `approved` (status only; content unchanged).
- 1.3 (2026-11-14): TASK-228 (CR-006 D-30; PRB-083, PRB-084). TC-004.4 converse case rewritten (no e-mail for an erasure that did not commit); TC-004.6 (commit-gated erasure e-mail, SR-024 AC 6) and TC-004.7 (concurrent sweeps, SR-024 AC 3, AC 5) added; fault-handling criteria extended; notes updated (PRB-012 no longer open). Approval cleared, `in_review`.
- 1.3 (2026-11-14): QA review of TASK-228 (round 1): `approved` (status only; content unchanged).
- 1.4 (2026-11-14): TASK-225 (QA of TASK-228): rows TC-004.6 and TC-004.7 had six cells against the five-column header; the "Negative control" text is merged into the Pass criteria cell. No change of content. Content change on an approved record, so the 1.3 approval record is cleared: `in_review`.
- 1.4 (2026-11-15): QA review of TASK-225 (round 2): `approved` (status only; content unchanged).
