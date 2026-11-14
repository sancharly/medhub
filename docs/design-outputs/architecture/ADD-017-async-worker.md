---
id: ADD-017
type: architecture-doc
title: Async Worker (SI-WORKER)
status: in_review
version: "1.6"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-14"
links:
  - target: SR-024
    relation: implements
  - target: SR-033
    relation: implements
  - target: SR-034
    relation: implements
  - target: SR-035
    relation: implements
  - target: RISK-008
    relation: relates_to
  - target: RISK-009
    relation: relates_to
  - target: SOUP-013
    relation: relates_to
  - target: SOUP-014
    relation: relates_to
  - target: SOUP-021
    relation: relates_to
  - target: SR-043
    relation: implements
tags:
  - software-item:SI-WORKER
  - class:B
  - layer:backend
---

# ADD-017 — Async Worker (SI-WORKER)

## Responsibility

Celery tasks: send activation & appointment emails, session-revocation propagation

## Software units (IEC 62304 §5.4.1)

- `U-WK-Email` — render & send activation/appointment emails via SMTP (SR-033, SR-035).
  **CR-006 (TASK-228, D-30):** `send_erasure_code_email(recipient, code, dataset_id, commit_checks=0)` reads the
  `anonymized_dataset` row with `dataset_id` (own session, one read by primary key, closed on every path)
  before sending, so the e-mail goes out only for a committed erasure (SR-024 AC 6, PRB-083). Row absent:
  `self.retry` with countdown `min(2 ** (n + 1), 60)` s for re-check n = 0..13 (about 10 minutes, no exception
  text logged), counted in `commit_checks`, apart from the 3 SMTP retries (60 s doubled), which are an explicit
  `try/except` around `_send_smtp`; absent at the last check: the code is dropped with one WARNING naming only
  the dataset id; the check cannot be made at the last check: the e-mail is sent with a WARNING (a lost code for
  a committed erasure is worse than a misleading e-mail).
- `U-WK-SessionRevoke` — propagate deactivation session-kill within 30s (SR-034.2).
- `U-WK-RetentionErase` — scheduled job that permanently erases anonymized datasets past their 5-year retention deadline (SR-024.4, ADR-0013).
  **CR-006 (TASK-141):** a first session lists the ids of the expired datasets (a batch of 100); then one
  database session and transaction per dataset, always closed; a failure is rolled back, isolated to its
  dataset and counted (id and exception class logged, not the exception text); the deadline is re-checked
  inside the dataset's session so a retry deletes only expired datasets; when any dataset failed the task
  retries itself (`self.retry`, at most 3, countdown 300 s doubled per retry, as the e-mail tasks'
  exponential backoff) and after the last retry logs the failed count (an integer) at ERROR without
  personal data (SR-024 AC 5, SR-043; RISK-007, RISK-008). Every per-dataset failure is retried, not only
  those known to be transient: a persistent one costs three more sweeps and the ERROR.
  **CR-006 (TASK-228, D-30):** the dataset row is read with `SELECT ... FOR UPDATE` and the deadline is re-checked
  in the same statement (`_locked_due_dataset`), so an overlapping sweep waits for the other's per-dataset
  transaction and then finds no row: one `ANONYMIZED_DATASET_ERASED` row per dataset (SR-024 AC 3, AC 5;
  PRB-084). `SKIP LOCKED` is not used: a skipped dataset whose lock holder rolls back would not be erased in that
  pass.
- Logging — worker and scheduler install the same JSON formatter and the
  shared redaction filter as the API process, through Celery's logging signals, on every handler.
  The filter replaces email-shaped values in the message and in every structured field before a
  record is emitted. Log calls name accounts and patients by identifier only (SR-043, PRB-011).
  The `setup_logging` receiver passes Celery's `--loglevel` to `configure_logging(level)`, so the worker's and
  beat's root level follows the option (default INFO); the filter sits on the handler, so debug records are
  redacted too, and the value of `argsrepr`/`kwargsrepr` in Celery's debug task-header records (which holds the
  activation token) is replaced (SR-043 AC 2, AC 4; TASK-206).
