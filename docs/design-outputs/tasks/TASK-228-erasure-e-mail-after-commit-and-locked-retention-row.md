---
id: "TASK-228"
type: task
title: "Erasure code e-mail sent only once the erasure is committed; retention row locked per dataset"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-14"
updated: "2026-11-14"
links:
  - target: "SR-024"
    relation: implements
  - target: "SR-043"
    relation: implements
  - target: "RISK-008"
    relation: mitigates
  - target: "RISK-006"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-083"
    relation: relates_to
  - target: "PRB-084"
    relation: relates_to
  - target: "TASK-141"
    relation: relates_to
  - target: "ADD-008"
    relation: relates_to
  - target: "ADD-017"
    relation: relates_to
  - target: "TS-004"
    relation: relates_to
  - target: "TS-017"
    relation: relates_to
  - target: "SOUP-014"
    relation: relates_to
  - target: "SOUP-020"
    relation: relates_to
tags: ["phase:review-2026-07", "cr:CR-006", "control:design"]
---

# TASK-228 — Erasure code e-mail sent only once the erasure is committed; retention row locked per dataset

- **Software items / units:** SI-WORKER `workers/email_tasks.py` `send_erasure_code_email` and
  `workers/retention_tasks.py` `erase_expired_anonymized_datasets` (ADD-017); SI-IDENTITY `identity/erasure.py`
  `ErasureService._erase` (ADD-008).
- **PRBs:** PRB-083 (TASK-141 QA LOW 1), PRB-084 (TASK-141 QA LOW 3). **CR:** CR-006 (D-30).
- **Depends on:** TASK-141 (committed `b2e7a1c`). Parallel with TASK-143 to TASK-146; shares no source file with
  them. Before TASK-225 and TASK-226.
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** S to M (`backend/app/workers/email_tasks.py`, `backend/app/identity/erasure.py`,
  `backend/app/workers/retention_tasks.py`; tests in `backend/tests/workers/` and `backend/tests/identity/`;
  records). No API, schema, migration or OpenAPI change.

## Objective

- **SR-024 AC 6 (PRB-083):** the "your account has been erased" e-mail with its retrieval code is sent only for an
  erasure that is committed. The enqueue stays where TASK-141 put it (before `invalidate_all`, inside the request
  transaction), so a failed enqueue still rolls the erasure back and no committed erasure loses its code.
- **SR-024 AC 3 and AC 5 (PRB-084):** two overlapping retention sweeps erase a dataset once and write one
  `ANONYMIZED_DATASET_ERASED` row for it; the deadline is re-checked under the row lock.
- **SR-043:** the new log lines carry the dataset id and counts only; no address, no retrieval code, no exception
  text.

## Design

### 1. Commit-gated erasure e-mail (PRB-083)

- **Check used: the `anonymized_dataset` row with the erasure's id exists.** `_erase` passes `str(dataset.id)` as
  a third task argument. The dataset INSERT, the PII severance and both SUCCESS audit rows are in one transaction,
  so the row being visible to the worker's own session (READ COMMITTED) means the whole erasure committed. The id
  is unique per erasure; account state (`status = DELETED`) is not used, because it cannot tell this erasure from
  an earlier one and would need the account id in the task. A dataset id is not personal data (SR-043; already
  logged by TASK-141).
- **Retry bounds: up to 14 re-checks, countdown `min(2 ** (n + 1), 60)` s for re-check n = 0..13** (2, 4, 8, 16,
  32 s, then 60 s nine times): about 10 minutes from the first attempt. Reasons:
  - In the normal path the worker can pick the task up before the commit, which follows a few milliseconds
    later; the short first countdowns deliver the code within seconds.
  - A false drop (the row appears after the last check) is the hazard SR-024 AC 6 forbids: a committed erasure
    whose code exists nowhere. The window is set far above any expected enqueue-to-commit time: more than
    twenty times Gunicorn's 30 s worker timeout and sixty times `DB_POOL_TIMEOUT` (10 s). Waiting longer
    costs little: no e-mail is sent while waiting, and the raw code stays in the broker only for an erasure
    that did not commit, whose code matches no dataset. 10 minutes is well inside the Redis transport
    `visibility_timeout` (1 h default; `task_acks_late=True` in `celery_app.py:58`).
  - No timeout bounds the request transaction itself (the Redis client has no `socket_timeout`,
    `api/deps.py:33-35`), so the window is a margin, not a guarantee. See residual risk below.
