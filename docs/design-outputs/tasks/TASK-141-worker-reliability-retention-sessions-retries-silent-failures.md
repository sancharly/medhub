---
id: "TASK-141"
type: task
title: "Retention sweep isolation and retries; erasure rolled back when its code e-mail cannot be queued"
status: approved
version: "1.5"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-11-14"
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

- [x] SR-024 AC 5: isolation, every session released, ≤ 3 retries, failed count logged without personal data.
- [x] SR-024 AC 6: enqueue failure → retryable error, nothing committed, account unchanged.
- [x] SR-024 AC 1 to AC 4 tests unchanged and green.

## Definition of Done

- [x] `ruff`, `mypy`, backend suite green; OpenAPI and types regenerated and committed if the 503 is added
- [x] TS-004, TS-017, ADD-008, ADD-017 consistent; `traceability-check` no error for this record

## Implementation notes and verification results (2026-11-14)

**Changed:** `backend/app/workers/retention_tasks.py` (a listing session, then one session and transaction per
dataset, closed on every path; per-dataset rollback and count; deadline re-checked in the dataset's session;
`self.retry(countdown=300 * 2**retries)` while `request.retries < max_retries`; final ERROR with the integer
failed count); `backend/app/identity/erasure.py` (enqueue moved before `invalidate_all`, WARNING with the
dataset id only, then `ErasureNotificationUnavailableProblem`); `backend/app/api/errors.py` (503,
`Retry-After: 30`, type `erasure-notification-unavailable`); `backend/app/api/routers/lifecycle.py`
(`responses={503: ...}`); `backend/openapi/openapi.json` and `frontend/src/api/generated/openapi.ts`
regenerated (only the 503 on `DELETE /accounts/{id}` differs; `npm run typecheck` clean, 315 frontend tests pass).
Records: TS-004 1.2, TS-017 1.4, ADD-008 1.3, ADD-017 1.5, SOUP-014 1.6 (all `in_review`, approval cleared).

**Tests:** new `tests/workers/test_retention_tasks.py` (the four sweep tests), `tests/api/test_erasure_rollback.py`
(real `create_app()`, real `get_db`/`DbSession` on PostgreSQL: 503, nothing changed, rollback before response
start; control with a working broker), two erasure unit tests in `tests/identity/test_erasure.py`
(`test_erasure_enqueue_failure_raises_retryable_problem_and_keeps_sessions`,
`test_erasure_enqueue_failure_logs_warning_without_personal_data`), `test_enqueue_with_unreachable_redis_raises`.
Adapted existing tests whose premise changed: `test_retention_erase.py` (two tests, new session structure; AC 1 to
AC 4 assertions unchanged), `test_erasure.py` (`test_erase_email_failure_does_not_raise` replaced: best effort is
now the opposite policy; autouse no-broker fixture), `test_decision_table.py` and `test_authz_decision_audit.py`
(the erasure call patches `.delay`, as the broker is no longer swallowed).

**Negative control:** with `backend/app` stashed back to HEAD the nine new or adapted tests fail (4 sweep tests,
2 adapted retention tests, 2 erasure unit tests, `test_erasure_enqueue_failure_rolls_back_and_returns_503`); restored,
they pass. **Results:** backend 1670 passed, 10 skipped; `modules/dicom_viewer/tests` 31 passed; `ruff check`,
`ruff format --check` (changed files), `mypy app` clean; `infra/tests` 178 OK.

**Decisions to confirm:** every failed dataset is retried (not only a classified transient error); the sweep
commits per dataset (previously once at the end, so one rollback undid earlier successes). PRB-012 and PRB-013 are
not closed here (QA / human). arc42 `06-runtime-views.md` 6.7 not edited (says the code is e-mailed; still true).

## QA review round 1 (qa-engineer, 2026-11-14) — APPROVED

Verdict: **APPROVED**, no CRITICAL, HIGH or MEDIUM finding; 5 LOW findings (non-blocking, for the orchestrator
to schedule or accept).

Checked independently:

- **Enqueue-before-commit (question 1).** `AnonymizedDatasetRepository.add` flushes, so the account severance and
  the dataset INSERT reach PostgreSQL before `.delay()`: constraint errors surface before the e-mail. What can still
  fail after a successful enqueue is `invalidate_all` (Redis), the two audit inserts and the commit. The worker task
  reads no database row (`email_tasks.py:142-173`), so there is no read race with the uncommitted transaction. An
  after-commit hook is not acceptable here: a failed enqueue after the commit is a committed erasure whose code exists
  nowhere (irrecoverable dataset), which is exactly what SR-024 AC 6 forbids; a transactional outbox would persist the
  raw code, which SR-024 forbids. The chosen order is the right one; residual: see LOW 1.
