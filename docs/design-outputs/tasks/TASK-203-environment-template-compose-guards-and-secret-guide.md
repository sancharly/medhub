---
id: "TASK-203"
type: task
title: "Empty environment template, required secrets in Compose, and a secret generation guide"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-01"
links:
  - target: "SR-041"
    relation: implements
  - target: "RISK-001"
    relation: mitigates
  - target: "RISK-005"
    relation: mitigates
  - target: "PRB-007"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "TASK-197"
    relation: relates_to
  - target: "ADD-026"
    relation: relates_to
tags: ["security", "deployment", "cr:CR-004", "control:design", "control:information"]
---

# TASK-203 — Empty environment template, required secrets in Compose, and a secret generation guide

- **Software item / unit:** SI-DEPLOY `U-DEP-Compose`, `U-DEP-EnvTemplate` (ADD-026).
- **PRB:** PRB-007. **CR:** CR-004.
- **Depends on:** TASK-140, TASK-197 (same files; the shared placeholder list). Ordered before
  TASK-191, TASK-198 and TASK-196, which edit the Compose file and template after it.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (`infra/docker-compose.yml`, `infra/.env.example`, `infra/DEPLOY.md`,
  `backend/tests/test_env_example.py`, 1 new infra test; TS-015)
- **Needs:** a Docker host for the bring-up checks.

## Objective

SR-041 AC 2 and AC 4: no default for any secret setting in the deployment definition; bring-up
fails with a message naming an unset or empty one; the template holds no secret value; the guide
says how to generate each. PRB-007 Investigation: `POSTGRES_PASSWORD` is unguarded and missing
from the template; `DATABASE_URL`, `SMTP_PASSWORD` and `AT_REST_ENCRYPTION_KEY` ship placeholders;
`backend` and `celery-worker` take everything from `env_file` without a guard.

## Implementation detail

1. `infra/docker-compose.yml`: `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}`;
   in `backend` and `celery-worker` `environment:`, every secret setting with a `:?` guard
   (`DATABASE_URL`, `AT_REST_ENCRYPTION_KEY`, the object-store keys). `SMTP_PASSWORD` cannot be
   conditionally required by Compose; it is passed through without a default and TASK-197's rule
   refuses it when `SMTP_USER` is set (Q-5). No `:-` default on any secret.
2. `infra/.env.example`: `POSTGRES_PASSWORD=`, `DATABASE_URL=`, `SMTP_USER=`, `SMTP_PASSWORD=`,
   `AT_REST_ENCRYPTION_KEY=` (all empty), each preceded by its generation command.
3. `infra/DEPLOY.md`: a "Secret settings" table (setting, used by, how to generate, rotation
   reference) that is the definition SR-041's Description points to.
4. `backend/tests/test_env_example.py`: the exception list that tolerates `changeme` in the
   database URL and SMTP password (`test_env_example.py:51-52`) is removed.

## Tests (write first)

- `infra/tests/test_compose_secrets.py`: parse the Compose file; every secret setting in every
  service that uses it is `${VAR:?…}`; no secret has `:-`; the secret list is the one in
  `backend/app/core/secret_settings.py`.
- `backend/tests/test_env_example.py`: every secret setting is present and empty; no value of
  the shared placeholder list appears anywhere in the file.
- Bring-up (manual, recorded): with `POSTGRES_PASSWORD` unset, `docker compose config` fails with
  a message naming it; same for `DATABASE_URL` and `AT_REST_ENCRYPTION_KEY`.

## Acceptance criteria

- [x] SR-041 AC 2: no default for any secret; unset or empty stops bring-up naming the setting
      (`infra/tests/test_compose_secrets.py`, bring-up record).
- [x] SR-041 AC 4: the template has no secret value and the guide says how to generate each
      (`backend/tests/test_env_example.py`, `infra/DEPLOY.md` review).

## Verification

```sh
cd infra && python3 -m pytest tests -v
cd backend && uv run pytest tests/test_env_example.py -v
docker compose -f infra/docker-compose.yml --env-file <filled .env without the POSTGRES_PASSWORD line> config   # expect: POSTGRES_PASSWORD must be set
```

## Records

- **TS-015**: TC-015.2 (Compose guards, bring-up refusal), TC-015.4 (template, guide).
- **PRB-007**: Resolution started; `resolved` by TASK-196, the last PRB-007 task.

## Definition of Done

- [x] Infra and backend tests pass; bring-up refusals recorded.
- [x] TS-015 `in_review`.
- [x] `traceability-check` shows no error for TASK-203, TS-015, SR-041.