- **Outcomes of a check:**
  - Row present → send as today.
  - Row absent, re-checks left → `raise self.retry(countdown=..., kwargs={..., "commit_checks": n + 1})`, no
    `exc`, so no exception text reaches a log.
  - Row absent at the last check → do not send; discard the code; log one WARNING naming only the dataset id
    (for example "Erasure code e-mail not sent: dataset %s was never committed"); return normally (no retry, no
    task failure).
  - The check itself raises (worker cannot reach PostgreSQL) → treated as "unknown" and re-checked on the same
    schedule; if the last check still cannot be made, **send** the e-mail and log a WARNING that the commit was
    not confirmed. Reason: in an unknown state a lost code for a committed erasure (SR-024 AC 6, RISK-008,
    irrecoverable dataset) is worse than a misleading e-mail (PRB-083, minor); the drop happens only on a
    positive "row absent".
- **Retry budgets kept apart.** The commit re-checks count in a `commit_checks` keyword argument (default 0). The
  SMTP retries stay exactly as today: 3 retries with the 60 s exponential backoff (TS-017 TC-017.3). Because
  Celery's `request.retries` counts both kinds, replace `autoretry_for` on this one task with an explicit
  `try/except` around `_send_smtp` that retries while `self.request.retries - commit_checks < _MAX_RETRIES`, with
  countdown `_RETRY_BACKOFF * 2 ** smtp_retries`, and re-raises after. Leave the other two e-mail tasks
  unchanged.
- **Session:** the check opens a session with `next(get_db())` and closes it in `finally` on every path (as the
  retention sweep). It reads one row by primary key; no write.
- **Rejected alternatives:** enqueue after commit (an `after_commit` hook): a failed enqueue would leave a
  committed erasure with no code (SR-024 AC 6). A transactional outbox: it stores the raw code (SR-024). Polling
  inside the task with `sleep`: it holds a worker slot for the whole window.

### 2. Row lock in the retention sweep (PRB-084)

- **Lock form: plain `SELECT ... FOR UPDATE` on the dataset row, with the deadline re-check in the same
  statement**, replacing `db.get` at `retention_tasks.py:67-70`:
  `select(AnonymizedDataset).where(AnonymizedDataset.id == dataset_id, AnonymizedDataset.retention_deadline <= now_utc).with_for_update()`,
  then `scalar_one_or_none()`; `None` → `continue` (already erased, or not due).
- **Why not `skip_locked=True`:** with `SKIP LOCKED`, a sweep that meets a locked row skips it; if the lock holder
  then rolls back, neither run erases the dataset in this pass, and the skipped run does not count it. Plain
  `FOR UPDATE` makes the second sweep wait for the first one's transaction (one row, one delete and one audit
  insert: milliseconds), after which PostgreSQL re-evaluates the row: deleted → no row → `continue` and no audit
  row; rolled back → the second sweep gets the row and erases it. It never skips, so "never skipped silently"
  (SR-024 AC 5) holds without a new counter. One row per transaction cannot deadlock.
- The deadline comparison is `<=`, aligned with the listing query (`:56`); today's re-check (`> now` → skip) is
  the same boundary.

### 3. Comment and record wording

- `erasure.py:120-124`: replace "harmless" with the commit-gated behaviour; pass the dataset id.
- Module docstring of `retention_tasks.py`: the row is locked per dataset.

## Steps

1. Write the tests below first and record them failing on `b2e7a1c` (negative control).
2. `email_tasks.py`: `send_erasure_code_email(self, recipient_email, retrieval_code, dataset_id, commit_checks=0)`;
   constants `_COMMIT_CHECKS = 14`, `_COMMIT_CHECK_MAX_COUNTDOWN = 60`; the check, the three outcomes and the
   explicit SMTP retry from Design 1.
3. `erasure.py`: `.delay(original_email, raw_code, str(dataset.id))`; comment updated.
4. `retention_tasks.py`: the locked select of Design 2.
5. Adapt the tests that call `send_erasure_code_email` with two arguments or rely on its `autoretry_for`:
   `tests/workers/test_email_tasks_logging.py`, `tests/workers/test_api_celery_broker.py`,
   `tests/identity/test_erasure.py`, `tests/api/test_erasure_rollback.py`, `tests/authz/test_decision_table.py`,
   `tests/audit/test_authz_decision_audit.py`. Assertions on the policy may not be weakened.
6. Records (below), `ruff`, `mypy`, backend suite, `graphify update .`.

## Tests (write first)

E-mail gate (`backend/tests/workers/test_erasure_code_email_gate.py`, new; SR-024 AC 6):

