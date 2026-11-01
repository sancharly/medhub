---
id: "TASK-191"
type: task
title: "Run migrations as the owner in a one-shot service and connect the application with the runtime role"
status: approved
version: "1.3"
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

- [x] SR-023 AC 8 on a started stack: the runtime role's `UPDATE` on `audit_log` fails with 42501
      (`infra/smoke-test.sh`).
- [x] SR-041 AC 2: the owner URL is a required secret with no default, given only to `db-migrate`
      (`infra/tests/test_compose_db_roles.py`).
- [x] PRB-061: on a started stack the worker and beat run, a queued task completes, and a
      placeholder secret stops the worker (started-stack record; infra test for the wiring).
- [x] The rehearsal on a populated copy completes with unchanged row counts and working API flows
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

- [x] Infra tests and smoke test pass; backend suite passes.
- [ ] Rehearsal recorded and presented to the human before any other database is converted.
- [x] `traceability-check` shows no error for TASK-191, TS-009, TS-015, SR-023, SR-041, PRB-005.

## Carried from the TASK-190 QA review (2026-11-01)

- **Ordering window.** Migration 0009 (TASK-190) dropped the 0006 rules while the application
  still connects as the owner. Until this task deploys the runtime role, an owner-connected
  `UPDATE`/`DELETE` on `audit_log` succeeds. The human decides whether this is accepted (TASK-190
  QA finding 1). If it is accepted: do not merge, tag or deploy the branch to a shared database
  between the two commits. PRB-005's Resolution states that the rules went before the role was
  deployed.
- **`apply` on a pre-existing role** (`backend/app/db/roles.py`). Refuse a runtime role that is a
  member of any role, owns any object or is a superuser. In PostgreSQL 16, `ALTER ROLE ...
  NOINHERIT` leaves an existing grant's INHERIT option in place. Add the smoke check: as the
  runtime role, `SET ROLE <owner>` fails and `pg_auth_members` is empty.
- **`alembic_version`.** Revoke `INSERT, UPDATE, DELETE` from the runtime role, guarded by
  `to_regclass` (the `create_all` test databases have no such table).
- **Grants after every migration.** `db-migrate` runs `alembic upgrade head && python -m app.db.roles`
  in one run, and no other process migrates. No default privileges are set, so a table is granted
  only by the next `apply`.
- **Optional.** Send a SCRAM verifier (`psycopg2.extensions.encrypt_password`) instead of the
  plaintext password in `CREATE/ALTER ROLE`, so server statement logs never hold it.

## Implementation notes (2026-11-01)

Human authorization (2026-11-01, chat): scratch, project-scoped Docker stacks only (`task191`,
`task191r`, `down -v` at the end); `infra/.env` never edited (md5 `b76307b812d4ab599fdcb8bf42ce9064`
before and after); the pre-existing `peaceful_pike` container and every pre-existing volume
untouched. The window between TASK-190 and TASK-191 is accepted (CR-004 D-4 1.3).

### Files

- `infra/docker-compose.yml`: `db-migrate` (one-shot, owner), `celery-beat`, `postgres` healthcheck;
  `backend` and `celery-worker` depend on `db-migrate` completing; `DATABASE_OWNER_URL: ""` in the
  three application services.
- `backend/entrypoint.sh` (`exec "$@"`, no alembic), `backend/Dockerfile` (gunicorn `CMD`),
  `backend/app/db/alembic/env.py` (owner URL, `enforce()`), `backend/app/db/roles.py`,
  `backend/app/core/secret_settings.py` (owner/runtime rule).
- `infra/.env.example`, `infra/DEPLOY.md`, `infra/smoke-test.sh`, `.github/workflows/ci.yml` (two steps).
- Tests: `infra/tests/test_compose_db_roles.py` (new), `test_compose_secrets.py`,
  `test_compose_object_store.py`, `test_ci_compose_env.py`, `test_compose_trusted_proxy.py`;
  `backend/tests/db/test_audit_append_only_privileges.py`, `backend/tests/core/test_secret_settings.py`.
- Records: TS-009 1.10, TS-015 1.3 (both `in_review`), PRB-005 1.4 and PRB-061 1.1 (`resolved`),
  PRB-007 1.6 (`open`), CR-004 1.3 (D-4 only), this task.

### Design choices and deviations