## Implementation notes (software developer, 2026-11-01)

- `infra/docker-compose.yml`: `:?` guard on `POSTGRES_PASSWORD`; `backend` and `celery-worker`
  `environment:` guard `DATABASE_URL`, `AT_REST_ENCRYPTION_KEY` (and, for the worker, the two
  object-store keys; the backend already had them). `SMTP_PASSWORD` is not in `environment:`:
  `env_file` passes it and the application refuses it when `SMTP_USER` is set. No `:-` on a secret.
- `infra/.env.example`: `POSTGRES_PASSWORD`, `DATABASE_URL`, `SMTP_USER`, `SMTP_PASSWORD`,
  `AT_REST_ENCRYPTION_KEY` empty, each with its generation note. `infra/DEPLOY.md`: "Secret
  settings" table and the list of what refuses what.
- Tests: new `infra/tests/test_compose_secrets.py` (unittest, like the other infra tests, not
  pytest; the Verification command above is run as `python3 -m unittest discover -s tests`);
  `backend/tests/test_env_example.py` (exception list removed, three tests added);
  `backend/tests/test_config.py::test_validation_error_never_echoes_a_rejected_value` (carried
  item 1, with negative control); `compose_config` in `test_compose_object_store.py` now ignores
  the caller's own secret variables and `GOOD` has a `DATABASE_URL`.
- Carried items: baseline test password changed from `pass` to a distinctive value in
  `backend/tests/conftest.py` and `backend/modules/dicom_viewer/tests/conftest.py` (CI needs no
  change); PRB-007 interim note reworded (1.4); PRB-061 created; CR-004 1.2 and TASK-191 1.1
  updated.
- Bring-up record: with each of `POSTGRES_PASSWORD`, `DATABASE_URL`, `AT_REST_ENCRYPTION_KEY`
  unset and empty, `docker compose config` exits non-zero with `<NAME> must be set`; the unfilled
  template alone is refused. No started stack was needed (Compose stops at interpolation).
- Operator-facing: an unfilled `.env` no longer starts; `infra/smoke-test.sh` copies the empty
  template when there is no `infra/.env` and now fails at its first check (TASK-191 edits that
  file).

## QA review round 1 (QA engineer, 2026-11-01): CHANGES REQUESTED

TASK-203 `in_review → draft`. TS-015 1.1 stays `in_review`: it is not approved while a finding is
open. The rest of the task is sound:
- The Compose guards are complete: `backend`, `celery-worker`, `postgres`, the preflight, the
  store and the initialiser. No `:-` default is left on a secret, and there is no beat service
  yet (PRB-061).
- The template is empty, and the TS-015 test content is right.
- TASK-197 findings 1, 3 and 4 are closed.

### Findings

1. **HIGH — the CI "Object Store Integration" job can no longer bring the store up.**
   - Where: `.github/workflows/ci.yml:238-251` writes only `OBJECT_STORE_ACCESS_KEY`,
     `OBJECT_STORE_SECRET_KEY`, `OBJECT_STORE_BUCKET` and `AT_REST_ENCRYPTION_KEY` to
     `infra/.env`, then runs `$COMPOSE up -d --build --wait object-store-preflight object-store
     object-store-init`.
   - Why it breaks: Compose interpolates the whole file, not only the named services. The new
     guards (`infra/docker-compose.yml:65-66,111,219-220`) therefore stop the command.
   - Reproduced: with exactly the CI variables, `docker compose -p qa203 -f
     infra/docker-compose.yml -f infra/compose.ci-object-store.yml --env-file <ci.env> config
     object-store-preflight object-store object-store-init` exits 15 with `required variable
     DATABASE_URL is missing a value`. `up --dry-run` also exits 15, on `POSTGRES_PASSWORD`. The
     `HEAD` Compose file with the same env exits 0.
   - Why the tests miss it: `test_compose_object_store.GOOD` now holds every variable, so no test
     renders the CI env.
   - → Fix the CI step and add a test:
     - In "Generate throwaway credentials", generate `pg=$(openssl rand -hex 24)` and mask it.
       Write `POSTGRES_PASSWORD=$pg` and `DATABASE_URL=postgresql://medhub:$pg@postgres:5432/medhub`.
     - Add an infra test that reads the `NAME=` lines that step writes (parse `ci.yml`). The test
       asserts that `docker compose config` with exactly those names, plus throwaway values,
       renders `object-store-preflight`, `object-store` and `object-store-init`. Then a future
       guard cannot break the job unseen.
     - Record the result in TS-015 TC-015.2.
