---
id: "PRB-084"
type: problem-report
title: "Concurrent retention sweeps write a duplicate erasure audit row"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-14"
updated: "2026-11-14"
criticality: minor
links: []
tags: ["reliability", "audit", "hazard:detectability", "found-in:TASK-141-qa"]
---

# PRB-084 — Concurrent retention sweeps write a duplicate erasure audit row

## Observed

Found by QA in the TASK-141 review (2026-11-14, LOW finding 3); the defect predates TASK-141. When two runs of
`workers.erase_expired_anonymized_datasets` overlap (a TASK-141 retry and the daily beat run, or a manual run),
both can process the same expired dataset, and each writes an `ANONYMIZED_DATASET_ERASED` SUCCESS audit row for
it. The dataset is deleted once; the audit trail records two erasures.

## Impact

The audit trail over-reports the retention erasures (two rows for one dataset, with different timestamps). No
dataset is deleted twice or early, and no data is lost or disclosed.

## Investigation

`backend/app/workers/retention_tasks.py`:

- `:54-59` list the ids of expired datasets in a separate session, without a lock.
- `:67` `db.get(AnonymizedDataset, dataset_id)` in the per-dataset session, a plain `SELECT` with no row lock.
  Under PostgreSQL's default READ COMMITTED, sweep B reads the row while sweep A's delete is uncommitted, or before
  A starts.
- `:69` the deadline re-check passes in both sweeps.
- `:71-72` `db.delete(dataset)` and `flush()`: B's `DELETE` waits on A's row lock, and after A commits it matches
  0 rows. SQLAlchemy only warns on a 0-row ORM delete, so no error is raised.
- `:73-81` B records `ANONYMIZED_DATASET_ERASED` and commits, and `erased` is counted twice across the two runs.

Broken assumption: "the dataset exists in this session, so this session erases it". Nothing serialises two
sessions on the same row. Derived from the code and the QA review; not yet reproduced on PostgreSQL.

## Safety evaluation

No safety-related function or clinical decision is affected, and the retention outcome is correct (deleted once,
never before its deadline, SR-024 AC 4). The effect is an inaccurate audit trail (SR-024 AC 3, SR-023; RISK-006,
accuracy of the record of who did what): an investigator sees two erasures for one dataset. It needs two
overlapping sweeps, which only a retry overlapping the daily run or a manual run produces. Criticality **minor**.
No release exists (CR-004 A-1), so no installation is affected and no notification is needed. The human sets the
final criticality.

## Resolution

Fixed by TASK-228 (CR-006 D-30). `backend/app/workers/retention_tasks.py`: the per-dataset session now selects the
dataset with `SELECT ... FOR UPDATE` and the deadline comparison in the same statement (`_locked_due_dataset`,
replacing `db.get` and the separate re-check). A second sweep that reaches a dataset another sweep is erasing waits
for that transaction; PostgreSQL then re-evaluates the row: deleted, no row, `continue` and no audit row; rolled
back, the row is returned and the second sweep erases it. Plain `FOR UPDATE`, not `SKIP LOCKED`, so a dataset is
never skipped (SR-024 AC 5); one row per transaction cannot deadlock. The deadline boundary is `<=`, as in the listing.

Verified (working tree, 2026-11-14), real PostgreSQL: `backend/tests/workers/test_retention_lock.py`
(`test_second_sweep_waits_and_writes_no_audit_row`: the sweep is seen blocked in `pg_stat_activity`, then
`erased == 0` and one audit row; `test_second_sweep_erases_after_the_first_rolls_back`: one audit row and the dataset
erased; `test_locked_select_rechecks_the_deadline`); TC-004.3 and TC-004.5 tests green with their fake session
answering `execute`; backend suite 1684 passed, 10 skipped. Negative control: removing `.with_for_update()` fails
`test_second_sweep_waits_and_writes_no_audit_row` (the unfixed code gives `erased == 1` and a second audit row) and
`test_locked_select_rechecks_the_deadline`. Reproduce: `cd backend && uv run pytest tests/workers/test_retention_lock.py`.

## Version history

- 1.0 (2026-11-14) — Created from the TASK-141 QA review (LOW 3) on the human's decision to fix it inside
  CR-006. `open`, `minor`.
- 1.1 (2026-11-14) — Resolved by TASK-228; Resolution written. Awaiting QA confirmation of the verification. `resolved`, `minor`.
