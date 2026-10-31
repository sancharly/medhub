---
id: "TASK-179"
type: task
title: "Check encryption end to end against the real object store in CI"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-022"
    relation: implements
  - target: "SR-028"
    relation: implements
  - target: "RISK-012"
    relation: mitigates
  - target: "RISK-011"
    relation: mitigates
  - target: "CR-002"
    relation: relates_to
  - target: "PRB-036"
    relation: relates_to
  - target: "TASK-175"
    relation: relates_to
  - target: "TASK-177"
    relation: relates_to
tags: ["encryption", "ci", "verification", "cr:CR-002", "issue:sancharly/medhub#33", "control:protective"]
---

# TASK-179 — Check encryption end to end against the real object store in CI

- **Software item / unit:** SI-ATTACH `ObjectStorageClient` (ADD-012); SI-DEVINFRA
  `U-INF-CIPipeline` (ADD-024)
- **Depends on:** TASK-175 (default encryption) and TASK-177 (the final network), as
  `relates_to` links. TASK-176 is reached through TASK-177.
- **Branch:** `bug/minio-object-store`
- **Size:** S (1 test module, a pytest marker, 1 Compose override, 1 CI job, TS-008, PRB-036; plus the two TASK-177 QA carry-overs in `infra/smoke-test.sh`)
- **Needs:** network access (CI on the branch head). A Docker host for the local run.

## Objective

Resolve PRB-036 and implement SR-022 AC 5. On every pull request, an automated check writes
through `ObjectStorageClient.put_object` to a real object store, asserts
`ServerSideEncryption: AES256` on the stored object, and reads the original bytes back. It also
re-checks AC-4 (bucket default encryption, plain upload encrypted) on a fresh amd64 runner, which
is CI evidence for AC-9.

**Q-4 (human, 2026-10-30): a CI job, because the image can be pulled in CI.** A GitHub Actions
`services:` container cannot take a command or arguments, and the server needs its command line
from TASK-172. The job therefore starts the store with the real Compose file plus a CI-only
override, as a job step. This is the CI form of Q-4's answer, not a smoke-test step.

## Interfaces to honor

- `infra/compose.ci-object-store.yml` (CI only) does two things: it attaches `object-store` to an
  extra non-internal network, and it publishes the S3 port on `127.0.0.1` only. That is needed
  because an `internal` network cannot publish (TASK-177). It adds no image, and the pin check
  covers it. The production file stays unchanged.
- Credentials: the job generates throwaway values that pass the TASK-174 rule
  (`openssl rand`), writes them to an env file, and masks them (`::add-mask::`). No secret is
  stored in the repository.
- Test module: `backend/tests/integration/test_object_store_sse.py`, marker `object_store`,
  registered in `backend/pyproject.toml`. It is skipped unless `OBJECT_STORE_INTEGRATION=1`, so
  the normal suite and the `backend-tests` job are unchanged.

## Implementation detail

1. Tests (`verifies` SR-022 AC 4 and AC 5):
   - `ObjectStorageClient().put_object(key, data, "application/octet-stream")`. Then a raw
     boto3 `head_object` reports `ServerSideEncryption == "AES256"`, and `get_object` equals the
     original data.
   - `get_bucket_encryption` has an `AES256` rule.
   - A raw boto3 `put_object` with no SSE argument is reported `AES256`.
   - Clean up the test keys.
2. Add the CI job `object-store-integration`:
   - check out the code and generate the env file;
   - `docker compose -f infra/docker-compose.yml -f infra/compose.ci-object-store.yml up -d
     --wait object-store-preflight object-store object-store-init`;
   - `cd backend && uv sync --frozen`, then
     `OBJECT_STORE_INTEGRATION=1 OBJECT_STORE_ENDPOINT=http://127.0.0.1:<port> uv run pytest -m
     object_store -v`;
   - always run `docker compose down -v` at the end. The volume is disposable here.
3. **TS-008** TC-008.8: the CI job and its three assertions. **ADD-024** gets the new job in
   `U-INF-CIPipeline` (TASK-180 records it).