- **Runtime password: no new setting.** The task text derives the role from `DATABASE_URL`
  (`roles.main()` already did). `DATABASE_URL` now names `medhub_app` with its own password;
  `DATABASE_OWNER_URL` is new and required. `secret_settings.check` refuses, when both are present,
  the same user or the same password (so `db-migrate` refuses a runtime URL equal to the owner's).
  The `POSTGRES_PASSWORD`-differs rule is therefore enforced as owner-password-differs, because the
  owner URL carries `POSTGRES_PASSWORD`.
- **`db-migrate` also gets the AT_REST and object-store keys.** `enforce()` reads the full Settings
  (it cannot run on a subset), so the same guarded expressions are passed. (`AT_REST_ENCRYPTION_KEY*`
  for migration 0010 is TASK-194's.)
- **(Superseded in round 2: no `env_file` at all, see below.) Owner URL kept out of `env_file` services by `DATABASE_OWNER_URL: ""`.** Compose passes the
  whole `.env` to `backend`, `celery-worker` and `celery-beat` (`env_file`), so an operator's
  `DATABASE_OWNER_URL` line would reach them; `environment:` wins. `test_compose_secrets.py`
  `test_no_secret_is_set_to_a_literal` allows exactly that one empty literal outside `db-migrate`.
- **`env.py` calls `enforce()` only when no `sqlalchemy.url` is set** (the deployment path). Test
  suites that set the URL themselves have module-scoped fixtures that run before the baseline test
  environment and would fail the secret rule on the developer's `.env`. `DATABASE_OWNER_URL` unset
  raises `RuntimeError`. Offline mode honours an explicit URL as well.
- **Beat as its own service** (`celery-beat`), not `-B`, so it can be restarted and checked on its
  own; schedule file in `/tmp` (the image user cannot write `/app`).
- **CI.** The backend job's migration step now sets `DATABASE_OWNER_URL` (owner) and a runtime
  `DATABASE_URL` for that step; the object-store job's `.env` writer adds `DATABASE_OWNER_URL` and a
  separate runtime password. Verified by running `alembic upgrade head` with the CI variables on a
  scratch PostgreSQL 16 container (removed afterwards).
- **Rehearsal source.** "Old layout" is the commit before TASK-190 (`HEAD~1`, `git archive` into the
  scratchpad): migrations through 0008, the 0006 rules in place, application connected as the owner,
  `celery-worker` running gunicorn. That is the state of an installation before CR-004.
- **Optional LOW (smoke section 11) done:** a built service that is not `running` and whose restart
  policy is not `no` is a FAIL (uses `State.Status`, so a restart loop is caught).
- **Not done:** the Compose project name `infra` of the human's own dev stack was not touched; that
  stack's `infra/.env` lacks `DATABASE_OWNER_URL` and must be converted with the upgrade procedure
  (DEPLOY.md) before it is started again; `docker compose up` refuses until then.

### Verification run

| Command | Result |
|---|---|
| `cd backend && uv run pytest --cov=app --cov-fail-under=85` | 1089 passed, 4 skipped; coverage 93.89 % |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `uv run ruff check . && uv run black --check . && uv run mypy app` | clean (249 files unchanged; 130 source files) |
| `cd infra && python3 -m unittest discover -s tests` | 69 tests OK |
| `uv run pytest tests/db/test_audit_append_only_privileges.py tests/core/test_secret_settings.py` | 171 passed (with `tests/db`) |
| Smoke test, started stack `task191` (fresh) | 59 passed, 0 failed |
| Smoke test, started stack `task191r` (after the rehearsal upgrade) | 59 passed, 0 failed |

### AC to evidence

| AC | Evidence |
|---|---|
| SR-023 AC 8 on a started stack | smoke section 12: `update`, `delete`, `truncate` on `audit_log` fail with 42501 as `medhub_app`; `SET ROLE` to any other role fails; `pg_auth_members` empty. Unit: `test_audit_append_only_privileges.py` |
| SR-041 AC 2 (owner URL required, only in `db-migrate`) | `test_compose_db_roles.py` (`test_owner_url_is_guarded_in_db_migrate_only`, `test_owner_url_unset_or_empty_is_refused_naming_it`, `test_application_services_do_not_receive_the_owner_url`); smoke: no container but `db-migrate` holds it |
| PRB-061 | `test_compose_db_roles.py` (`test_no_service_but_db_migrate_runs_alembic`, `test_worker_and_beat_run_celery`, `test_the_entrypoint_does_not_migrate_and_ends_with_exec`); started stack below |
| Rehearsal | below |

### Started-stack record (project `task191`, copy of the tree, own `.env`)

- `docker compose -p task191 up -d --build`: `db-migrate` ran 0001..0009 and printed `database roles
  applied for runtime role medhub_app`, exit 0; `backend`, `celery-worker`, `celery-beat` started after.
- API flows through the proxy (`https://localhost`, doctor and patient accounts created in the
  scratch database): consent grant 201, doctor lists patients 200, clinical entry create 201 and read
  200, attachment upload 201 and download 200 with identical bytes, logout 204. 16 audit rows were
  written by the runtime role.
- Worker: `celery inspect ping` answers `pong`; a task sent with `send_task` returned
  `{'erased': 0, 'failed': 0}`, state SUCCESS, in 0.37 s.
- Beat: `beat: Starting...`; with `RETENTION_SWEEP_CRON=* * * * *` (scratch `.env`) the log showed
  `Scheduler: Sending due task erase-expired-anonymized-datasets` at 15:25:00.042 and the worker
  `received` (15:25:00.055) and `succeeded` it. The cron was restored afterwards.
- UID evidence (smoke section 11): PID 1 and `id -u` of `celery-worker` and `celery-beat` are non-zero;
  section 12: PID 1 command lines are `celery ... worker` and `celery ... beat`.

### Rehearsal record (project `task191r`, populated throwaway database)

- Old layout (`HEAD~1`): `alembic current` 0008, rules `no_delete_audit_log` and `no_update_audit_log`
  present, application connected as `medhub`. Seeded: 2 accounts, 1 group, consent, 1 clinical entry,
  1 attachment (through the API), plus 5000 `audit_log` rows (5015 in all). Stack stopped (no `-v`).
- Upgrade (DEPLOY.md procedure): backup `pg_dump -Fc` (153 KB, deleted with the scratchpad copy),
  both URLs set, `docker compose up --build db-migrate`: 0008 to 0009, roles applied, exit 0, **3.0 s**
  (`StartedAt` to `FinishedAt`); `up -d --build` then brought the stack up.
- Row counts before and after identical for all 14 tables (`audit_log` 5015, `account` 2,
  `attachment` 1, `clinical_entry` 1, `consent_grant` 1, `group` 1, `group_membership` 2); md5 of the
  5015 pre-existing `audit_log` rows `a4bf0be3...` before and after; md5 of the account rows
  `7885cc8a...` before and after. `alembic_version` 0009, no rules on `audit_log`, `medhub` superuser,
  `medhub_app` not.
- App flows after the upgrade, through the proxy, with the accounts created before it: login,
  clinical entries read (200, the pre-upgrade entry found), the pre-upgrade attachment downloaded with
  identical bytes (200), a new entry created (201).
- As `medhub_app`: `UPDATE`, `DELETE`, `TRUNCATE` on `audit_log` each SQLSTATE 42501; 5000 seeded rows
  remained. Smoke test 59 passed, 0 failed (worker, beat, `inspect ping`, schedule included).

### Negative controls

| Control | Result |
|---|---|
| `DATABASE_URL` pointed at the owner (backend recreated) | smoke: 5 FAIL (backend runs as `medhub`, superuser; update, delete, truncate and `SET ROLE` executed). `db-migrate` with the same value refuses: same user and same password |
| `exec "$@"` removed from the entrypoint | worker and beat restart-loop; smoke: 8 FAIL (not running, main process empty, `inspect ping`, schedule, `beat: Starting`, UID unreadable, probe) |
| `roles.apply` on a pre-existing superuser / member / owner role | `apply` raises; with the check removed, 3 tests fail |
| `OBJECT_STORE_SECRET_KEY=change-me` on `celery-worker` and `celery-beat` | both exit 1 with `refusing to start, secret settings rejected` |

### Records that need a human or a later task (not edited here)

- **ADD-026** (approved): `U-DEP-Compose` now includes `db-migrate` and `celery-beat`; the entrypoint
  no longer migrates; `U-DEP-DbRoles` is run by `db-migrate`; the secret rule gains the owner/runtime
  rule. Confirm `U-DEP-DbRoles` and revise (task Records line).
- **ADD-016** (`U-PER-Roles`) and **ADR-0017** (`Proposed` to accepted): `alembic_version` is not
  writable by the runtime role; `apply` refuses a role that is privileged or owns objects; the
  password is sent as a SCRAM verifier; `env.py` uses `DATABASE_OWNER_URL`. ADR-0017 line 61 ("the
  entrypoint loses its `alembic upgrade head`") is now true.
- **SR-041** AC wording is unchanged; **SOUP-009** (alembic) text "runs at bring-up
  (`backend/entrypoint.sh`)" is stale: it runs in `db-migrate`.
- **Release:** the human accepts the official nginx reverse-proxy image running its master as UID 0
  (outside SR-041 AC 1, TASK-198 QA MEDIUM 1; PRB-007 note).
- PRB-056 (empty `CORS_ORIGINS` in the template) is still open: the scratch environments used
  `CORS_ORIGINS=[]`.

### Teardown

`docker compose -p task191 down -v` and `-p task191r down -v`; afterwards 0 containers, 0 volumes and
0 networks whose name contains `task191`; `peaceful_pike` unchanged (`Created`); `infra/.env` md5
unchanged.

## QA review round 1 (QA engineer, 2026-11-01): CHANGES REQUESTED

Status `in_review` → `draft`. TS-009 1.10 and TS-015 1.3 stay `in_review`. Everything the developer
reported reproduced, except the claim that only `db-migrate` holds the owner credential.

### Findings

1. **HIGH: the owner (superuser) password reaches `backend`, `celery-worker` and `celery-beat`.**
   Location: `infra/docker-compose.yml:57`, `:264` and `:293` (`env_file: .env`), together with
   `infra/.env.example` `POSTGRES_PASSWORD=`.
   - **Cause.** `DATABASE_OWNER_URL: ""` blanks the URL. But `env_file` still passes
     `POSTGRES_PASSWORD`, which is the owner's password, to all three application services.
   - **Evidence.** Project `qa191`, started from the empty template with generated secrets.
     `docker inspect` `Config.Env` and `/proc/1/environ` of `backend`, `celery-worker` and
     `celery-beat` each contain the owner password, as `POSTGRES_PASSWORD`. `docker compose config`
     renders it too. From inside `backend`, this connected as `medhub` with `rolsuper = true`:
     `psycopg2.connect(host='postgres', user='medhub', password=os.environ['POSTGRES_PASSWORD'])`.
   - **Effect.** A compromised application process can bypass SR-023 AC 8 by reconnecting as the
     owner. This defeats the TASK-191 objective "no superuser application credential (PRB-007
     item 3)" and the "given only to `db-migrate`" part of the SR-041 AC 2 line in this task.
   - **Why it was missed.** `infra/smoke-test.sh:318-324` checks only the variable *name*
     `DATABASE_OWNER_URL`, so 59/59 passes anyway. `test_application_services_do_not_receive_the_owner_url`
     (`infra/tests/test_compose_db_roles.py:97`) has the same blind spot.
   - **Fix.**
     - Add `POSTGRES_PASSWORD: ""` to the `environment:` of `backend`, `celery-worker` and
       `celery-beat`, or drop `env_file` from those services. Nothing in `backend/app` or
       `backend/scripts` reads `POSTGRES_PASSWORD`.
     - In `test_compose_db_roles.py`, assert that no rendered environment value of a service other
       than `postgres` and `db-migrate` contains the owner password from `GOOD`. `compose config`
       merges `env_file`, so this test can see the leak.
     - In smoke section 12, read the owner password from `postgres` (`printenv POSTGRES_PASSWORD`).
       Then fail when any running container other than `postgres` has that password anywhere in
       `/proc/1/environ`, without printing it.
     - Correct the records: PRB-007 1.6 line 100 ("No application container holds a database
       superuser credential"), PRB-005 1.4 line 110 ("holds no application session") and the TS-015
       TC-015.2 claim. PRB-005 stays `resolved` only once this fix is verified.
2. **LOW: the postgres healthcheck can report healthy during initdb.** Location:
   `infra/docker-compose.yml:125`.
   - **Cause.** `pg_isready -U medhub -d medhub` checks the Unix socket. The image's temporary
     init server listens only on that socket.
   - **Evidence.** On a fresh `postgres:16.15` container polled every ~0.1 s, the socket check
     answered ready before the TCP check (`Yn`) while initdb was running.
   - **Effect.** If the probe lands in that window, `db-migrate` (TCP, `restart: "no"`) fails on
     first install and the application stays down until it is re-run.
   - **Fix.** `pg_isready -h 127.0.0.1 -U medhub -d medhub`.
3. **LOW: a second beat is only documented against, not prevented.** Location:
   `infra/docker-compose.yml:284-285`. `up --scale celery-beat=2` started `qa191-celery-beat-1`
   and `-2`, and both ran.
   - **Fix.** Either accept it as documented (DEPLOY.md says to run exactly one), or add a check in
     smoke section 12 that exactly one `celery-beat` container is running. `container_name` would
     prevent scaling, but it breaks project-scoped stacks.
4. **LOW: `roles.apply` neither resets nor refuses `REPLICATION`/`BYPASSRLS`, and it keeps extra
   direct grants.** Location: `backend/app/db/roles.py:70` and `:83`.
   - **Cause.** A pre-existing `medhub_app` keeps `REPLICATION`/`BYPASSRLS`. It also keeps
     `TRIGGER` and `REFERENCES` on `audit_log` (and any other direct grant), because only
     `UPDATE, DELETE, TRUNCATE` are revoked.
   - **Fix.** Add `NOREPLICATION NOBYPASSRLS` to the attributes. Replace the audit revoke with
     `REVOKE ALL ON audit_log FROM role; GRANT SELECT, INSERT ON audit_log TO role`. Add one test
     case for each.
5. **LOW: the DEPLOY.md rollback step leaves out two facts.** Location: `infra/DEPLOY.md:268`.
   - Restoring the backup loses every row written after the upgrade.
   - The `medhub_app` role survives a database restore, because roles are cluster-global. In the QA
     rollback it was still present, with login.
   - **Fix.** State both, and say to run `DROP ROLE medhub_app` after the restore (or that leaving
     it is harmless while no service uses it).

### Judged and found correct

1. **`enforce()` on the deployed path.**
   - The `db-migrate` entrypoint runs `python -c "...enforce()"` first.
   - `alembic.ini` has `sqlalchemy.url =` (empty), so `env.py` `check_secrets()` also calls
     `enforce()` on the deployed path.
   - QA control: on a fresh database, `OBJECT_STORE_SECRET_KEY=change-me-…` exits 1 naming the
     setting. Afterwards `alembic_version` was absent and no `medhub_app` role existed.
   - The same holds with the entrypoint bypassed (`--entrypoint "alembic upgrade head"`), so the
     `env.py` check alone refuses.
   - Also refused: `AT_REST_ENCRYPTION_KEY=changeme`, and a runtime URL with the owner's user or the
     owner's password.
2. **The `DATABASE_OWNER_URL: ""` override wins over `env_file`.** The value is empty in all three
   containers. Apart from finding 1, no other unneeded secret goes to a service.
3. **Ordering.**
   - A failing `db-migrate` (exit 1) left `backend`, `celery-worker`, `celery-beat` and
     `reverse-proxy` in `Created`.
   - Two re-runs of `db-migrate` exited 0, still at 0009, with grants unchanged.
4. **`roles.py`.**
   - The stored password is `SCRAM-SHA-256$…`, and the server has
     `password_encryption = scram-sha-256` and `pg_hba` `scram-sha-256`. The backend logs in with it.
   - `alembic_version` is SELECT-only and `audit_log` is SELECT and INSERT.
   - The `pg_shdepend` `deptype 'o'` check covers ownership of schemas, databases and objects in
     other databases (shared catalog).
   - `apply` runs in the same `db-migrate` run, after `alembic`.
5. **`secret_settings`.** Users and passwords are compared on parsed URLs (`urlsplit`, password
   unquoted), not as substrings. No message carries a value.
6. **Rehearsal.**
   - `HEAD~1` is `3f0d017` (TASK-198), the parent of the TASK-190 commit `b5294d8`. It has 0008 as
     head, the 0006 rules and an entrypoint that migrates as the owner. It is the right "old layout".
   - QA reduced rehearsal (`qa191r`): `git archive 3f0d017` was started at 0008 with both rules,
     and 2000 `audit_log` rows plus API data were seeded. The upgrade followed the DEPLOY.md steps:
     `pg_dump`, `.env` change, `up --build db-migrate` (0008→0009, roles applied, exit 0, 9 s
     including the build), `up -d --build`.
   - After the upgrade, the 14 table counts, the md5 of all `audit_log` rows and the md5 of all
     `account` rows were identical. The data still has 0 rules. Smoke: 59/0.
   - Old accounts log in. The pre-upgrade entry was found and the pre-upgrade attachment came back
     byte-identical. As `medhub_app`, `UPDATE`, `DELETE` and `TRUNCATE` each returned 42501, and
     the 2000 seeded rows remain.
   - Rollback (step 5, `pg_restore --clean` with the old tree and the old `.env`): counts and
     checksums are identical to before, at 0008 with 2 rules, and the API flows work.
     `medhub_app` is left behind (finding 5).
7. **Records.**
   - PRB-005 and PRB-061 have CR-004 `resolves` links.
   - The PRB-061 Resolution reproduced: worker ping, a task with state SUCCESS, the `beat: Starting`
     log line, and worker and beat with UID 999 running Celery as PID 1, each exiting 1 on a
     placeholder.
   - PRB-005 states the D-4 window, but its line 110 is wrong (finding 1).
   - PRB-007 has the reverse-proxy UID 0 sentence, but line 100 is wrong (finding 1).
   - The CR-004 1.3 edit is limited to D-4 and its history line.
   - TS-009 and TS-015 have valid frontmatter and links, and are `in_review`.
8. **CI.**
   - The backend job's migration step was reproduced with `env -i` and exactly that job's
     variables against a scratch `postgres:16.15`: it ran 0001→0009.
   - `test_ci_compose_env` passes 3 tests: the object-store job writes `DATABASE_OWNER_URL` and the
     subset renders.

### Verification run (QA)

| Command | Result |
|---|---|
| `cd backend && uv run pytest --cov=app --cov-fail-under=85` | 1089 passed, 4 skipped, 93.89 % |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `ruff check .` / `black --check .` / `mypy app` | clean / 249 unchanged / no issues (130 files) |
| `cd infra && python3 -m unittest discover -s tests` | 69 OK |
| Started stack `qa191`, `COMPOSE_PROJECT_NAME=qa191 bash infra/smoke-test.sh` (scratch tree) | 59 passed, 0 failed (false-green on finding 1) |
| API flow through the proxy (`qa191`) | consent 201, list 200, entry 201/200, upload 201, download 200 byte-identical, logout 204 |
| Rehearsal `qa191r`: smoke after the upgrade | 59 passed, 0 failed |
| traceability (`trace.py`, the 9 records in scope) | 0 errors, 18 warnings (W5/W6/W1, none in TASK-191's own links) |

`infra/.env` sha256 `a4933b8c…c696da` before and after. Teardown: `down -v` on `qa191` and
`qa191r`, plus the `qa191-pgprobe` and `qa191-cipg` throwaway containers (`--rm`) and the
`qa191*` images. Afterwards the volume and network lists were identical to before the review, and
only `peaceful_pike` (`Created`) remains.

## Checkpoint C result (QA engineer, 2026-11-01): NOT CLOSED

The criteria come from the CR-004 Plan, "Checkpoints" C. They were checked on started stack `qa191`
across TASK-140, 197, 203, 198, 190 and 191.

| Criterion | Result |
|---|---|
| Stack starts from the empty template with generated secrets | **Met.** Every service came up from `.env.example` with `openssl` values, and the smoke test passed 59/0. Compose refuses an unset `DATABASE_OWNER_URL`, naming it |
| Refuses a placeholder | **Met.** Exit 1, naming the setting, for `db-migrate` (before any migration), `backend` (`AT_REST_ENCRYPTION_KEY`), `celery-worker` and `celery-beat` |
| Every built image and running process non-root | **Met for built images.** `backend`, `celery-worker` and `celery-beat` run as `medhub` with PID 1 UID 999; `frontend` runs as `nginx`/101. Pulled images: postgres and redis 999, object-store 1000. The reverse proxy's master is UID 0, which is outside SR-041 AC 1 and needs human acceptance (PRB-007) |
| Runtime role cannot update `audit_log` | **Met for the role, not for the deployment.** `medhub_app` gets 42501 on UPDATE, DELETE and TRUNCATE, and `SET ROLE` is refused. But the same containers hold the superuser password (finding 1) |
| TASK-191 rehearsal recorded | **Met.** It is recorded and QA reproduced it, including the rollback |

Checkpoint C closes when finding 1 is fixed and re-verified on a started stack.

## Implementation notes, round 2 (2026-11-01)

QA round 1 findings 1 to 5 addressed. Same authorization (scratch project `task191`, `down -v`
afterwards); `infra/.env` md5 `b76307b812d4ab599fdcb8bf42ce9064` before and after.

### 1. HIGH: the owner password reached the application services

- **Choice: drop `env_file` from every service, list each service's settings.** The alternative,
  `POSTGRES_PASSWORD: ""` in the three services, is a deny-list: the next owner-level line added to
  `.env` (a renamed password, another URL) would leak again, and the leak is invisible. An
  allow-list fails safe: a setting not listed does not reach the container, and the cost is that a
  new setting must be added to the service that reads it (written in DEPLOY.md). Compose still fills
  the listed settings from `infra/.env` or the shell by interpolation.
- Per service (names only):
  - `backend`: `DATABASE_URL`, `AT_REST_ENCRYPTION_KEY`, `OBJECT_STORE_{ENDPOINT,ACCESS_KEY,SECRET_KEY,BUCKET}`,
    `REDIS_URL`, `ENVIRONMENT`, `SMTP_HOST`, the four `SESSION_*` timeouts, `SESSION_COOKIE_SECURE`,
    `CORS_ORIGINS`, `TRUSTED_PROXIES`.
  - `celery-worker`: the common set (`DATABASE_URL`, `AT_REST_ENCRYPTION_KEY`, object store four,
    `REDIS_URL`, `ENVIRONMENT`, `SMTP_HOST`) plus `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`,
    `SMTP_USE_TLS`, `SMTP_USE_SSL`, `MAIL_FROM`, `PUBLIC_BASE_URL`.
  - `celery-beat`: the common set plus `RETENTION_SWEEP_CRON`.
  - `db-migrate`: the common set plus `DATABASE_OWNER_URL`, `PYTHONPATH`.
  - `postgres`: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`. Object store, preflight and
    initialiser: unchanged (object-store keys, SSE key). `frontend`, `redis`, `reverse-proxy`: none.
- **Other secrets checked.** SMTP credentials: only `email_tasks.py` reads them, so the backend and
  beat no longer get `SMTP_USER`/`SMTP_PASSWORD` (they keep `SMTP_HOST`, which `Settings` requires).
  Object-store keys and `AT_REST_ENCRYPTION_KEY` stay on `celery-beat` and `db-migrate`: they read no
  object, but `enforce()` (the start-up rule) checks every required secret and `Settings` requires
  them, so removing them would need a separate rule for beat. `SMTP_PASSWORD` has no `:?` guard (it
  is conditional) and no default: `${SMTP_PASSWORD}`; `test_compose_secrets.py` allows exactly that
  form. A leftover `SESSION_SIGNING_KEY` in `.env` no longer reaches any container.
- Side effect: `CORS_ORIGINS` is passed as `${CORS_ORIGINS:-[]}`, so the template's empty
  `CORS_ORIGINS=` no longer stops the stack (PRB-056 stays open for other consumers of the
  template; the round-2 stack was started from an empty `CORS_ORIGINS=` line).
- **Tests.** `infra/tests/test_compose_db_roles.py`: value-based
  `test_no_owner_credential_value_reaches_a_service_but_postgres_and_db_migrate` (renders a copy of
  the Compose file whose project `.env` holds the throwaway values, so an `env_file` would show;
  asserts the owner password and URL are in no service's rendered config but `postgres` and
  `db-migrate`), `test_no_service_reads_env_file`,
  `test_each_application_service_gets_only_the_settings_it_reads`. Smoke section 12: reads the owner
  password from `postgres` and fails when it is in `/proc/1/environ` (read as PID 1's own user;
  root cannot read it without `CAP_SYS_PTRACE`) or `Config.Env` of any other running container,
  without printing it.
- **Negative control.** `env_file: .env` put back on `backend`: 4 infra tests fail (the value-based
  one, `test_no_service_reads_env_file`, `test_each_application_service_gets_only_the_settings_it_reads`,
  `test_an_owner_url_in_the_shell_does_not_reach_the_backend`) and the smoke check
  `'backend' holds no owner credential` FAILs ("the owner password is in its environment").

### 2 to 5

- **2.** Healthcheck is `pg_isready -h 127.0.0.1 -U medhub -d medhub` (`test_postgres_healthcheck_uses_tcp`).
- **3.** Smoke section 12 FAILs unless exactly one `celery-beat` container is running; DEPLOY.md says so.
- **4.** `roles.apply`: `NOREPLICATION NOBYPASSRLS` added; the audit grant is `REVOKE ALL` then
  `GRANT SELECT, INSERT`. Tests: `test_apply_resets_replication_and_bypassrls_on_a_pre_existing_role`,
  `test_apply_removes_extra_direct_grants_on_the_audit_table`; both fail with the change reverted.
- **5.** DEPLOY.md rollback: rows written after the upgrade are lost; `medhub_app` survives a restore
  of a volume that already ran `db-migrate`, leaving it is harmless, `DROP OWNED BY medhub_app; DROP ROLE medhub_app;` removes it.

### Round 2 verification run

| Command | Result |
|---|---|
| `cd backend && uv run pytest --cov=app --cov-fail-under=85` | 1091 passed, 4 skipped; 93.89 % |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `uv run ruff check . && uv run black --check . && uv run mypy app` | clean |
| `cd infra && python3 -m unittest discover -s tests` | 71 OK |
| Smoke test, fresh stack `task191` | 64 passed, 0 failed (62 + the beat count and value checks; all containers) |

Started-stack inspection (project `task191`, fresh, empty `CORS_ORIGINS=`): `Config.Env` of all 9
containers searched for the owner password and the owner URL: found in `postgres` only (password), never
the URL. `/proc/1/environ` of every running container other than `postgres`: owner password absent
(smoke section 12, 7 checks). From `backend`: `POSTGRES_PASSWORD` and `DATABASE_OWNER_URL` are not
in the environment, and `psycopg2.connect(host="postgres", user="medhub")` fails with `fe_sendauth: no
password supplied`. API flow through the proxy (consent, clinical entry, attachment upload and
download, logout) and a queued task (`SUCCESS`) work. Teardown: `down -v`; 0 containers, volumes and
networks named `task191`; `peaceful_pike` unchanged.

## QA review round 2 (QA engineer, 2026-11-01): APPROVED

Status `in_review` → `approved`; TS-009 1.11 and TS-015 1.4 are `approved` too. No CRITICAL or HIGH
finding is open. The DoD item "presented to the human" is the human's step and stays unticked.

### Round-1 findings re-verified

All checks were on fresh scratch stack `qa191`, started from `.env.example` with generated secrets
and `CORS_ORIGINS=` left empty.

1. **HIGH, owner credential: fixed.**
   - **By value.** I searched for the owner password in `Config.Env` of all 11 containers and in
     `/proc/1/environ` (read as root) of every running container. It appears only in `postgres`
     `Config.Env` (`POSTGRES_PASSWORD`) and `db-migrate` (`DATABASE_OWNER_URL`).
   - **SMTP password.** It is only in `celery-worker`.
   - **Owner connect.** From `backend`, `celery-worker` and `celery-beat`, connecting as `medhub`
     is refused with `fe_sendauth: no password supplied`. Neither variable is set in those
     containers.
   - **Negative control.** I put `env_file: .env` back on `backend` in the scratch tree.
     - Smoke: `[FAIL] 'backend' holds no owner credential: the owner password is in its environment`.
     - Infra: 4 tests fail (`test_no_service_reads_env_file`,
       `…no_owner_credential_value_reaches…`, `…gets_only_the_settings_it_reads`,
       `…owner_url_in_the_shell…`).
     - From the backend, the owner connect succeeds again.
     - Restored afterwards.
2. **LOW, healthcheck: fixed.** It is `pg_isready -h 127.0.0.1 …`, with
   `test_postgres_healthcheck_uses_tcp`.
3. **LOW, single beat: fixed.** With `--scale celery-beat=2`, smoke fails "exactly one celery-beat
   container is running: 2 running". It passes at 1.
4. **LOW, role reset: fixed.**
   - `medhub_app` has `rolsuper`, `rolreplication`, `rolbypassrls`, `rolcreaterole`, `rolcreatedb`
     and `rolinherit` all `f`.
   - On `audit_log` it has only `INSERT` and `SELECT`.
   - `REVOKE ALL` and the `GRANT` run in the same transaction.
5. **LOW, rollback text: fixed, with one inaccuracy (R2-2 below).**

### Deviations judged

- **(a) `CORS_ORIGINS: "${CORS_ORIGINS:-[]}"`: accepted.**
  - `[]` is the `Settings` default and the most restrictive value: no cross-origin is allowed.
    The backend received `[]` and started.
  - SR-041 AC 2 and the "no `:-`" rule apply to secret settings only, and `CORS_ORIGINS` is not a
    secret. The non-secret defaults (`OBJECT_STORE_BUCKET`, `REDIS_URL`, …) already follow this
    convention.
  - PRB-056 stays `open`. The template comment still says "Comma-separated list", which the
    backend rejects, and a run outside Compose is unchanged. See R2-1.
- **(b) Beat and `db-migrate` receive the object-store and at-rest keys: accepted, carried.**
  - Cause: `enforce()` and `Settings` require them in every Python process.
  - Neither service has a network path to the store: they are on `medhub` only, and the store is
    on the internal `object-store` network.
  - Narrowing this needs per-process settings, so it is a design change for TASK-201/202 and not
    a fix for this task. It is listed for the human below.
- **(c) Rehearsal: a reduced re-run is enough. Done by QA (project `qa191r`).**
  - **Old layout.** `git archive 3f0d017` with an `.env` built from *that commit's* template.
    Starting state: 0008, 2 rules, the application as the owner, API data plus 2000 extra
    `audit_log` rows.
  - **Upgrade.** Done by the DEPLOY.md steps with the round-2 tree: `pg_dump`, step 2 `.env` edit,
    `up --build db-migrate` (0008→0009, roles applied, exit 0, 10 s including the build), then
    `up -d --build`.
  - **Data unchanged.** The 14 table counts and the md5 of all `audit_log` and `account` rows are
    identical before and after.
  - **Checks.** Smoke 64/0. The owner password appears only in `postgres` and `db-migrate`.
    `UPDATE`, `DELETE` and `TRUNCATE` each return 42501.
  - **Pre-upgrade data.** Login 200; the old entry is found; the old attachment comes back
    byte-identical; logout 204.
  - **Why reduced is enough.** The round-2 change is environment plumbing only. The migration and
    role code was rehearsed in full in round 1.
- **(d) Allow-list maintenance: no test exists. Added as R2-3.**
  - Today every `Settings` field and every template key reaches a service. `TRUSTED_PROXIES` is
    fixed in Compose on purpose. Checked by diffing the template keys and `Settings.model_fields`
    against the interpolated names.
  - A future *required* field fails loudly at start-up.
  - A future *defaulted* field would be silently ignored, and so would an optional secret read
    from `os.environ` by `enforce()`, such as `OBJECT_STORE_SSE_KEY` or
    `AT_REST_ENCRYPTION_RETIRED_KEYS` (TASK-193/196).

### Round-2 findings (all LOW, none blocking)

- **R2-1 [LOW] PRB-056 does not record the Compose-path change.**
  - Location: `docs/problem-reports/PRB-056-empty-cors-origins-in-env-example-breaks-startup.md`
    ("Proposed resolution"); `infra/.env.example` `CORS_ORIGINS` comment.
  - Fix: add an interim note to PRB-056. Compose now defaults an empty value to `[]` (TASK-191);
    the template comment still says comma-separated; the PRB stays `open` until a task fixes the
    template or parsing.
- **R2-2 [LOW] The rollback sentence is wrong for the `pg_dump` path.**
  - Location: `infra/DEPLOY.md:282-284`.
  - Cause: roles are cluster-global. A `pg_restore` of the step-1 dump into the upgraded server
    keeps `medhub_app`; QA round 1 saw this. Only restoring the step-1 *volume copy* removes it.
  - Fix: "After restoring the step-1 volume copy the role is gone; after a `pg_restore` of the
    step-1 dump into the upgraded server it remains."
- **R2-3 [LOW] No test ties the allow-lists to `Settings`.**
  - Location: `infra/tests/test_compose_db_roles.py`
    (`test_each_application_service_gets_only_the_settings_it_reads`).
  - Fix: add a test with two checks:
    - every `Settings` field (upper-cased) and every name in `secret_settings.SECRET_SETTINGS` is
      in the environment of at least one Python service, or is in an explicit exception list
      (`TRUSTED_PROXIES` fixed, `DATABASE_OWNER_URL` in `db-migrate` only);
    - the fields without a default are in every Python service.
  - It can read `backend/app/core/config.py` statically, so it stays standard-library only.
  - Carry this to TASK-193/196, which add optional secrets.

### Verification run (QA, round 2)

| Command | Result |
|---|---|
| `uv run pytest --cov=app --cov-fail-under=85` | 1091 passed, 4 skipped, 93.89 % |
| DICOM tests | 25 passed |
| ruff / black / mypy | clean / 249 files unchanged / no issues in 130 files |
| `python3 -m unittest discover -s tests` (infra) | 71 OK |
| Smoke `qa191` (fresh, empty `CORS_ORIGINS`) | 64 passed, 0 failed |
| Smoke with the negative control (`env_file` on backend, 2 beats) | 3 FAIL (owner credential, exactly one beat, beat log line) |
| API flow through the proxy (`qa191`) | consent 201, list 200, entry 201/200, upload 201, download byte-identical, logout 204 |
| Reduced rehearsal `qa191r` | see (c) above; smoke 64/0 |
| Traceability on the 9 records | 0 errors, 18 warnings (unchanged from round 1) |

`infra/.env` sha256 `a4933b8c…c696da` before and after. `down -v` ran on `qa191` and `qa191r`.
The scratch dump was deleted. The volume and network lists are back to the pre-review snapshot,
and only `peaceful_pike` (`Created`) remains.

## Checkpoint C final result (QA engineer, 2026-11-01): PASSED

Checked across TASK-140, 197, 203, 198, 190 and 191 on stack `qa191` (round 2).

| Criterion | Result |
|---|---|
| Stack starts from the empty template with generated secrets | Met. `.env.example` was filled only with `openssl` values. All services came up: 8 running, 3 one-shots exited 0. Smoke 64/0 |
| Refuses a placeholder | Met, re-run in round 2 on the round-2 images: with `OBJECT_STORE_SECRET_KEY=change-me-…`, `db-migrate` (before any connection), `celery-worker` and `celery-beat` exit 1, and `backend` exits 3 (gunicorn worker boot failure), each naming the setting. Compose refuses an empty `DATABASE_OWNER_URL`, naming it |
| Every built image and running process non-root | Met for MedHub-built images: backend, worker and beat run as `medhub`, UID 999; frontend as 101 (smoke section 11). Pulled reverse-proxy master is UID 0, outside SR-041 AC 1, for the human to accept at release (PRB-007) |
| Runtime role cannot update `audit_log` | Met. UPDATE, DELETE and TRUNCATE each return 42501, `SET ROLE` is refused and there are no memberships. No application container holds the owner credential (by value), so the role is the only database identity the application has |
| TASK-191 rehearsal recorded | Met. It is recorded (rounds 1 and 2) and QA reproduced it in both rounds, including the round-1 rollback |
