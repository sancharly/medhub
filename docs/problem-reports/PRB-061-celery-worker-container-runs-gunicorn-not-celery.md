---
id: "PRB-061"
type: problem-report
title: "The celery-worker container runs gunicorn, not Celery, and no beat process exists"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-01"
updated: "2026-11-01"
criticality: major
links:
  - target: "SR-023"
    relation: relates_to
  - target: "SR-024"
    relation: relates_to
  - target: "SR-030"
    relation: relates_to
  - target: "SR-041"
    relation: relates_to
  - target: "PRB-007"
    relation: relates_to
tags: ["deployment", "worker", "celery", "cr:CR-004"]
---

# PRB-061 — The celery-worker container runs gunicorn, not Celery, and no beat process exists

## Observed

Found by the Software Developer while writing the Compose secret guards (TASK-203, 2026-11-01).
The `celery-worker` service in `infra/docker-compose.yml` sets `command: celery -A
app.workers.celery_app worker --loglevel=info --concurrency=4`, but the container does not run
Celery. It runs the API server: it migrates the database and serves the API on port 8000, like the
`backend` service. No Celery worker consumes the Redis queue, so every task the application
queues is never executed, and the schedule has no process to fire it.

## Impact

Nothing queued is processed: activation e-mails (`workers.send_activation_email`), erasure-code
e-mails (`workers.send_erasure_code_email`), appointment notifications
(`workers.send_appointment_notification`), the session-kill propagation
(`workers.propagate_session_kill`) and the retention sweep
(`workers.erase_expired_anonymized_datasets`). A second API container also runs migrations on
every start, concurrently with the `backend` service. The start-up refusal of missing or
placeholder secrets that the worker is supposed to run on `worker_init` (SR-041 AC 3, TASK-197)
never runs in the started stack.

## Investigation

Read on 2026-11-01. **Root cause found.**

1. `backend/Dockerfile:21` is `ENTRYPOINT ["./entrypoint.sh"]` with no `CMD`. A Compose `command:`
   becomes the arguments of the entrypoint, not a replacement for it.
2. `backend/entrypoint.sh:3-4` runs `alembic upgrade head`, and `:8` ends with
   `exec gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --forwarded-allow-ips=
   app.main:app`. The script never reads `"$@"`, so the arguments Compose passes are dropped.
3. `infra/docker-compose.yml:208-215` (`celery-worker`) sets the `command:` of item 1 and
   overrides no entrypoint. The two services that need a different process (`object-store-init`,
   `object-store-preflight`) do override it (`entrypoint: [...]`), which is how the same image
   avoids the migration; `celery-worker` does not.
4. **Beat is affected too, differently.** `backend/app/workers/celery_app.py:47` defines
   `beat_schedule` (the retention sweep), but no Compose service runs `celery ... beat` and the
   worker command has no `-B`. Even with item 1 fixed, the schedule would not fire. The
   `beat_init` hook (`celery_app.py:25`) therefore has never run in a started stack either.
5. The entrypoint dates from commit `a928072` (TASK-004a, migrate on bring-up). The worker command
   predates it and was never exercised against it: no test starts the worker container (the
   `worker_init` and `beat_init` handlers are tested in process,
   `backend/tests/workers/test_celery_start_up.py`).

## Safety evaluation

Criticality **major**: a safety-related function is absent from the deployed stack, though the
core clinical function (reading and writing records) works.

- **SR-023 (audit):** the `SESSION_KILL_PROPAGATED` audit row, written by
  `propagate_session_kill` (`backend/app/workers/session_tasks.py`), is never written. The other
  audit writes are in the request transaction and are not affected.
- **SR-024 (erasure):** the retention sweep never runs, so anonymized datasets are not erased on
  schedule, and the erasure-code e-mail is not sent. Compliance risk (RISK-008); no wrong clinical
  data is shown.
- **SR-030 (sessions):** the request path kills the account's sessions synchronously
  (`backend/app/identity/lifecycle.py:63`), so a deactivated account loses its sessions at once;
  the worker's second, idempotent invalidation is the part that is missing. Inactivity and
  lifetime expiry are enforced in the request path and are not affected.
- **SR-041:** the worker's start-up refusal is not effective in the stack (see Impact).
- **Data integrity:** no data is corrupted. Two API containers run `alembic upgrade head` at the
  same time on a clean start; Alembic does not serialise concurrent runs by itself, so a
  concurrent first migration could fail one container. Not observed.
- **Released versions:** no release exists (CR-004 A-1), so no notification is needed.

## Resolution

Fixed in TASK-191 (human decision 2026-10-31, CR-004 D-3).

- `backend/entrypoint.sh` ends with `exec "$@"` and no longer runs `alembic`; `backend/Dockerfile`
  has the gunicorn command as its default `CMD` (`--forwarded-allow-ips=` kept, ADR-0019), so
  `backend` starts as before and a Compose `command:` is honoured.
- `celery-worker` runs its `command:` (`celery -A app.workers.celery_app worker`); a new
  `celery-beat` service runs `celery -A app.workers.celery_app beat --schedule=/tmp/celerybeat-schedule`
  (the image user cannot write to `/app`). Both depend on `db-migrate` and connect as the runtime
  role.
- `db-migrate` is the only process that runs `alembic`; it calls `enforce()` first, and
  `backend/app/db/alembic/env.py` calls it again and takes `DATABASE_OWNER_URL` (required with
  `:?`, no default, in that service only). The concurrent-migration exposure of the Safety
  evaluation is gone.

Verification, reproducible (scratch Compose project `task191`, copy of the tree, own `.env`):

1. `cd infra && python3 -m unittest discover -s tests`: `test_compose_db_roles.py` checks that no
   service but `db-migrate` runs `alembic`, that the entrypoint ends with `exec "$@"`, that
   `celery-worker` and `celery-beat` run Celery and wait for `db-migrate`.
2. `docker compose -p task191 up -d --build`, then `COMPOSE_PROJECT_NAME=task191 bash infra/smoke-test.sh`:
   64 passed, 0 failed (round 2). Section 11: PID 1 UID of `celery-worker` and `celery-beat` is non-zero;
   section 12: PID 1 command line is `celery ... worker` / `celery ... beat`, `celery inspect ping`
   answers `pong`, the schedule holds `erase-expired-anonymized-datasets`, the log has
   `beat: Starting`.
3. A task queued with `send_task("workers.erase_expired_anonymized_datasets")` completed:
   `Task ... succeeded in 0.37s: {'erased': 0, 'failed': 0}` in the worker log (the task connects
   as the runtime role).
4. With `RETENTION_SWEEP_CRON=* * * * *` beat logged `Scheduler: Sending due task
   erase-expired-anonymized-datasets` and the worker `received` and `succeeded` the task, 0.01 s
   later.
5. Negative controls: `OBJECT_STORE_SECRET_KEY=change-me` on `celery-worker` and on `celery-beat`
   exits 1 with "refusing to start, secret settings rejected" (`worker_init`, `beat_init`);
   removing `exec "$@"` from the entrypoint makes the containers restart-loop and the smoke test
   report 8 failures, including "'celery-worker' is running (restart: unless-stopped): not running".

## Source

Found while implementing TASK-203 (CR-004); human decision recorded in CR-004.

## Version history

- 1.0 (2026-11-01) — Created from TASK-203. `open`, `major`.
- 1.1 (2026-11-01) — TASK-191: fixed and verified on a started stack. Status `open` → `resolved`; criticality unchanged.