4. **PRB-036** → `resolved`, with a `## Resolution` that names the job and the test module.

## Acceptance criteria

- [x] CR-002 **AC-7** / SR-022 AC 5: the check writes through `put_object` to a real store,
      asserts `AES256` and reads back the original bytes. It runs in CI on every pull request and
      is listed in TS-008.
- [ ] CR-002 **AC-4** re-checked in CI. **AC-9** CI part: the store is pulled and started on a
      fresh amd64 runner.
- [x] CR-002 **AC-19** (PRB-036 part): PRB-036 is `resolved`.
- [x] CR-002 **AC-15** (SR-022 part): TS-008 `verifies` SR-022 and lists TC-008.6 and TC-008.8.

## Verification

```sh
python3 infra/check_image_pins.py
# CI ONLY. These commands write infra/.env and end with `down -v`: by hand, back up infra/.env
# first and keep the project name, so the dev project `infra` and its volumes are not touched.
# The job's steps: generate infra/.env, then
docker compose -p medhub-ci -f infra/docker-compose.yml -f infra/compose.ci-object-store.yml up -d --build --wait object-store-preflight object-store object-store-init
cd backend && set -a; . ../infra/.env; set +a; OBJECT_STORE_INTEGRATION=1 OBJECT_STORE_ENDPOINT="http://127.0.0.1:${OBJECT_STORE_CI_PORT:-8333}" uv run pytest -m object_store -v
docker compose -p medhub-ci -f infra/docker-compose.yml -f infra/compose.ci-object-store.yml down -v
cd backend && uv run pytest     # integration test skipped, rest unchanged
```

CI on the branch head: `object-store-integration` is green. Also show that the test fails when
`ServerSideEncryption` is removed from `put_object` and the bucket default is not set. Use a
scratch run, and record it.

## Definition of Done

- [ ] The new CI job and every existing job are green on the branch head.
- [x] `traceability-check` shows no error for this task, TS-008 and PRB-036.

## Verification results (software developer, 2026-10-30)

**Hosted-runner run: PENDING.** GitHub Actions cannot run from this session. Everything below is a
local reproduction of the job's own steps; the job is green on the branch head only once the branch
is pushed (TASK-182 covers it). The Definition of Done item "new CI job green on the branch head" and
the amd64-runner part of AC-9 stay open until then.

### Files

- `.github/workflows/ci.yml`: new job `object-store-integration`.
- `infra/compose.ci-object-store.yml` (new, CI only): extra non-internal network `ci-publish` for the
  store and port `127.0.0.1:${OBJECT_STORE_CI_PORT:-8333}:8333`. No image.
- `backend/tests/integration/test_object_store_sse.py` (new, with `__init__.py`), marker
  `object_store` registered in `backend/pyproject.toml`.
- `infra/tests/test_compose_object_store.py`: new test for the override (no image, one non-internal
  network, loopback port only, `object-store` network still internal, only proxy and store publish).
- `infra/smoke-test.sh`: the two TASK-177 carry-overs (below).
- TS-008 (TC-008.8, `in_review`, 1.4), PRB-036 (`resolved`, 1.2).
- ADD-024 is not edited here: TASK-180 records the job and the override in `U-INF-CIPipeline` and
  clears the approval.

Notes: the job writes `infra/.env` (needed because Compose validates `env_file: .env` for the whole
project) with generated, masked values, so on a developer machine the job's steps overwrite a real
`infra/.env`; run them only in CI or with the file backed up. The test module re-reads the real
`OBJECT_STORE_*` variables at import because the root `conftest.py` replaces them with fakes for
every test.

### Local reproduction of the job

The job's `run` steps were extracted from `ci.yml` and executed unchanged
(`/private/tmp/.../scratchpad/runjob.py`), with `DOCKER_CONTEXT=desktop-linux`,
`COMPOSE_PROJECT_NAME=medhub-ci179` and `OBJECT_STORE_CI_PORT=18333` (the host's port 8333 is
avoided). Docker Compose v2.20.2-desktop.1 on an arm64 host.