- `test_sends_when_the_dataset_is_committed`: dataset row present → `_send_smtp` called once, no retry.
- `test_rechecks_until_the_dataset_is_committed`: row absent on the first two checks, present on the third → two
  retries with countdowns 2 s and 4 s and `commit_checks` 1 and 2, then one send.
- `test_drops_the_e_mail_when_the_erasure_never_commits`: row always absent → exactly 14 retries with the
  countdown schedule of Design 1, then no `_send_smtp` call, one WARNING, task returns without raising.
- `test_sends_when_the_commit_cannot_be_confirmed`: the check raises on every attempt → after the last re-check
  the e-mail is sent and a WARNING is logged.
- `test_smtp_retry_budget_unchanged_after_commit_checks`: row absent once, then present; SMTP fails every time →
  exactly 3 SMTP retries, then the task raises.
- `test_commit_check_session_closed_on_every_path`: sessions opened = sessions closed for present, absent and
  raising checks.
- Real PostgreSQL (testcontainers, as `test_erasure_rollback.py`): `test_gate_does_not_see_an_uncommitted_erasure`:
  an erasure transaction left open with its dataset flushed → the check reports absent; after the commit →
  present.

Logs (SR-043, extends TS-017):

- `test_erasure_e_mail_drop_and_unconfirmed_logs_hold_no_personal_data`: with a known address and code, the
  captured records of the drop path and the unconfirmed path contain the dataset id and neither the address, the
  code nor an exception text; the retry records carry no `exc`.

Locked sweep (`backend/tests/workers/test_retention_lock.py`, new, real PostgreSQL; SR-024 AC 3, AC 5):

- `test_second_sweep_waits_and_writes_no_audit_row`: session A locks and deletes an expired dataset and writes its
  audit row without committing; the sweep starts in a thread and blocks (confirmed through `pg_stat_activity`
  `wait_event_type = 'Lock'`, not a sleep); A commits; the sweep finishes with `erased == 0`, `failed == 0`; the
  table holds exactly one `ANONYMIZED_DATASET_ERASED` row for the dataset.
- `test_second_sweep_erases_after_the_first_rolls_back`: as above, but A rolls back → the sweep erases the dataset
  and writes exactly one audit row.
- `test_locked_select_rechecks_the_deadline`: the statement compiled for PostgreSQL contains `FOR UPDATE` (and no
  `SKIP LOCKED`), and a dataset whose deadline is in the future is not returned under the lock.
- Regression: the TC-004.3 and TC-004.5 tests unchanged and green (adapted only where the fake session must answer
  `execute` instead of `get`).

Negative controls: removing `.with_for_update()` fails `test_second_sweep_waits_and_writes_no_audit_row`; sending
without the check fails `test_drops_the_e_mail_when_the_erasure_never_commits`.

## Records to update (developer)

- **TS-004** (approved 1.2 → 1.3, approval cleared, `in_review`): TC-004.4 "Converse case" rewritten (no e-mail is
  sent for an erasure that did not commit; reference TC-004.6); new TC-004.6 (commit-gated e-mail, the gate tests);
  new TC-004.7 (concurrent sweeps, the lock tests); fault-handling criteria extended; Notes: PRB-012 is no longer
  open (TASK-141 QA LOW 5).
- **TS-017** (approved 1.4 → 1.5, approval cleared, `in_review`): new TC-017.9 (drop and unconfirmed WARNINGs
  without personal data); TC-017.3 still passes with three SMTP retries.
- **ADD-008** (`in_review` 1.3 → 1.4) and **ADD-017** (`in_review` 1.5 → 1.6): the e-mail task reads the dataset
  row before sending; the sweep locks the row.
- **SOUP-014** Celery (`in_review` 1.6 → 1.7): relied-on behaviour `self.retry(countdown=, kwargs=)` with an ETA
  under the Redis `visibility_timeout`. **SOUP-020** PostgreSQL (approved 1.3 → 1.4, approval cleared): relied-on
  behaviour `SELECT ... FOR UPDATE` under READ COMMITTED re-evaluates a row deleted by the lock holder and returns
  no row. SOUP-008 SQLAlchemy: `Select.with_for_update()` only, no record change expected.
- **PRB-083, PRB-084:** Resolution written; `resolved` when verified in the working tree (QA confirms).
- **RISK-008, RISK-006:** "none yet (planned …)" in the new rows replaced by the test names (Verify column).

## Acceptance criteria

- [x] SR-024 AC 6: no "account erased" e-mail for an erasure that did not commit; a committed erasure's code is
  sent; an enqueue failure still rolls the erasure back (TC-004.4 unchanged and green).
- [x] SR-024 AC 3, AC 5: two overlapping sweeps write one audit row per erased dataset; no dataset skipped or
  erased before its deadline.
