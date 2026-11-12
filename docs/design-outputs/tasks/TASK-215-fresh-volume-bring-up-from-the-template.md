---
id: "TASK-215"
type: task
title: "Record a fresh-volume bring-up from the environment template"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-12"
updated: "2026-11-13"
links:
  - target: "SR-041"
    relation: implements
  - target: "RISK-001"
    relation: mitigates
  - target: "CR-005"
    relation: relates_to
  - target: "PRB-038"
    relation: relates_to
  - target: "TASK-203"
    relation: relates_to
  - target: "TASK-214"
    relation: relates_to
tags: ["deployment", "verification", "cr:CR-005", "control:design"]
---

# TASK-215 — Record a fresh-volume bring-up from the environment template

- **Software item / unit:** SI-DEPLOY `U-DEP-Compose`, `U-DEP-EnvTemplate` (ADD-026).
- **PRB:** PRB-038. **CR:** CR-005 (AC-9; Q-1: verification only, no code change).
- **Depends on:** TASK-214 (the bring-up runs the final backend image, so its log also confirms
  AC-8 on a fresh volume).
- **Branch:** `bug/build-hygiene`.
- **Size:** XS (no source file; PRB-038 and this record).
- **Needs:** a Docker host.

## Objective

Show on a fresh volume that the template fixed by CR-004 TASK-203 (commit `4b1daf5`) brings the
stack up with `POSTGRES_PASSWORD`, and that an empty value stops Compose naming it (SR-041 AC 2,
AC 4). This closes the records gap of PRB-038; nothing is changed.

## Procedure

1. A scratch copy of `infra/` (or `-p task215` with a scratch env file), so the developer's
   `infra/.env` and volumes are untouched; check `docker volume ls` has no `task215_*` volume.
2. `.env` = `infra/.env.example` with only the required secret values filled, each generated with
   the command the template names. `DATABASE_OWNER_URL` uses the generated `POSTGRES_PASSWORD`;
   `DATABASE_URL` uses the runtime role and its own password (`infra/DEPLOY.md`).