| Step | Result |
|---|---|
| Generate throwaway credentials | rc 0 |
| Start the object store (`up -d --build --wait object-store-preflight object-store object-store-init`) | rc 0; preflight Exited, store Healthy, initialiser Healthy |
| Install dependencies (`uv sync --frozen`) | rc 0 |
| Check encryption (`OBJECT_STORE_INTEGRATION=1 ... uv run pytest -m object_store -v`) | 3 passed, 578 deselected |
| Stop the object store (`down -v`) | rc 0; project containers, volumes and networks gone |

Failure shown (scratch run, source restored afterwards, `git diff backend/app` empty):

- `ServerSideEncryption="AES256"` removed from `put_object`, bucket default still set: 3 passed.
  The bucket default alone encrypts a write, so this mutation is caught only by the bucket-default
  and plain-upload tests when the default is also unset (next line).
- Same, and the bucket default deleted (`delete_bucket_encryption`): 3 failed
  (`KeyError: 'ServerSideEncryption'` x2, `ServerSideEncryptionConfigurationNotFoundError`).

### Workflow validity

`actionlint` is not installed; I did not install it. The workflow parses as YAML; a structural check
confirms the job has `runs-on` and every step has exactly one of `uses` or `run`. The pin check
(`python3 infra/check_image_pins.py` and, for the new untracked file, `... infra/compose.ci-object-store.yml
.github/workflows/ci.yml`) exits 0. The override has no image. Compose v2.20.2 accepts `--wait` with
the two one-shot services; the hosted runner's Compose version may differ, which only the hosted run
shows.

### Other commands

| Command | Result |
|---|---|
| `cd backend && uv run pytest --cov=app --cov-fail-under=85` (CI command, `DOCKER_HOST` set to Docker Desktop) | 578 passed, 3 skipped (the integration tests), coverage 91.31% |
| `uv run ruff check .`, `uv run black --check .`, `uv run mypy app` | clean (232 files; 126 source files) |
| `python3 -m unittest discover -s infra/tests` | 32 tests OK |
| `python3 infra/check_image_pins.py` | exit 0 |
| `bash infra/smoke-test.sh` on a started stack (own project `medhub-sm179`, temp `.env`) | 26 passed, 1 failed (see PRB candidates) |

### Carry-overs from TASK-177 QA

1. **[MEDIUM] fixed.** Section 10 of `infra/smoke-test.sh` skips only when
   `[ -z "$(compose ps -q)" ]`. When the stack is up but `object-store` or `backend` is not running it
   reports `[FAIL] object-store and backend are running ...`. Shown: store stopped, stack otherwise up:
   exit 1 with that FAIL. All containers stopped: `[SKIP] stack not running`.
2. **[LOW] fixed.** Positive controls are cross-container and by service name:
   `frontend:nc:backend:8000`, `postgres:bash:redis:6379`, `redis:bash:postgres:5432` (the
   `reverse-proxy` and `celery-worker` controls already were). All five controls pass on the started
   stack and each probe then reports the store as unreachable. I did not add a printed line for a
   passing control (optional).

### PRB candidates (not fixed here)

- `infra/smoke-test.sh` section 8 still requires a named volume `minio_data` in `docker-compose.yml`;
  TASK-178 removed it, so the smoke test now ends with one FAIL on a healthy stack.
- `infra/.env.example` has `CORS_ORIGINS=` empty, which makes `Settings()` fail
  (`error parsing value for field "cors_origins"`) and the backend restart in a loop when `.env` is
  copied from the example unchanged. `[]` works.

### Open for the hosted run (TASK-182)

`object-store-integration` green on the pushed branch head, including the amd64 pull and start of the
store by digest (AC-9 CI part) and Compose `--wait` behaviour on the runner's Compose version.

## QA review, round 1 (QA engineer, 2026-10-30): CHANGES REQUESTED