- [x] SR-043: drop and unconfirmed logs hold the dataset id only.

## Definition of Done

- [x] `ruff`, `mypy`, backend suite green; OpenAPI export byte-identical (no contract change)
- [x] TS-004, TS-017, ADD-008, ADD-017, SOUP-014, SOUP-020 consistent; `traceability-check` no error for this record

## Version history

- 1.0 (2026-11-14) — Created at the CR-006 D-30 decision (Software Architect role) for TASK-141 QA LOW 1 and LOW 3. `draft`.
- 1.1 (2026-11-14) — Implemented by the Software Developer role; `draft` -> `in_review` for QA. Verification results and deviations below.
- 1.2 (2026-11-14) — QA review round 1 (QA Engineer role): APPROVED, `in_review` -> `approved`; 1 MEDIUM and 3 LOW findings below. PRB-083 and PRB-084 verified (`resolved` confirmed); TS-004 1.3 and TS-017 1.5 approved.

## Implementation notes and verification results

Files: `backend/app/workers/email_tasks.py`, `backend/app/identity/erasure.py`, `backend/app/workers/retention_tasks.py`;
tests `backend/tests/workers/test_erasure_code_email_gate.py` (new), `backend/tests/workers/test_retention_lock.py` (new),
adapted `test_email_tasks_logging.py`, `test_retention_tasks.py`, `test_retention_erase.py`, `tests/identity/test_erasure.py`.
No API, schema, migration or OpenAPI change (the export is byte-identical to `backend/openapi/openapi.json`).

Deviations from the Design:

- The locked select is a small helper `_locked_due_dataset(dataset_id, now)` in `retention_tasks.py` (same statement
  as Design 2), so the lock test can compile it and the sweep fake can read its parameters.
- `max_retries` of the e-mail task is `_COMMIT_CHECKS + _MAX_RETRIES` (17): Celery counts every retry against it, so
  the task's former limit of 3 would have stopped the commit re-checks. SMTP retries are still capped at 3 by the
  explicit check on `request.retries - commit_checks`; their countdown is `60 * 2 ** n` without Celery's jitter.
