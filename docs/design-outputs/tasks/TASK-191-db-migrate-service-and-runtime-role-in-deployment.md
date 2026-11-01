---
id: "TASK-191"
type: task
title: "Run migrations as the owner in a one-shot service and connect the application with the runtime role"
status: draft
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-01"
links:
  - target: "SR-023"
    relation: implements
  - target: "SR-041"
    relation: implements
  - target: "RISK-006"
    relation: mitigates
  - target: "RISK-001"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "PRB-005"
    relation: relates_to
  - target: "PRB-007"
    relation: relates_to
  - target: "PRB-061"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-190"
    relation: relates_to
  - target: "ADD-026"
    relation: relates_to
tags: ["security", "deployment", "cr:CR-004", "control:design", "ask-first"]
---

# TASK-191 — Run migrations as the owner in a one-shot service and connect the application with the runtime role

- **Software item / unit:** SI-DEPLOY `U-DEP-Compose`, `U-DEP-DbRoles` (ADD-026).
- **PRB:** PRB-005 (last task), PRB-007 (superuser credential), PRB-061 (worker container runs gunicorn; folded in by the human, CR-004 D-3). **CR:** CR-004.
- **Depends on:** TASK-190; TASK-203 (environment template and Compose guards, edited first).
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (`infra/docker-compose.yml`, `backend/entrypoint.sh`, `backend/Dockerfile`, `infra/.env.example`,
  `infra/DEPLOY.md`, `infra/smoke-test.sh`, 1 infra test; TS-009, TS-015)
- **Needs:** a Docker host; a copy of a populated development database for the rehearsal.
- **Boundary (CR-004 "Ask first"):** a grant change applied to an existing database. Run it only
  on the rehearsal copy until the human has approved the rehearsal result.
- **Design:** [ADR-0017](../../design/adr/0017-database-roles-and-append-only-audit-log.md)

## Objective

SR-023 AC 8 on the deployed stack, and no superuser application credential (PRB-007 item 3).

## Implementation detail

1. `infra/docker-compose.yml`: new one-shot `db-migrate` (backend image, entrypoint
   `sh -c "alembic upgrade head && python -m app.db.roles"`, `restart: "no"`, `medhub` network),
   with `DATABASE_OWNER_URL`, `DATABASE_URL` and `AT_REST_ENCRYPTION_KEY*` (for migration 0010,
   TASK-194) passed with `:?` guards. `backend` and `celery-worker` depend on it with
   `service_completed_successfully`. `postgres` gets a healthcheck (`pg_isready`), and
   `db-migrate` waits for `service_healthy`.
2. `backend/entrypoint.sh`: remove `alembic upgrade head`.
3. `infra/.env.example`: `DATABASE_OWNER_URL=` and `DATABASE_URL=` (runtime user `medhub_app`),
   both empty, with generation notes (SR-041 AC 4).
4. `infra/DEPLOY.md`: new settings; upgrade procedure for an existing installation (back up,
   set both URLs, `docker compose up db-migrate`, check, start); rehearsal result.
5. `infra/smoke-test.sh`: a check that, as the runtime role, `UPDATE audit_log` fails with 42501,
   and that `backend` is connected as the runtime role (`current_user`).
6. **Rehearsal** (record in TS-009 and for the next TR): restore a copy of a populated development
   database into a throw-away volume, run `db-migrate`, start the stack, run the smoke test and
   the API flows (login, clinical read, attachment download); record row counts before and after,
   the role check, and the time taken. The original volume is not touched.

7. **PRB-061 (human decision 2026-10-31, CR-004 D-3).** The `celery-worker` container runs gunicorn
   because `entrypoint.sh` never runs `"$@"`. With the migrations gone from the entrypoint (item 2):
   - `backend/entrypoint.sh` ends with `exec "$@"`; `backend/Dockerfile` gets the gunicorn command
     as its default `CMD` (the `--forwarded-allow-ips=` option stays, ADR-0019), so `backend`
     starts as before and `celery-worker` runs its Compose `command:`;
   - the worker **and beat** run in the started stack: beat as its own service or with `-B` (a
     `beat_schedule` exists, `backend/app/workers/celery_app.py:47`, and nothing runs it);
   - `enforce()` (`backend/app/core/secret_settings.py`) is called before `alembic` in
     `db-migrate` and in `env.py`, and `DATABASE_OWNER_URL` is required (`:?`, no default) in that
     process, so the owner credential is checked where it is used;
   - on the started stack, show the worker and beat processes (`celery inspect ping`, the beat
     log line), run a queued task to completion, and show that the worker refuses a placeholder
     secret at `worker_init` (negative control). Extend `infra/tests/test_compose_db_roles.py`
     (or a new infra test) with: no service but `db-migrate` runs `alembic`; `celery-worker`
     keeps its `command:`.

## Tests (write first)

- `infra/tests/test_compose_db_roles.py`: `db-migrate` exists and is one-shot; `backend` and
  `celery-worker` depend on its successful completion and do not receive `DATABASE_OWNER_URL`;
  both URLs have `:?` guards; the backend entrypoint does not migrate.
- `infra/smoke-test.sh` (started stack): the two checks above.

## Acceptance criteria

- [ ] SR-023 AC 8 on a started stack: the runtime role's `UPDATE` on `audit_log` fails with 42501
      (`infra/smoke-test.sh`).
- [ ] SR-041 AC 2: the owner URL is a required secret with no default, given only to `db-migrate`
      (`infra/tests/test_compose_db_roles.py`).
- [ ] PRB-061: on a started stack the worker and beat run, a queued task completes, and a
      placeholder secret stops the worker (started-stack record; infra test for the wiring).
- [ ] The rehearsal on a populated copy completes with unchanged row counts and working API flows
      (rehearsal record).

## Verification

```sh
cd infra && python3 -m pytest tests -v
docker compose -f infra/docker-compose.yml --env-file infra/.env up -d && infra/smoke-test.sh
cd backend && uv run pytest --cov=app --cov-fail-under=85
```

## Records

- **TS-009**: TC-009.11 extended (started-stack check, rehearsal); **TS-015**: TC-015.2 extended
  (owner URL guard).
- **PRB-005**: `## Resolution` (TASK-190, TASK-191, TASK-192), `resolved`.
- **PRB-061**: `## Resolution` with the started-stack evidence, `resolved` (CR-004 `resolves` link in 1.2).
- **ADD-026** 1.0: confirm `U-DEP-DbRoles`.

## Definition of Done

- [ ] Infra tests and smoke test pass; backend suite passes.
- [ ] Rehearsal recorded and presented to the human before any other database is converted.
- [ ] `traceability-check` shows no error for TASK-191, TS-009, TS-015, SR-023, SR-041, PRB-005.