TASK-179 and TS-008 go back from `in_review` to `draft`. QA reran every check itself. The job's
`run` steps were extracted from `ci.yml` and run unchanged in project `qa179` with
`OBJECT_STORE_CI_PORT=18333`. The dev `infra/.env` was backed up first and restored byte-identical
(`cmp`, SHA-256 `a4933b8c…96da`). Results: 3 passed. Backend CI command: 578 passed, 3 skipped,
91.31 %. ruff, black and mypy are clean. Infra tests: 32 OK. Pin check exits 0, also with the two
new files given explicitly. `traceability-check`: 0 errors.

The smoke test was run on a started stack (`qa179sm`, temporary `.env`). Healthy stack: 26 passed,
1 failed (§8 `minio_data`). Store stopped: §10 FAILs ("stack is up but object-store or backend is
not running"). Redis stopped: the three cross-container controls FAIL. All containers stopped:
`[SKIP] stack not running`. The carry-overs from TASK-177 are fixed.

### Findings

- **[HIGH] The smoke test fails on a healthy stack.** At `infra/smoke-test.sh:125`, section 8
  still requires the named volume `minio_data`. TASK-178 (`db0b480`) removed that declaration from
  `infra/docker-compose.yml`, so every run on the branch ends with `26 passed, 1 failed`, and
  CR-002 AC-16 ("every check passing") cannot be met. This task already edits the script, and it
  accepted the FAIL in its own verification. **Fix:** remove `minio_data` from the loop at :125,
  then rerun the smoke test on a started stack and expect 27 passed, 0 failed. Record the
  regression as found during TASK-179 verification. The overlay requires a PRB for a defect from
  another task: raise a minor PRB, resolved by CR-002 through TASK-179, and the orchestrator adds
  the `resolves` link on CR-002.
- **[MEDIUM] TC-008.8 cannot tell whether `put_object` requests encryption.** In
  `backend/tests/integration/test_object_store_sse.py:61-67`, the bucket has default encryption,
  so test 1 passes even when `ServerSideEncryption` is removed from `put_object` (the developer's
  own mutation). PRB-036's root cause is that "what the store does with the parameter was never
  observed", and that is still not observed. QA showed the check is feasible on the real store
  (scratch probe, project `qa179`). The probe created a bucket with no default encryption
  (`get_bucket_encryption` returned `ServerSideEncryptionConfigurationNotFoundError`). The real
  `ObjectStorageClient.put_object` gave `head_object` `ServerSideEncryption = AES256`. With the
  argument stripped, it gave `None`. **Fix:** add a fourth test. It creates a uniquely named
  bucket with the raw client, monkeypatches `OBJECT_STORE_BUCKET` to that bucket (then
  `get_settings.cache_clear()`), and asserts `get_bucket_encryption` raises
  `ServerSideEncryptionConfigurationNotFoundError`. It then writes through
  `ObjectStorageClient.put_object` and asserts `head_object` reports `AES256`, and deletes the
  object and the bucket in teardown. Update TC-008.8 (expected result and the single-mutation
  failure) and PRB-036 `## Resolution` to match.
- **[MEDIUM] Running the job's steps locally targets the developer's Compose project and volumes.**
  `.github/workflows/ci.yml:234` sets `COMPOSE` without a project name, so the project is `infra`
  (from the directory of the first file). The "Generate" step overwrites `infra/.env`, and the
  `always()` step runs `down -v`, which on a developer machine deletes `infra_postgres_data`,
  `infra_redis_data` and `infra_object_store_data`. On a hosted runner this is safe, because the
  checkout has no `infra/.env` (`.gitignore:53`) and the runner is disposable. The warning exists
  only in this task's "Notes". **Fix:** add `-p medhub-ci` to `COMPOSE` at :234. Put a comment on
  the Generate step saying it overwrites `infra/.env` and is for CI only. Add the same warning,
  with "back up `infra/.env`, set `COMPOSE_PROJECT_NAME`", to TC-008.8 and to the module docstring
  ("or by hand, see TASK-179").
- **[LOW] The TC-008.8 command cannot be reproduced as written.** TS-008 TC-008.8 and this task's
  "Verification" run `OBJECT_STORE_INTEGRATION=1 OBJECT_STORE_ENDPOINT=… uv run pytest -m
  object_store` without exporting the `OBJECT_STORE_*` credentials. In that case the module keeps
  none, and the conftest's fake keys are used. **Fix:** prefix the command with
  `set -a; . ../infra/.env; set +a;`, as the job does, and use the port variable
  (`${OBJECT_STORE_CI_PORT:-8333}`).
- **[LOW] The override test depends on the shell.** At
  `infra/tests/test_compose_object_store.py:174-178`, `docker compose config` inherits
  `OBJECT_STORE_CI_PORT`. With `OBJECT_STORE_CI_PORT=18333` exported (the documented local
  reproduction), the test fails (`OBJECT_STORE_CI_PORT=18333 python3 -m unittest
  infra.tests.test_compose_object_store` gives 1 failure). **Fix:** pass
  `env={k: v for k, v in os.environ.items() if k != "OBJECT_STORE_CI_PORT"}` to `subprocess.run`.
- **[LOW] PRB-036's safety evaluation is out of date.** At
  `docs/problem-reports/PRB-036-no-end-to-end-sse-verification.md:40`, it still argues from MinIO
  ("makes MinIO reject the write"). **Fix:** restate it for SeaweedFS and for the bucket default
  (TASK-175/176), which now catches a missing request parameter. The `minor` rating stays.

### Not blocking (recorded)

- `CORS_ORIGINS=` is empty in `infra/.env.example:82`. With it, `Settings()` raises
  `SettingsError: error parsing value for field "cors_origins"`, and the backend restart-loops.
  This is pre-existing: the line and `cors_origins: list[str] = []` both come from `7cd2b6a`
  (TASK-003, 2026-06-20), and the comment's "comma-separated" form is wrong too (a list field
  needs JSON, e.g. `[]`). It is outside CR-002's scope, so raise a new PRB, `minor`: the failure is
  loud at start-up and affects only availability on a fresh setup from the example, with no data
  or clinical impact. TASK-182 (AC-16 fresh-host run) must set `CORS_ORIGINS=[]` in its temporary
  `.env` and say so.