- The retry keeps the positional arguments and passes `kwargs={**request.kwargs, "commit_checks": n + 1}`.
- `tests/workers/test_api_celery_broker.py` needed no change (it only resolves the task's broker).
- The "Heads-up" order dependency: at `b2e7a1c` `tests/api/test_erasure_rollback.py::test_erasure_with_a_working_broker_commits_before_the_response`
  already fails when run after `tests/workers/test_celery_results.py` in one session (checked on a clean worktree of HEAD);
  in the full suite order it passes. Not caused by this task; not fixed here.

Negative controls (by hand, restored afterwards): without `.with_for_update()` 2 lock tests fail
(`test_second_sweep_waits_and_writes_no_audit_row`: `erased == 1`, a second audit row; `test_locked_select_rechecks_the_deadline`);
with the commit check replaced by `True` 9 gate tests fail (`test_drops_the_e_mail_when_the_erasure_never_commits` among them).
Before the change the 14 new tests: 13 failed, 1 passed (`test_second_sweep_erases_after_the_first_rolls_back`, which holds on the old code too).

Runs (2026-11-14): `uv run pytest -q` 1684 passed, 10 skipped; `uv run pytest modules/dicom_viewer/tests` 31 passed;
`uv run ruff check` clean; `uv run ruff format --check` only the 3 known files; `uv run mypy app` no issues in 136 files;
`python3 -m unittest discover -s infra/tests` 178 tests OK.

## QA review — round 1 (2026-11-14)

**Verdict: APPROVED.** No CRITICAL or HIGH finding.

Findings:

- **MEDIUM — human decisions not recorded in CR-006.** The human approved P-16 (accept the 10-minute window as the
  residual of cause 14) and P-17 (no SR-024 change), and confirmed both PRBs as `minor`, but CR-006 has no decision
  entry for it; PRB-083 "Resolution" already cites "Accepted residual (human, CR-006 P-16)". Fix (orchestrator or
  Software Architect, before the TASK-228 commit): add a D-31 bullet to the CR-006 decision log with the decision,
  date and source, and a 1.11 version-history line. The plan row of TASK-228 still says "new (`draft`)"; update it in
  the same edit.
- **LOW 1 — `max_retries` boundary untested.** `email_tasks.py:160` `max_retries=_COMMIT_CHECKS + _MAX_RETRIES` (17)
  is exactly tight: the worst case (14 re-checks, then 3 SMTP retries) calls `retry` at `request.retries == 16`.
  The mutant `_COMMIT_CHECKS + _MAX_RETRIES - 1` passes all 30 tests of the gate, logging and e-mail modules; it
  leaves only 2 SMTP retries in that worst case. A QA probe proved the arithmetic correct (countdowns
  2, 4, 8, 16, 32, 60 s x 10, 120, 240; 4 sends; the SMTP exception raised) and killed the mutant. Fix: add
  `test_smtp_retry_budget_after_all_commit_checks` to `test_erasure_code_email_gate.py`: `run(["raise"], smtp=_refused)`, assert
  countdowns `_SCHEDULE + [60, 120, 240]` and `send.call_count == 4`.
- **LOW 2 — TS-004 table rows with an extra cell.** TC-004.6 and TC-004.7 have 6 cells against the 5-column header
  (`TS-004:36-37`). Most Markdown renderers drop the sixth, so the negative-control text disappears. Fix: move
  "Negative control: ..." into the Pass criteria cell at the next TS-004 revision.
- **LOW 3 — "the task returns" not asserted.** `test_drops_the_e_mail_when_the_erasure_never_commits` does not assert
  that the final run returns normally (under `apply()` the outer state is `RETRY`), and
  `test_rechecks_until_the_dataset_is_committed` accepts `RETRY` or `SUCCESS`. Fix: also call
  `send_erasure_code_email.apply(args=(ADDRESS, CODE, DATASET_ID), kwargs={"commit_checks": 14})` with the row
  absent and assert `result.successful()`.

Verified by QA:

- Retry arithmetic: re-checks n = 0..13 at `min(2 ** (n + 1), 60)`; drop at the 15th run; SMTP budget
  `request.retries - commit_checks` stays equal to the number of SMTP retries in every interleaving (each retry
  increments `request.retries` and either increments `commit_checks` or not). Celery 5.6.3 raises
  `MaxRetriesExceededError` only when `request.retries + 1 > max_retries`, so the largest call (16) is allowed.
  The error message would contain the task args (address and code), but it cannot be reached.
- Logs: drop and unconfirmed WARNINGs carry the dataset id only; the re-check `retry` has no `exc`; the SMTP
  retry's exception text is covered by TC-017.3 (`test_erasure_code_email_failure_logs_no_address`, redaction filter).
- Runtime role: `db/roles.py:82` grants SELECT, UPDATE and DELETE on all tables, so the worker can run the gate
  read and `FOR UPDATE`.
- Mutants (each restored, checksum verified): no `.with_for_update()` fails `test_second_sweep_waits_and_writes_no_audit_row` (`erased == 1`),
  `test_locked_select_rechecks_the_deadline` and the fake-based sweep tests. The gate forced to `True` gives 9 failures,
  `_COMMIT_CHECKS = 13` gives 2, unknown → drop gives 1, SMTP `>` instead of `>=` gives 1, and SMTP budget from total
  retries gives 1. `max_retries - 1` survives (LOW 1).
- Adapted tests: only the fixtures changed (third argument, `_erasure_committed` patched, fakes answer the locked
  `execute`); no assertion removed or relaxed.
- Order dependency (pre-existing, confirmed at `b2e7a1c` from a `git archive` copy): `test_erasure_rollback.py`
  builds `TestClient(...)` without `with`, so the lifespan and `_bind_celery_app()` never run. Any earlier test that
  imports `app.workers.celery_app` in the main thread makes it that thread's current app. Even
  `test_task_ignore_result_is_set` alone does this. The test's `patch(...send_erasure_code_email.delay)` then
  resolves the `shared_task` proxy to the `medhub` app's task, but the request's worker thread resolves Celery's
  fallback default app, a different task object. The real `.delay` runs against the default broker, fails, and the
  test gets a 503. A probe showed different task objects across threads only after the import. Not fixed here.

Runs (QA, 2026-11-14): `uv run pytest -q` 1684 passed, 10 skipped; `modules/dicom_viewer/tests` 31 passed;
`ruff check` clean; `ruff format --check` only the 3 known files; `mypy app` no issues in 136 files;
`infra/tests` 178 OK; OpenAPI export byte-identical; traceability (scope TASK-228, PRB-083/084, CR-006,
RISK-006/008, TS-004/017, ADD-008/017, SOUP-014/020, SR-024/043): 136 records, 0 errors; 106 warnings before the
approvals, 111 after (the new ones: W5 from the approved TASK-228 to RISK-006/008, ADD-008/017 and SOUP-014/020,
which await the human, and approval-digest warnings on TASK-228, TS-004 and TS-017).
