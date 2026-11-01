---
id: "PRB-061"
type: problem-report
title: "The celery-worker container runs gunicorn, not Celery, and no beat process exists"
status: open
version: "1.0"
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

Not yet fixed. **Human decision, 2026-10-31:** fix it in TASK-191, which moves the migrations out
of the entrypoint into the one-shot `db-migrate` service (CR-004 D-3). That task will:

- change `backend/entrypoint.sh` to `exec "$@"` and give the image `CMD` of the gunicorn command,
  so a Compose `command:` is honoured and the API still starts by default;
- run the worker and beat as processes of the stack (beat as its own service or with `-B`; the
  choice is TASK-191's);
- prove, on a started stack, that the worker and beat run and consume or fire a task;
- call `enforce()` before `alembic` in `db-migrate` and in `env.py`, and require
  `DATABASE_OWNER_URL` in that process.

The report stays `open` until TASK-191 has been verified on a started stack. TASK-203 changes
nothing here; it documents the limit in `infra/DEPLOY.md`.

## Source

Found while implementing TASK-203 (CR-004); human decision recorded in CR-004.

## Version history

- 1.0 (2026-11-01) — Created from TASK-203. `open`, `major`.