- `ci.yml` has no `permissions:` block (pre-existing, every job). The new job needs only
  `contents: read`. A top-level `permissions: contents: read` belongs to a separate change.
- Compose `--wait` with the one-shot preflight and initialiser works on v2.20.2 here. The runner's
  Compose version is checked only by the hosted run (TASK-182).

## Round 2 (software developer, 2026-10-30): QA findings fixed

Hosted-runner run still PENDING (TASK-182). TASK-179 and TS-008 (1.5) go back to `in_review`.
This section supersedes the counts above where they differ (3 tests became 4; the smoke test now
passes in full).

1. **[HIGH] fixed.** `minio_data` removed from the section 8 loop of `infra/smoke-test.sh`. PRB-055
   is `resolved` (1.1) with a reproducible Resolution. Smoke test on a started stack (project
   `medhub-sm179b`, temporary `.env` with `CORS_ORIGINS=[]`, PRB-056): `26 passed, 0 failed`
   (27 checks before, minus the removed one). Stopped-store FAIL and all-stopped SKIP behaviour is
   unchanged from round 1.
2. **[MEDIUM] fixed.** Fourth test `test_put_object_requests_encryption_on_a_bucket_without_a_default`:
   unique bucket, `get_bucket_encryption` raises `ServerSideEncryptionConfigurationNotFoundError`,
   `OBJECT_STORE_BUCKET` monkeypatched and the settings cache cleared, write through
   `ObjectStorageClient.put_object`, `head_object` reports `AES256`, object and bucket deleted.
   Local job run: 4 passed. Mutation (`ServerSideEncryption` removed from `put_object`, bucket
   default intact): the new test fails (`KeyError: 'ServerSideEncryption'`), the other three pass;
   `git diff backend/app` empty afterwards. TC-008.8 and PRB-036 Resolution updated.
