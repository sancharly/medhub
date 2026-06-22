# TASK-036 — Worker: 5-year permanent erasure

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-WORKER / U-WK-RetentionErase
- **Implements:** SR-024.4 (records past retention handled per policy → permanent erasure); ADR-0013
- **Depends on:** TASK-035 (erasure → anonymized dataset with a retention deadline)
- **Branch:** `feature/worker-retention-erase`
- **Status:** Completed

## Objective

Provide the scheduled Celery Beat job that **permanently and irreversibly erases** any anonymized
dataset whose 5-year retention deadline has passed (ADR-0013 step 4, runtime §6.7 "Expiry"). This
is the storage-limitation control that closes the retention window opened by TASK-035: after 5
years the dataset is gone and a retrieval attempt returns not-found.

## Interfaces to honor

No external HTTP interface; a scheduled Celery Beat task:

```python
def erase_expired_anonymized_datasets() -> int: ...   # returns count erased; scheduled (beat)
```

Consumes the anonymized-dataset repository (TASK-012, model TASK-010/011), the object store for any
re-keyed binaries (TASK-013/045 — attachments), and `AuditService` (TASK-014). Reuses the Celery
base from TASK-031.

Must **not**: erase a dataset before its deadline (ADR-0013); leave orphaned binaries in object
storage (erase DB rows and the referenced objects atomically/consistently); log or expose any
identifying data (the datasets are already anonymized; only dataset ids appear in audit).

## Implementation detail

- Files to create:
  - `backend/app/workers/retention_tasks.py` — `erase_expired_anonymized_datasets`, beat schedule
    entry.
- Schedule: register a Celery Beat periodic task (e.g. daily) in `celery_app.py` (TASK-031). The
  cadence is configurable (`RETENTION_SWEEP_CRON`, TASK-003); daily is sufficient for a 5-year
  deadline.
- Job logic: select anonymized datasets where `retention_deadline <= now`; for each, permanently
  delete the DB row(s) and any associated object-store binaries (re-keyed attachments), irreversibly
  (ADR-0013 — no soft-delete, no recovery). Process in bounded batches; idempotent (a re-run after a
  partial failure resumes cleanly).
- Audit: record `ANONYMIZED_DATASET_ERASED` per dataset (dataset id + ts) (§8.4, SR-023) — never any
  identifying data (there is none) and never a retrieval code (there is none stored).
- Interaction with retrieval (TASK-035): once erased, `retrieve_anonymized` for that dataset returns
  `NotFoundError` (404) (runtime §6.7 "expired dataset → not found").
- Config keys: `RETENTION_SWEEP_CRON` (TASK-003); retention length (5 years) is set at erase time in
  TASK-035, not here.
- Error cases: object-store deletion failure for one dataset is isolated (logged, retried next sweep)
  and does not block erasing the others; the DB row is removed only once its binaries are gone
  (no orphans).

## Tests (write first — TDD, CLAUDE.md §4)

Run eager (`task_always_eager`) with a frozen clock and a fake object store.

- Unit (`backend/tests/workers/test_retention_erase.py`):
  - A dataset with `retention_deadline` in the past is permanently erased (row + binaries); the
    count is returned (SR-024.4, ADR-0013).
  - A dataset still within the 5-year window is **not** touched (ADR-0013).
  - After erasure, `retrieve_anonymized` (TASK-035) for that dataset returns not-found (runtime §6.7).
  - Each erasure audited as `ANONYMIZED_DATASET_ERASED` with dataset id + ts; no identifying data,
    no code (§8.4).
  - Idempotent: a re-run after a simulated partial failure completes without double-erasing or
    crashing; an object-store failure on one dataset does not block the others (no orphan rows).
- Integration (`backend/tests/workers/test_retention_beat_wiring.py`): the beat schedule entry is
  registered and the task is discoverable/enqueueable.

## Acceptance criteria

Distilled from SR-024.4 / ADR-0013:

- [ ] Datasets past their 5-year deadline are permanently and irreversibly erased (row + binaries)
      (SR-024.4, ADR-0013).
- [ ] Datasets within the window are untouched (ADR-0013).
- [ ] Erased datasets are no longer retrievable (404) (runtime §6.7).
- [ ] The sweep is scheduled (Celery Beat), idempotent, and isolates per-dataset failures.
- [ ] Each erasure is audited with dataset id + ts; no identifying data or code (SR-023, ADR-0013).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit (and required integration) tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (N/A — scheduled job, no HTTP endpoint)
- [ ] Audit events emitted for security-relevant actions (ANONYMIZED_DATASET_ERASED — SR-023)
- [ ] Traceability matrix row updated (SR-024.4, ADR-0013 → TASK-036 → tests)
- [ ] Security review completed (N/A — not auth/session/authz; verify irreversibility & no-orphans)