- **Retry idempotency (question 2).** A retry re-lists only rows still present: committed datasets are gone, so they
  are not re-processed; the deadline is re-checked in the dataset's session. A persistent failure costs three more
  sweeps (300/600/1200 s) and one ERROR, then reappears at the next daily run, never silently. Probe on real
  PostgreSQL (scratch test, `Task.apply()`, pool 2/0): a dataset failing twice is erased by the second retry,
  five audit rows for five expired datasets, the future dataset kept, `pool.checkedout() == 0`.
- **Per-dataset commit (question 3).** The delete and its `ANONYMIZED_DATASET_ERASED` row still commit in one
  transaction. Nothing relied on all-or-nothing; the old single commit was itself wrong (a rollback undid earlier
  deletes that had already been counted and logged as erased).
- **Logs (question 4).** Per-dataset ERROR: dataset id and exception class; final ERROR: integers; erasure WARNING:
  dataset id, no `exc_info`. `problem_error_handler` logs nothing, and `self.retry()` is raised without `exc`, so no
  exception text reaches a log.
- **Mutations (scratch copy):** erasure `raise` replaced by `pass` → 3 tests fail; retention `<=` max_retries,
  no `close()`, no deadline re-check, no `rollback()` → each killed.
- **Adapted tests not weakened:** the authz and audit tests only patch `.delay` (the broker used to be swallowed);
  `test_erase_per_dataset_failure_isolation` now asserts per-session rollback/commit/close and the retry;
  `test_erase_email_failure_does_not_raise` asserted the opposite policy and is replaced by the two AC 6 tests.
- **OpenAPI:** export from the working tree is byte-identical to `backend/openapi/openapi.json`; `openapi-typescript`
  output is identical to `frontend/src/api/generated/openapi.ts`; the only change is the 503 on `DELETE /accounts/{id}`
  (same style as the 503 of `auth.py:56`).

LOW findings:

1. **The converse case is not harmless.** If `invalidate_all`, an audit insert or the commit fails after the
   enqueue, the subject gets "Your MedHub account has been erased per your request" (`email_tasks.py:152`) while
   nothing was erased (the requester sees a 5xx). No data is lost and a retry sends a second, valid code. CR-006 cause
   6 and TS-004 TC-004.4 call it harmless → correct the wording to "misleading e-mail, no data loss", or bind the
   e-mail to the commit without losing AC 6: pass the dataset id to `send_erasure_code_email` and have the worker
   send only once the `anonymized_dataset` row exists (retry with countdown, drop after the last retry). Raise a
   minor PRB if the human wants the fix.
2. **No FAILURE audit row for the rolled-back erasure** (`identity/erasure.py:128-135`): only a WARNING records it,
   while other refusals are audited through `add_independent` (ADR-0016) → optionally record `ACCOUNT_DELETED`
   FAILURE (independent) with the account id. Not required by SR-024 AC 6.
3. **Concurrent sweeps write a duplicate audit row** (`workers/retention_tasks.py:67-80`, as before TASK-141): a
   retry overlapping a beat run or a manual run both `get` the row; the second DELETE matches 0 rows (SQLAlchemy warns
   only) and still records `ANONYMIZED_DATASET_ERASED` → `db.get(AnonymizedDataset, dataset_id, with_for_update=True)`
   (returns None once the other transaction commits).
4. **Dead assignment** `backend/tests/workers/test_retention_erase.py:26` (overwritten on the next line) → delete it.
5. **TS-004 Notes** still say PRB-012 is open → update at the next TS-004 content change.

Verification run: backend `pytest -q` 1670 passed, 10 skipped; `modules/dicom_viewer/tests` 31 passed; `ruff check`
clean (`ruff format --check`: three untouched files, pre-existing); `mypy app` clean; `infra/tests` 178 OK; frontend
`typecheck` clean, vitest 315 passed (32 files); traceability (scope TASK-141 and links, 142 records): 0 errors,
16 warnings (W5 for records in review, W6 pre-existing obsolete SOUP links).

## Version history

- 1.1 (2026-09-17) — Added `mitigates` RISK-007, RISK-008, RISK-009 (TASK-147).
- 1.2 (2026-10-21) — Tagged `control:design`, `control:protective`.
- 1.3 (2026-11-13) — CR-006 Plan stage (Software Architect). Re-based on SR-024 AC 5 and AC 6 (D-5, D-11);
  PRB-013 narrowed to the erasure path (the two silent sites were logged by TASK-207); SR-035 changed from
  `implements` to `relates_to` (its paths stay best effort); `implements` SR-043 added (failed-count log).
- 1.4 (2026-11-14) — Implemented (software-developer). Implementation notes and verification results added; TS-004, TS-017, ADD-008, ADD-017, SOUP-014 changed (`in_review`). `in_review`.
- 1.5 (2026-11-14) — QA review round 1 (qa-engineer): APPROVED with 5 LOW findings; acceptance criteria and DoD ticked. `in_review → approved`.