3. `docker compose -p task215 up -d --build --wait` → exit 0; `postgres` initialised a new
   cluster (log line "database system is ready", no "Database directory appears to contain a
   database"); `db-migrate` exited 0.
4. `COMPOSE_PROJECT_NAME=task215 infra/smoke-test.sh` → every check passed, 0 failed (80 checks at
   HEAD; record the actual count).
5. The same `.env` with `POSTGRES_PASSWORD=` (empty): `docker compose -p task215 config` stops with
   `POSTGRES_PASSWORD must be set`.
6. `docker compose -p task215 down -v`; `docker volume ls` shows no `task215_*` volume and the
   developer's volumes as before.

## Acceptance criteria

- [x] CR-005 AC-9: steps 3, 4 and 5 give the stated results; outputs recorded below; teardown
      leaves no `task215` resource.
- [x] Records: PRB-038 `## Resolution` cites TASK-203 and commit `4b1daf5` as the fix and this
      task as the verification (Q-1); `resolved` only after QA approves.

## Verification

The procedure above is the verification. QA repeats steps 3 to 5 on its own scratch project.

## Verification results (Software Developer, 2026-11-13)

Files changed: this record and `docs/problem-reports/PRB-038-postgres-password-missing-from-env-example.md`
(`## Resolution`, 1.2; stays `open`). No source file. Run on `a85d8f7` (HEAD, clean tree).

**Setup and deviations from a literal fresh `infra/.env`.** The developer's MedHub stack was running
(`infra_*` volumes, ports 80/443, subnet 10.77.77.0/24) and was not touched. A scratch tree
`<s>` = `/private/tmp/claude-501/-Users-carlos-santiago--claude-spares-spare-24NrGN/090e43af-a2e3-49b6-80c7-2e35c85eed7d/scratchpad/s215`
(outside the repository) holds: `<s>/infra` = copy of `infra/` without `.env` and `tests/`;
`<s>/backend` and `<s>/frontend` = symlinks to the repository's, so the `../backend` and
`../frontend` build contexts are the repository's; `<s>/infra/.env` = `infra/.env.example` with only
`POSTGRES_PASSWORD`, `DATABASE_OWNER_URL`, `DATABASE_URL`, `OBJECT_STORE_ACCESS_KEY`,
`OBJECT_STORE_SECRET_KEY`, `AT_REST_ENCRYPTION_KEY`, `AT_REST_ENCRYPTION_KEY_ID` (`k1`) and
`OBJECT_STORE_SSE_KEY` filled (generated with the template's `openssl` commands; the runtime
password differs from `POSTGRES_PASSWORD`). Deviations:

1. `<s>/infra/docker-compose.yml` differs from `infra/docker-compose.yml` only in host ports
   `18080:80` / `18443:443`, the `medhub` subnet 10.78.78.0/24 (ip_range 10.78.78.128/25), the
   proxy address 10.78.78.2 and `TRUSTED_PROXIES: 10.78.78.2` (the live stack held 80/443 and
   10.77.77.0/24; diff checked).
2. `infra/smoke-test.sh` cannot be pointed at another project without editing it: it resolves
   `COMPOSE_FILE` and `.env` from its own directory and posts to the fixed `https://localhost/`
   (the developer's stack). It was **not edited**; the scratch copy `<s>/infra/smoke-test.sh` differs
   only in `https://localhost/` to `https://localhost:18443/` (10 lines). Run from `<s>/infra`, it
   therefore reads the scratch Compose file and `.env`.
3. The scratch directory has no `.env` of the developer's; the `.env` is the generated one above, in
   `<s>/infra`, so no `--env-file`/`--project-directory` was needed.
4. The smoke script's own result is 78 checks, not the 80 estimated in the plan (no check was skipped:
   no `[SKIP]` and no `[FAIL]` line).

**Commands** (all from `<s>/infra`):

```sh
docker volume ls -q | grep -c task215                      # 0 before
docker compose -p task215 up -d --build --wait             # exit 0 (49 s, images built)
docker compose -p task215 logs --no-color postgres | grep -E 'init process complete|ready to accept'
docker inspect task215-db-migrate-1 --format '{{.State.ExitCode}}'      # 0
COMPOSE_PROJECT_NAME=task215 bash ./smoke-test.sh          # exit 0
cp .env ../env.empty && sed -i '' 's/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=/' ../env.empty
docker compose -p task215 --env-file ../env.empty config   # exit 15
docker compose -p task215 down -v --rmi local
```

**Step 3 (AC-9).** `up -d --build --wait` exit 0; every service `Healthy`, `db-migrate`,
`object-store-init` and `object-store-preflight` `Exited` (0). `postgres` log: new cluster
(`initdb: warning: enabling "trust" authentication for local connections`, "PostgreSQL init process
complete; ready for start up", "database system is ready to accept connections"); no "Database
directory appears to contain a database". `db-migrate` exit 0, last lines: "Running upgrade 0009 ->
0010 ...", "database roles applied for runtime role medhub_app", "field-encryption key ids verified".
Backend log: `grep -cE 'Control server error|\[ERROR\]'` = 0 (AC-8 on a fresh volume, TASK-214).

**Step 4.** `=== Results: 78 passed, 0 failed ===` (78 `[PASS]` lines, no `[FAIL]`, no `[SKIP]`).

**Step 5.** With `POSTGRES_PASSWORD=` empty (`env.empty` = the same `.env`, one line changed),
`docker compose config` (and `up -d --no-start`) stopped with exit 15:

```
error while interpolating services.postgres.environment.POSTGRES_PASSWORD: required variable POSTGRES_PASSWORD is missing a value: POSTGRES_PASSWORD must be set
```

**Step 6.** `down -v --rmi local` removed the containers, `task215_postgres_data`, `task215_redis_data`,
`task215_object_store_data`, the networks `task215_medhub` and `task215_object-store` and the
`task215-*` images. After: 0 `task215` containers, networks and volumes; `docker volume ls` shows
only `infra_object_store_data`, `infra_postgres_data`, `infra_redis_data` as before, and the 8
`infra-*` containers of the developer's stack still running. `git status` clean (no repository file
changed by the bring-up).

Not done: `traceability-check` was not run by this role; PRB-038 stays `open` (QA moves it).

## QA review (2026-11-13): APPROVED

No CRITICAL, HIGH or MEDIUM finding. The LOW findings below do not block.

**78 versus 80.** `infra/smoke-test.sh` at `a85d8f7` has no fixed number of checks: sections 11
and 12 add checks per container. For the stack as shipped (8 running containers: reverse-proxy,
backend, frontend, postgres, redis, object-store, celery-worker, celery-beat; 3 exited one-shot
built services) the count is 78:

| Section | Checks |
|---|---|
| 1-9 (static, plus the login probe) | 20 (1 + 9 services + 1 + 3 + 2 + 3 volumes + 1) |
| 10 object-store isolation | 8 (5 probes + backend reaches + round trip + no host port) |
| 11 non-root | 16 (7 built images: 1 each; the 4 running ones +2 each for PID 1 and `id -u`; SPA) |
| 12 roles and processes | 31 (16 fixed + 7 owner-credential checks + 8 encryption-key checks; 2N - 1 for N = 8 running) |
| 14 activation token | 3 |

The only checks that do not run on a fully started stack are the `[SKIP]` branches (stack down,
`curl` missing), the per-service "publishes external ports" FAIL lines in section 3 (written only on
failure), the "login reachable" variant of check 9 and the "is running (restart: ...)" FAIL of section
11. None is skipped by design on a healthy stack: 78 `[PASS]`, no `[SKIP]`, in both runs.
"80" comes from CR-004 TASK-202 (`:210-211`, `:240`): the QA project `qa202` had a scratch
`smtp-catcher` container, which adds the two per-container checks of section 12. The script has not
changed since TASK-207 (`b905560`), and TASK-202 already recorded 78 for the shipped stack. AC-9's
criterion ("every check passed and 0 failed") is met; the count is informational.

**Scratch copy of the smoke test.** `sed 's#https://localhost:18443/#https://localhost/#g'` over
`<s>/infra/smoke-test.sh` is byte-identical (`cmp`) to `infra/smoke-test.sh` at HEAD. 9 lines differ
(`:154`, `:291`, `:539-541`, `:543`, `:545-547`), all host and port of a `curl` URL. The scratch
`docker-compose.yml` differs only in the ports, subnet, `ip_range`, proxy address and
`TRUSTED_PROXIES` (normalised and `cmp`-identical). Every other `infra/` file used matches HEAD.
The URL is the environment, not the logic under test, and the HEAD script cannot reach another
project's proxy without stopping the developer's stack. So this evidence is acceptable for AC-9.

**Independent reproduction (QA, project `qa215`).** `git archive a85d8f7 backend frontend infra`
into a scratch directory (no symlink to the working tree). A fresh self-signed certificate was
generated in `infra/certs/`. Ports 28080/28443, subnet 10.79.79.0/24 and proxy 10.79.79.2 were set,
and `https://localhost/` became `https://localhost:28443/` in the smoke script copy. The `.env` was
built from `.env.example` with only the 8 required secrets set, each from the template's `openssl`
command, with the runtime password different from `POSTGRES_PASSWORD`. `config` showed
`qa215_*` volumes and networks; none existed before.
- `docker compose -p qa215 up -d --build --wait`: exit 0 (115 s). Every long-running service was
  `Healthy`; `db-migrate`, `object-store-init` and `object-store-preflight` were `exited 0`.
- `postgres` log: `initdb: warning: enabling "trust" ...`, "PostgreSQL init process complete; ready
  for start up", "database system is ready to accept connections"; no "appears to contain a
  database". `db-migrate` (owner URL with the generated `POSTGRES_PASSWORD`) ran 0001 to 0010, then
  "database roles applied for runtime role medhub_app" and "field-encryption key ids verified".
- `COMPOSE_PROJECT_NAME=qa215 bash ./smoke-test.sh`: `=== Results: 78 passed, 0 failed ===`, exit 0,
  no `[SKIP]`, no `[FAIL]`.
- AC-8 on the fresh volume: backend `Config.Cmd` includes `--no-control-socket`. A login through
  the proxy (`POST https://localhost:28443/api/v1/auth/login`) was answered `401`. After it, the
  backend log had `grep -cE 'Control server error|\[ERROR\]'` = 0.
- `POSTGRES_PASSWORD=` (one line changed, `env -i` so no shell value leaks in): `config` and
  `up -d --no-start postgres` both exit 15 with `required variable POSTGRES_PASSWORD is missing a
  value: POSTGRES_PASSWORD must be set`. The running `qa215-postgres-1` was not recreated. With the
  line removed, the result is the same.
- `docker compose -p qa215 down -v --rmi local`: 0 `qa215` containers, volumes, networks and images
  left. The developer's 8 `infra-*` containers have the same `StartedAt` as before the run, and the 3
  `infra_*` volumes are unchanged.

**PRB-038 Resolution.** It is accurate. It cites TASK-203 and `4b1daf5` as the fix and this task as
the verification (Q-1). The claims about `.env.example`, the `:?` guard and `DEPLOY.md:27-34` match
HEAD. The run can be reproduced from the command forms here. Its status sentence is reworded at
`resolved`.

**LOW findings (not blocking; for TASK-216's records pass):**
- **[LOW 1] "80 checks at HEAD" is wrong.** The text is at
  `docs/change-requests/CR-005-reproducible-build-test-and-deployment-configuration.md:232` (AC-9)
  and in this task's procedure step 4. Deviation 4 also calls 80 "estimated in the plan". → In
  CR-005 AC-9 write "At HEAD that is 78 checks for the stack as shipped (the count grows by two per
  extra running container; TASK-202's 80 included a scratch `smtp-catcher`)", with a dated
  change-log line. Step 4 of this task is read with this note; it is not rewritten after the run.
- **[LOW 2] Wording slips in the deviations.** Deviation 2 says the smoke copy differs in "10
  lines"; it is 9 (`diff` groups the unchanged comment `:542` into the hunk). The copied `infra/`
  also carried the developer's untracked `infra/certs/` (the dev certificate), which is not listed.
  → Read "9 lines" and add "and `infra/certs/` (untracked dev certificate)" at the next revision.
  QA's run used a freshly generated certificate, so the result does not depend on it.

**Checkpoint B (CR-005 Plan, after tasks 4-6, started stack): passed.**
- `python3 -m unittest discover -s infra/tests`: `Ran 163 tests ... OK`. `python3 infra/check_image_pins.py`: exit 0.
- Negative controls, run in a scratch git copy of `a85d8f7`, one at a time, reset between them. Each
  one is red and names the file and line:
  - `actions/checkout@v4` → `ci.yml:15: action not pinned to a commit SHA`.
  - `pip install uv` in CI → `ci.yml:23`; in `backend/Dockerfile` → `Dockerfile:3: uv install without an exact version`.
  - `python-version: "3.12"` → `ci.yml:20: python-version without a full patch version`.
  - `POSTGRES_IMAGE = "postgres:16"` → `backend/postgres_image.py:13: test image without @sha256 digest`.
  - Compose `postgres` digest changed → `ci.yml:51: CI service image differs from infra/docker-compose.yml:126`.
  - `--no-control-socket` removed → `FAIL: test_cmd_starts_gunicorn_without_the_control_socket`
    (163 run, 1 failure).
- Fresh-volume stack from the template: started; smoke test 78 passed, 0 failed; the backend log
  has no ERROR line (above).
- `traceability-check` (two-hop CR-005 scope, 171 records): 0 errors, 33 warnings (the known W5
  approved-on-`in_review` links to ADD-024, ADD-026, SOUP-001, SOUP-005, TS-013, and the
  pre-existing W6 links to obsolete records). PRB-038 at `resolved` has its incoming `resolves` link
  from CR-005 (E9).

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
- 1.1 (2026-11-13) — Verification run recorded (78 passed, 0 failed; empty password stops Compose); `draft → in_review` (Software Developer role).
- 1.2 (2026-11-13) — QA review: APPROVED (2 LOW, non-blocking, above); 78-vs-80 explained; Checkpoint B passed. `in_review → approved`; boxes ticked; PRB-038 `open → resolved`.