2. **LOW — the documented check command names a different setting.**
   - Where: `infra/DEPLOY.md:50` and this task's Verification (line 83).
   - `env -u POSTGRES_PASSWORD docker compose -f infra/docker-compose.yml --env-file /dev/null
     config` stops at `DATABASE_URL`, the first missing variable. It never reaches
     `POSTGRES_PASSWORD`. Verified: exit 15, `services.backend.environment.DATABASE_URL`.
   - → Say "fails, naming the first missing setting". Or use a filled env file with one line
     removed, which is what the infra test does.
3. **LOW — the guide contradicts itself on reusing a value** (`infra/DEPLOY.md:26`). It says
   "never reuse a value for two settings", while the table requires the `DATABASE_URL` password
   to equal `POSTGRES_PASSWORD`. → Add "except the password inside `DATABASE_URL`, which is
   `POSTGRES_PASSWORD`".

### Checks (coordinator questions)

1. **Guards.** Every service that reads a secret guards it with `:?`. `SMTP_PASSWORD` comes only
   through `env_file`; the application still refuses it missing when `SMTP_USER` is set (TASK-197
   tests). The static and bring-up tests catch the three mutations below.
2. **`DATABASE_URL` vs `POSTGRES_PASSWORD`.** Nothing checks that they match; there is only
   documentation. A mismatch fails closed: alembic and the API cannot authenticate, and the
   driver error does not print the password. Accepted. Carried to TASK-191: the runtime role's
   password will differ from `POSTGRES_PASSWORD`, so that table row must be rewritten then.
3. **Smoke test.** `ci.yml` never runs `infra/smoke-test.sh`, so its failing first check without
   an `infra/.env` (the copied template is empty) breaks no pipeline. Deferral accepted; carried
   to TASK-191/198: config-only validation should copy the template with throwaway values filled
   in.
4. **`.errors()`.** Nothing on the start-up or logging path calls `.errors()` on a settings
   error. The only call, `app/api/errors.py:151`, is the HTTP `RequestValidationError` handler,
   which returns `loc`, `type` and `msg`, never `input`. A pydantic-settings source error (bad
   `CORS_ORIGINS` JSON with a sentinel) prints `error parsing value for field "cors_origins" from
   source "EnvSettingsSource"`; the full chained traceback holds no sentinel.
5. **PRB-061.**
   - The contract is met: Investigation with file:line (spot-checked Dockerfile:21,
     entrypoint.sh:4,8, `celery_app.py:25,47`, `lifecycle.py:63`, `session_tasks.py:51`); Safety
     evaluation per SR; `major` justified; no release, so no notification.
   - The CR-004 1.2 edit is limited to the `resolves` link, the Scope row, D-3 and its history
     line.
   - TASK-191 1.1 item 7, the AC and the Records match D-3, and fold in my TASK-197 C1.
   - Carried to TASK-202: RISK-008's cause already names "a retention sweep fails silently", but no
     control row covers "the sweep is scheduled and runs in the deployed stack". Add PRB-061 and
     the TASK-191 started-stack evidence as that control and its verification before re-scoring.
6. **DEPLOY.md table.**
   - Matches `secret_settings.py`: the required four plus `SMTP_PASSWORD`, conditional; the three
     optional ones checked only when set.
   - Matches the template: the six secrets are present and empty.
   - The "used by" columns match Compose.
   - Only findings 2 and 3 apply.

### Negative controls (scratch copy)

| Mutation | Result |
|---|---|
| `${POSTGRES_PASSWORD:-x}` | 5 static and bring-up tests fail |
| `celery-worker` `AT_REST_ENCRYPTION_KEY` guard removed | `test_services_that_use_a_secret_guard_it_in_environment` fails (and the render test) |
| literal `POSTGRES_PASSWORD` | 5 fail |
| value written into the template's `AT_REST_ENCRYPTION_KEY=` | 2 template tests fail |
| `hide_input_in_errors` removed | `test_validation_error_never_echoes_a_rejected_value` fails |

### Verification run

| Command | Result |
|---|---|
| `uv run pytest tests/test_config.py tests/test_env_example.py tests/core tests/test_lifespan.py tests/audit` | 321 passed |
| `uv run pytest --cov=app --cov-fail-under=85` | 1056 passed, 4 skipped; coverage 94.13 % |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `ruff`, `black --check`, `mypy app` | clean; 246 files unchanged; no issues in 128 files |
| `cd infra && python3 -m unittest discover -s tests` | 45 OK (`BringUpRefusal` ran, not skipped); `infra/.env` checksum unchanged |
| OpenAPI export vs `backend/openapi/openapi.json` | identical |
| `docker compose config` with the bare template | exit 15, names `OBJECT_STORE_ACCESS_KEY` |
| `docker compose config` with the CI job's variables (new vs `HEAD` Compose) | exit 15 vs 0 (finding 1) |
| traceability (TASK-203, TS-015, PRB-007, PRB-061, CR-004, TASK-191, SR-041) | 0 errors, 7 warnings, none new for this task: W5 TASK-197 and TASK-185 → ADD-026 `in_review`; W5 ADD-005 → SOUP-004/005 `in_review`; W6 CR-002 → SOUP-022/023 obsolete; W1 SR-043 no TS (TS-017 planned) |