3. **[MEDIUM] fixed.** `COMPOSE` is `docker compose -p medhub-ci ...`; a CI-ONLY comment on the
   Generate step; the warning repeated in TC-008.8, the test module docstring and the Verification
   block above. Local run of the job's steps under `medhub-ci`: the dev `infra/.env` was backed up
   and restored (`shasum` identical, `a4933b8c...96da`); the list of Docker volumes before and
   after is identical (the dev `infra_minio_data`, `infra_postgres_data` and `infra_redis_data`
   present and untouched; no `infra_object_store_data` existed); no `medhub-ci` container remains.
4. **[LOW] fixed.** TC-008.8 and Verification export the credentials
   (`set -a; . ../infra/.env; set +a;`) and use `${OBJECT_STORE_CI_PORT:-8333}`.
5. **[LOW] fixed.** The override test passes an environment without `OBJECT_STORE_CI_PORT`. Infra
   tests: 32 OK both plain and with `OBJECT_STORE_CI_PORT=18333` exported.
6. **[LOW] fixed.** PRB-036 safety evaluation restated for SeaweedFS and the bucket default
   (TASK-175/176); `minor` stays; version 1.3.

Other commands: backend CI command 578 passed, 4 skipped, coverage 91.31%; ruff, black (232
files unchanged) and mypy (126 source files) clean; pin check exit 0.

## QA review, round 2 (QA engineer, 2026-10-30): APPROVED

TASK-179 and TS-008 1.5 move from `in_review` to `approved`. QA ticked AC-7, AC-15, AC-19
(PRB-036) and the traceability item of the Definition of Done. **Left open**, by design: AC-4/AC-9
CI part (store pulled and started on a fresh amd64 runner) and "new CI job green on the branch
head". Both need the hosted run, which TASK-182 checks.

Reruns by QA:

- **Job steps.** They were extracted from `ci.yml` and run unchanged under `-p medhub-ci`, with
  `OBJECT_STORE_CI_PORT=18333`, and gave **4 passed**. The dev `infra/.env` was backed up and
  restored (`cmp` identical). The Docker volume list is identical before and after. The
  `infra_*` volumes keep their 2026-06-20 creation dates. No `medhub-ci` container or volume is
  left.
- **Mutation.** A pytest plugin replaced `put_object` with a copy without `ServerSideEncryption`,
  with no source edit (`git diff backend/app` is empty). Result: **1 failed, 3 passed**. Only
  `test_put_object_requests_encryption_on_a_bucket_without_a_default` failed
  (`KeyError: 'ServerSideEncryption'`). Its `finally` removed the scratch bucket: afterwards only
  `medhub-ci` exists, and it holds 0 objects.
- **Smoke test.** On a started stack (project `qa179sm2`, temporary `.env`) it gave
  **26 passed, 0 failed**. The stack was then removed with `down -v`, and the dev `.env` and
  volumes are unchanged.
- **Infra tests.** 32 OK, both plain and with `OBJECT_STORE_CI_PORT=18333` exported.
- **Backend CI command.** 578 passed, 4 skipped, 91.31 %. ruff, black and mypy are clean. The pin
  check exits 0, also with the two new files given explicitly.
- **`traceability-check`.** Whole project, 376 records: **0 errors**. In scope (TASK-179, TS-008,
  PRB-036, PRB-055), the only warning is W5, TASK-179 (approved) → RISK-012 (`in_review`). That is
  expected until TASK-181. The old W5 TP-001 → TS-008 is gone. E9 for PRB-055 passes only with the
  working-copy `resolves` link on CR-002.

Every round 1 finding is closed. Observations, not blocking:

- **E9 at the commit.** Commit CR-002's `resolves` → PRB-055 in the same commit as PRB-055
  `resolved`, or earlier. Otherwise that commit fails E9.
- **PRB-055 Resolution wording.** "Fixed in the CR-002 TASK-179 commit" is accepted, provided the
  real commit is cited. Proposed wording: "Fixed in commit `<sha>` (`<subject>`, TASK-179);
  verify with `git show <sha> -- infra/smoke-test.sh`. The regression came with db0b480 (TASK-178)."
- **Stale candidate list.** "PRB candidates (not fixed here)" above predates round 2. The items
  are now PRB-055 (resolved) and PRB-056 (open, minor, outside CR-002).