- Dispatch — `celery_app` sets `task_ignore_result=True`: no code reads a task result, and without it
  `.delay()` retried the result store about twenty times when Redis was unreachable and blocked the
  request for about 20 s inside its transaction; the enqueue now fails in under a second
  (TASK-207). The two call sites that failed silently (session-kill and appointment notification)
  log a WARNING with identifiers only; PRB-013 stays open. **CR-006 (TASK-141, D-5):** those two stay
  best effort; the erasure-code enqueue fails its request instead (ADD-008, SR-024 AC 6).
- Binding — the API process sets the configured Celery app as the process default in its lifespan
  (`_bind_celery_app()` in `backend/app/main.py`, after the secret rule; `celery_app.set_default()`
  is process-global, so every thread resolves the Redis broker). Before it, `.delay()` in the API
  process used Celery's default broker, not Redis and every task was lost (PRB-071). Importing the
  module sets nothing; tests import it without settings.
- Services — `celery-worker` and `celery-beat` are separate containers from the backend image,
  each given its own `command:` through an entrypoint that ends in `exec "$@"` (PRB-061); the
  worker refuses missing or placeholder secrets on `worker_init` and beat on `beat_init`
  (`U-DEP-SecretRule`, ADD-026). Exactly one beat runs the retention schedule.
- Open: activation tokens, retrieval codes and an erased user's e-mail address travel as task
  arguments through Redis in plaintext (PRB-074).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-024, SR-033, SR-034, SR-035; SR-043 was added by CR-004.
Non-functional requirements constraining this item: —.

## Interfaces

Provided and consumed interfaces are specified in
[12-interfaces.md](../../design/12-interfaces.md); the runtime interactions this item takes part in
are in [06-runtime-views.md](../../design/06-runtime-views.md) and the sequence diagrams under
[`../../specifications/`](../../specifications/).

## Architecture narrative

This record is a summary and traceability anchor, not the narrative. The design itself is in the
arc42 sections — [05 building blocks](../../design/05-building-blocks.md) for the decomposition,
[04 solution strategy](../../design/04-solution-strategy.md),
[08 cross-cutting concepts](../../design/08-cross-cutting-concepts.md) and, for deployment,
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0002](../../design/adr/), [ADR-0006](../../design/adr/), [ADR-0009](../../design/adr/), [ADR-0011](../../design/adr/), [ADR-0012](../../design/adr/), [ADR-0013](../../design/adr/).

## Risk relevance

Participates in RISK-008, RISK-009 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): unit changes for the planned design added (marked "CR-004"), links added. Content change, so the approval record is cleared and the record returns to review. The implementing tasks confirm the unit text when they land.
- 1.2 (2026-11-07): TASK-206. Logging unit: `--loglevel` honoured and debug task headers redacted. Approval record cleared; `in_review`.
- 1.3 (2026-11-08) — TASK-201 (CR-004): `_bind_celery_app()` (PRB-071), `task_ignore_result` and the logged enqueue failures (TASK-207), the beat service and entrypoint (PRB-061) added; the "CR-004 change" marker removed. `in_review`.
- 1.4 (2026-11-13) — CR-006 Plan stage (Software Architect role): retention sweep isolation, session release and retries (SR-024 AC 5) and the enqueue policy of D-5 marked "CR-006 (planned)". Content change, so the 1.3 approval record is cleared and the record returns to review.
- 1.5 (2026-11-14) — TASK-141 (CR-006): "planned" markers of the retention sweep and of the enqueue policy removed; the implemented behaviour described (per-dataset session and transaction, retry, failed-count log). Approval record cleared; `in_review`.
- 1.6 (2026-11-14) — TASK-228 (CR-006 D-30, PRB-083, PRB-084): the erasure e-mail task checks the dataset row before sending; the retention sweep locks the dataset row. Approval record cleared; `in_review`.