### Round 2 (software developer, 2026-11-01)

Answers "QA review round 1".

1. **[HIGH] CI "Object Store Integration" job.** `.github/workflows/ci.yml` step "Generate
   throwaway credentials" now generates `pg=$(openssl rand -hex 24)`, masks it, and writes
   `POSTGRES_PASSWORD=$pg` and `DATABASE_URL=postgresql://medhub:$pg@postgres:5432/medhub` (user
   and database as in the Compose `postgres` service). It is the only CI job that runs Compose.
   New `infra/tests/test_ci_compose_env.py` parses the `NAME=` lines of that step and runs
   `docker compose config` with the job's two `-f` files, exactly those names and throwaway
   values; it asserts the three object-store services render. Negative control: with the
   `POSTGRES_PASSWORD` line deleted from the step, two tests fail (exit 15, "POSTGRES_PASSWORD
   must be set"); restored, they pass. Recorded in TS-015 TC-015.2.
2. **[LOW]** `infra/DEPLOY.md` and the Verification command above now say Compose names the first
   missing setting and use a filled env file with one line removed.
3. **[LOW]** `infra/DEPLOY.md` states the one exception to "never reuse a value": the password in
   `DATABASE_URL` equals `POSTGRES_PASSWORD`.

## QA review round 2 (QA engineer, 2026-11-01): APPROVED

Round-1 findings 1 to 3 are closed. TASK-203 `in_review → approved`; TS-015 1.1
`in_review → approved`.

- **Finding 1 (HIGH), closed.**
  - In `.github/workflows/ci.yml:245-246` the new `add-mask` comes before anything that could
    print the value. The `{ … } > infra/.env` block writes to the file, not to the log, and
    `DATABASE_URL` contains only the masked `$pg`.
  - The only Compose user in CI is this job (`ci.yml:232`).
  - The round-1 probe, re-run with the new step's six variables (`config` on the three services,
    both `-f` files, `env -i`), now exits 0. It exited 15 before.
  - `infra/tests/test_ci_compose_env.py` parses the real workflow file (`ROOT/.github/workflows/ci.yml`)
    and uses the job's two Compose files.
  - My control: deleting the step's `DATABASE_URL` line makes 2 of its 3 tests fail.
- **Finding 2 (LOW), closed.** `infra/DEPLOY.md:47-51` now says Compose names the first missing
  setting. Verified: a filled CI env with the `POSTGRES_PASSWORD` line removed is refused, naming
  `POSTGRES_PASSWORD`.
- **Finding 3 (LOW), closed.** `infra/DEPLOY.md:26-27` states the exception.

### Observation (not blocking)

- **LOW.** The test hard-codes the Compose files and `STORE_SERVICES`
  (`infra/tests/test_ci_compose_env.py:20-22`); it does not parse them from the job's `COMPOSE`
  value and its `up` line.
  - My control: adding `backend` to the job's `up` list still passes.
  - Harmless today, because Compose resolves variables across the whole file, so the service list
    cannot change the outcome.
  - → When the job's command next changes, parse `COMPOSE` and the `up` arguments, and assert
    that they equal the constants.

### Verification run

| Command | Result |
|---|---|
| `cd infra && python3 -m unittest discover -s tests` | 48 OK (the 3 new tests ran); `infra/.env` checksum unchanged |
| `uv run pytest tests/test_config.py tests/test_env_example.py` | 16 passed |
| `uv run pytest --cov=app --cov-fail-under=85` | 1056 passed, 4 skipped; coverage 94.13 % |
| `uv run pytest modules/dicom_viewer/tests` | 25 passed |
| `ruff`, `black --check`, `mypy app` | clean; 246 files unchanged; no issues in 128 files |
| `docker compose ... config object-store-preflight object-store object-store-init` with the CI variable set | exit 0 (round 1: 15) |
| traceability (TASK-203, TS-015) | 0 errors; 1 warning: W5 TASK-197 → ADD-026 `in_review` (pre-existing) |
