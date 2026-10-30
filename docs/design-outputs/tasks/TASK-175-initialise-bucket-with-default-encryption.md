---
id: "TASK-175"
type: task
title: "Initialise the bucket from the backend image with default encryption, and retire mc"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-040"
    relation: implements
  - target: "SR-022"
    relation: implements
  - target: "RISK-012"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-002"
    relation: relates_to
  - target: "PRB-039"
    relation: relates_to
  - target: "SOUP-023"
    relation: relates_to
  - target: "SOUP-019"
    relation: relates_to
  - target: "TASK-174"
    relation: relates_to
tags: ["configuration", "encryption", "soup", "cr:CR-002", "issue:sancharly/medhub#33", "control:protective"]
---

# TASK-175 — Initialise the bucket from the backend image with default encryption, and retire mc

- **Software item / unit:** SI-OBJSTORE `U-OBJ-Init` (ADD-025)
- **Depends on:** TASK-174 (the preflight dependency and the same Compose block, `relates_to`).
  It is independent of the Q-1 answer (ADR-0015 D2).
- **Branch:** `bug/minio-object-store`
- **Size:** M (1 new module and its tests, Compose, SOUP-023, ADD-012, TS-014, TS-008, PRB-039)
- **Needs:** a Docker host. The started-stack checks run against the current MinIO, which only
  the reference workstation holds in its image cache. TASK-176 repeats them on the new server.

## Objective

Resolve PRB-039 and implement SR-040 AC 4 and SR-022 AC 4.

- The bucket initialiser starts only after the store is healthy and fails loudly on any error.
- It sets SSE-S3 as the bucket's default encryption, so any write is encrypted at rest,
  whichever path made it.
- It runs from the backend image with boto3 (SOUP-019), so the `mc` client (SOUP-023) leaves
  the deployment.

## Interfaces to honor

- Entry point: `python -m app.core.object_store_init`. It reads `OBJECT_STORE_ENDPOINT`,
  `OBJECT_STORE_ACCESS_KEY`, `OBJECT_STORE_SECRET_KEY` and `OBJECT_STORE_BUCKET` the way
  `ObjectStorageClient` does, from the same settings.
- Exit 0 only when all of these hold:
  - the bucket exists or was created;
  - `get_bucket_encryption` returns an `AES256` rule;
  - `get_bucket_policy` returns `NoSuchBucketPolicy`.

  Otherwise exit 1 with one line naming the failed step. Never `exit 0` over a failure.
- Idempotent: a second run on an initialised bucket exits 0 and changes nothing.

## Implementation detail

1. Write the module:
   - `head_bucket`, then `create_bucket` on 404;
   - `put_bucket_encryption` (`SSEAlgorithm: AES256`);
   - `get_bucket_encryption`, and check it;
   - `get_bucket_policy`, and expect `NoSuchBucketPolicy`.

   Map `botocore` `ClientError`, `EndpointConnectionError` and `NoCredentialsError` to exit 1.
2. **Compose**:
   - `minio` gets a healthcheck that succeeds only once S3 accepts requests. It must use a tool
     present in the image, so check that first. MinIO serves `/minio/health/live` and `/ready`.
   - Replace `createbuckets` by `object-store-init`:
     - built from `../backend`, with the four `OBJECT_STORE_*` values through `environment:`
       (the same `${...:?}` expressions as `minio` and the preflight; no `env_file`, per QA's
       TASK-174 review);
     - `command: python -m app.core.object_store_init`, `restart: "no"`;
     - `depends_on`: `minio: service_healthy` and `object-store-preflight:
       service_completed_successfully`.
   - `backend` depends on `object-store-init: service_completed_successfully`, so a failed
     initialisation keeps the backend down (SR-040 AC 4).
   - The `minio/mc` image reference leaves the file.
3. **SOUP-023 → `obsolete`**:
   - bump the version and clear the approval record;
   - change-log entry "retired by CR-002 TASK-175 (ADR-0015 D2), replaced by the boto3
     initialiser".
4. **ADD-012**:
   - bump to 1.1 and clear the approval record, as the first CR-002 task that changes it;
   - remove `relates_to` SOUP-023.

   TASK-176 removes SOUP-022 under the same version. ADD-025 needs no SOUP-023 link.
5. **TS-014** TC-014.4: the initialiser exits non-zero for an unreachable store, a failing
   encryption call and a policy present, and the backend does not start.
6. **TS-008** TC-008.6: bucket default encryption is `AES256`, and a plain upload with no SSE
   request is reported `AES256` (SR-022 AC 4).
7. **PRB-039** → `resolved`, with a `## Resolution` that names the files, the ordering and the
   failing exit.

## Tests (write first)

Unit tests with `botocore.stub.Stubber` for:

- fresh bucket;
- existing bucket;
- `put_bucket_encryption` error;
- unexpected encryption read-back;
- policy present;
- endpoint unreachable;
- the second run is idempotent.

## Acceptance criteria

- [x] CR-002 **AC-6** / SR-040 AC 4: the initialiser starts after the healthcheck passes. It exits
      non-zero against an unreachable store and on a failing command. On a fresh volume,
      `docker compose up -d` creates the bucket with no manual step.
- [x] CR-002 **AC-4** / SR-022 AC 4 (on the current store): after the initialiser on a fresh
      volume, the bucket's default encryption is SSE-S3, and a plain upload is reported `AES256`.
- [x] CR-002 **AC-12** (SOUP-023 part): SOUP-023 is `obsolete`, and ADD-012 no longer links it.
- [x] CR-002 **AC-19** (PRB-039 part): PRB-039 is `resolved` with its `## Resolution`.

## Verification

```sh
cd backend && uv run pytest tests/core/test_object_store_init.py -v
python3 -m unittest discover -s infra/tests -v && python3 infra/check_image_pins.py
docker compose -f infra/docker-compose.yml down && docker volume rm <scratch copy only>   # never the real minio_data
docker compose -f infra/docker-compose.yml up -d && docker compose -f infra/docker-compose.yml ps -a
# negative: stop minio, run object-store-init once -> exit 1; backend stays down
bash infra/smoke-test.sh
```

Run the fresh-volume check with a Compose project name of its own (`-p cr002-init`), so the real
`minio_data` volume is never removed.

## Definition of Done

- [x] Lint, type-check and the backend suite pass (coverage ≥ 85 %). The pin check and the
      infrastructure tests pass. Smoke passes.
- [x] `traceability-check` shows no error for the touched records.

## Verification results (software developer, 2026-10-30)

Implementation notes and deviations:

- `app.core.object_store_init` reads the four `OBJECT_STORE_*` variables from the environment
  directly rather than `get_settings()`: `Settings` also requires database, SMTP and session
  settings that the initialiser container, which receives only the four object-store values, must
  not hold. The names are the same ones `ObjectStorageClient` reads. It pins `region_name` to
  `us-east-1` and sets short connect/read timeouts so an unreachable store fails in seconds.
- Compose: `minio` healthcheck uses `curl` (present in the pinned image) on `/minio/health/ready`.
  The `backend` `depends_on` list became a map (postgres and redis `service_started`, as before) to
  add `object-store-init: service_completed_successfully`.
- The new f-string lines avoid the words `from`/`join`/`select`...: `tests/db/test_no_raw_sql.py`
  flags any f-string line containing them (hence the `_failed` helper).

Commands and results:

- `cd backend && uv run pytest tests/core/test_object_store_init.py -v`: 13 passed.
- `cd backend && uv run pytest --cov=app --cov-fail-under=85`: 552 passed, 91.30 %.
  `ruff check .`, `black --check app tests` and `mypy app` (126 files) are clean.
- `python3 -m unittest discover -s infra/tests -v`: 22 OK. `python3 infra/check_image_pins.py`: exit 0.
- Started stack, `DOCKER_CONTEXT=desktop-linux`, Compose project `cr002-init`, fresh volumes,
  temporary `infra/.env` (generated keys; the dev file's keys are rejected by the TASK-174 preflight):
  - `docker compose up -d --build`: preflight Exited (0), `minio` Healthy, then `object-store-init`
    Exited (0) with "object-store init ok: bucket medhub private, AES256", then `backend` started.
    No manual step.
  - From inside `backend`, boto3: `get_bucket_encryption` returned
    `[{'ApplyServerSideEncryptionByDefault': {'SSEAlgorithm': 'AES256'}}]`; a plain `put_object`
    with no SSE argument then `head_object` gave `ServerSideEncryption: AES256`; `get_bucket_policy`
    gave `NoSuchBucketPolicy`.
  - Re-run of `object-store-init` on the initialised bucket: exit 0 (idempotent).
  - `-e OBJECT_STORE_ENDPOINT=http://127.0.0.1:1`: exit 1, "object store unreachable". Wrong secret:
    exit 1, "head_bucket failed: 403".
  - Project `cr002-neg`, `up -d backend` with `OBJECT_STORE_ENDPOINT=http://127.0.0.1:1`:
    `object-store-init` Exited (1), `backend` `Created` (not started).
  - `bash infra/smoke-test.sh` against the running stack: 17 passed, 0 failed.
- The containers and networks of both projects were removed with `docker compose down`; their
  volumes (`cr002-init_*`, `cr002-neg_*`) were left in place. The dev `infra/.env` was restored
  byte-identical (`cmp`, sha1 714c7630...). The real `infra_minio_data` was never touched.
- Not run: `traceability-check` (left for QA).

Handoff: TASK `draft` to `in_review`; SOUP-023 `obsolete`; PRB-039 `resolved`; ADD-012, TS-008 and
TS-014 `in_review` with their approval records cleared.

## QA review (2026-10-30): APPROVED

TASK `in_review → approved`; TS-008 1.2 and TS-014 1.2 `in_review → approved`. ADD-012 1.1 stays
`in_review` for the human. No CRITICAL or HIGH finding. The MEDIUM items below are small record and
wiring fixes. They can be taken before the TASK-175 commit or carried into TASK-176/TASK-177.

Ruling on the `get_settings()` deviation: accepted. `Settings` requires `database_url`, `redis_url`,
`session_signing_key`, the SMTP settings and `at_rest_encryption_key` with no defaults
(`backend/app/core/config.py:19-41`). Reading the four variables directly keeps those secrets out of
the initialiser container. The names are the ones `ObjectStorageClient` reads through `Settings`
(`backend/app/core/object_storage.py:24-31`). The Interfaces text ("from the same settings") is met
in substance. The deviation is recorded in the module docstring and in "Verification results".

### Findings

- **[MEDIUM] Shell override makes the initialiser and the backend use different buckets** —
  `infra/docker-compose.yml:153,156` (init) vs `:39` (backend `env_file: .env`). The init receives
  `OBJECT_STORE_ENDPOINT` and `OBJECT_STORE_BUCKET` by interpolation, so the shell wins. The backend
  receives them from `env_file`, where the shell has no effect. QA probe:
  `OBJECT_STORE_BUCKET=decoy docker compose ... config` gives init `decoy` and backend `medhub`. On a
  started store, with `medhub`'s default encryption deleted (the state of a pre-CR-002 volume made by
  `mc`), `OBJECT_STORE_BUCKET=decoy` init exited 0 ("bucket decoy private, AES256"). `medhub` stayed
  `ServerSideEncryptionConfigurationNotFoundError`, and the backend would have started. The
  application's own writes still request `AES256` (`object_storage.py:40`), so this affects the
  defence-in-depth path SR-022 AC 4 adds, not app-path writes. On a fresh volume the mismatch fails
  loudly at the first upload. This is the TASK-174 env-split pattern again. → Give `backend` (and any
  other service that uses the store) an `environment:` block with `OBJECT_STORE_ENDPOINT` and
  `OBJECT_STORE_BUCKET`, using the init's exact expressions. `environment:` overrides `env_file`.
  Extend `test_initialiser_runs_once_from_the_backend_image_with_the_store_keys` with a shell
  override of the bucket and endpoint, asserting that init and backend resolve them identically.
- **[MEDIUM] PRB-039 `## Resolution` is pinned to the working tree and gives no commands** —
  `docs/problem-reports/PRB-039-createbuckets-starts-before-minio-ready.md` (Resolution, first line
  and "Verification" bullet). "On the working tree of `bug/minio-object-store`" is no longer true
  after the commit, and the verification lists results but no commands. problem-report-resolution
  requires the verification to be stated reproducibly. → Say "resolved by the TASK-175 commit on
  `bug/minio-object-store`". Add the commands and their results in one place:
  `cd backend && uv run pytest tests/core/test_object_store_init.py -v` (13 passed),
  `python3 -m unittest discover -s infra/tests -v` (22 OK), and the started-stack steps (TASK-175
  Verification, TS-014 TC-014.4).
- **[MEDIUM] PRB-039 `## Safety evaluation` has no released-version or notification statement** —
  same file, `## Safety evaluation`. §9.3 and the PRB body contract ask whether a released version
  in use is affected and whether notification is needed. This is a recurring gap. → Add one
  sentence: no released version (PLAN-001 has no REL record), so no notification is needed. Name
  RISK-007 as the related risk and keep `minor`.
- **[LOW] Not every botocore transport error becomes the one-line message** —
  `backend/app/core/object_store_init.py:91-94`. `ConnectionClosedError` (and, by class,
  `ReadTimeoutError`) is not an `EndpointConnectionError`. QA run with
  `OBJECT_STORE_ENDPOINT=http://redis:6379`: exit 1, but with a traceback instead of "object-store
  init failed: ...". It still fails closed and prints no key. → Catch
  `botocore.exceptions.BotoCoreError` after the two specific handlers and print
  `object store error: <ExceptionClass>`. Add a stub-free unit test like
  `test_endpoint_unreachable_fails` that raises `ConnectionClosedError`.
- **[LOW] TS-014 preconditions and unit acceptance criteria do not yet cover TC-014.4** —
  `docs/design-outputs/tests-specifications/TS-014-object-store-deployment-hardening.md`
  "Preconditions and environment" (names only TC-014.2's started stack) and "Acceptance criteria"
  (lists only the credential rule). → Add the TC-014.4 environment: a Compose project of its own
  (`-p`), fresh volumes, a temporary `infra/.env` with generated keys (and `POSTGRES_PASSWORD`,
  PRB-038). Add U-OBJ-Init unit criteria: one line naming the failed step, no key value printed,
  idempotent re-run, exit 0 only when all three checks hold. Do it at the next TS-014 revision
  (TASK-176).

### Ruling on the developer's PRB candidate (`test_no_raw_sql`)

Confirmed. Raise a PRB with criticality **minor**. `backend/tests/db/test_no_raw_sql.py:16-34` flags
any f-string whose first source line contains `select|insert|update|delete|where|from|join`,
case-insensitive. QA probe of the same logic (scratchpad `qa175/rawsql_probe.py`):

- false positive on `f"failed to update {name}"`;
- false negative on a multi-line f-string whose SQL starts on a later line (only `node.lineno` is
  read);
- false negative on `"SELECT ... {}".format(x)` outside `text(...)` (`:50-56` only looks inside
  `text()`).

Minor because SR-031 also has real-database evidence (`tests/db/test_repositories.py`, TC-008.3) and
no product code is affected. Still, the static guard both blocks harmless wording (developers
reword messages to get past it, as here) and misses real SQL interpolation. Suggested fix:
check `ast.JoinedStr` / `.format` / `%` nodes passed to `text()`, `execute()` or `exec_driver_sql()`,
instead of keyword-grepping lines.

### Pre-existing (not blocking)

- PRB-038: `POSTGRES_PASSWORD` is not in `infra/.env.example` or the dev `infra/.env`, and the
  Compose file has no `:?` guard (`infra/docker-compose.yml:76`). On a fresh volume `postgres` loops
  `Restarting (1)` until it is set. QA added it to the temporary `.env`.
- `infra/DEPLOY.md:79-89` still tells the operator to create the bucket by hand with `mc`.
  This is TASK-180's scope (AC-20, Q-6).
- RISK-010, RISK-012 and CR-002 keep `relates_to` SOUP-023 (W6). CR-002 is a retiring record under
  AC-12. TASK-181 moves the RISK links (its step "replace `relates_to` SOUP-022 and SOUP-023 with
  SOUP-036").

### Verification run (QA, 2026-10-30, `DOCKER_CONTEXT=desktop-linux`)

- `cd backend && uv lock --check && uv run ruff check . && uv run black --check . && uv run mypy app`:
  clean (227 files unchanged, 126 source files no issues).
- `cd backend && uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85`: 552 passed,
  91.30 %. `uv run pytest tests/core/test_object_store_init.py -v`: 13 passed.
- `python3 -m unittest discover -s infra/tests -v`: 22 OK. `python3 infra/check_image_pins.py`: exit 0.
- Started stack, project `qa175`, fresh volumes, temporary `infra/.env` (generated
  `OBJECT_STORE_*` keys, plus `POSTGRES_PASSWORD` per PRB-038):
  - `up -d --build`: preflight Exited (0), `minio` healthy, `object-store-init` Exited (0) ("bucket
    medhub private, AES256"), backend healthy.
  - From `backend`, boto3: `get_bucket_encryption` gave `[{'ApplyServerSideEncryptionByDefault':
    {'SSEAlgorithm': 'AES256'}}]`; a plain `put_object` then `head_object` gave
    `ServerSideEncryption: AES256`; `get_bucket_policy` gave `NoSuchBucketPolicy`. Test object deleted
    (`head_object` 404, `KeyCount` 0).
  - `run --rm --no-deps object-store-init`: exit 0 (idempotent). With an `s3:GetObject` `*` bucket
    policy set: exit 1, "bucket has a policy; it must stay private". After the policy was deleted:
    exit 0.
  - Wrong secret: exit 1, "head_bucket failed: 403", secret not in the output. `http://127.0.0.1:1`
    and `http://nosuchhost:9000`: exit 1, "object store unreachable". Bucket `Bad_Bucket`: exit 1,
    "head_bucket failed: 400". `http://redis:6379`: exit 1 with a traceback (LOW above).
  - `bash infra/smoke-test.sh`: 17 passed, 0 failed.
- Ordering, project `qa175o`, fresh volumes, `up -d object-store-init` under `docker events`:
  preflight start/die, `minio` start, `minio health_status: healthy`, then `object-store-init` start
  and die (exit 0). The init started only after the healthy event.
- Existing-volume repair (`qa175o`): with `medhub`'s default encryption deleted, a normal init run
  restored `AES256`.
- Negative stack, project `qa175neg`, `OBJECT_STORE_ENDPOINT=http://127.0.0.1:1 up -d backend`:
  `object-store-init` Exited (1) ("object store unreachable"), `backend` `created` (never started),
  and Compose reported "service object-store-init didn't complete successfully: exit 1".
- Clean-up: `down --remove-orphans` for `qa175`, `qa175o` and `qa175neg`; containers and networks are
  gone. Volumes `qa175*_{minio,postgres,redis}_data` and the `qa175-*` images were left in place.
  The dev `infra/.env` was restored byte-identical (`cmp` OK, sha1 `714c7630...`). The real
  `infra_minio_data` was not touched.
- traceability-check (fallback parsers; no MedTrace tooling in the repo). Scoped to SOUP-023,
  ADD-012, TS-008, TS-014, PRB-039 and TASK-175: 0 errors. 2 warnings, both expected:
  `soup_unintegrated` on obsolete SOUP-023 (a fallback artefact), and W6 TASK-175 → SOUP-023 (the
  retiring task).
  Whole project, 372 records: 0 errors, 24 warnings:
  - W5 17: CR-002 records held at `in_review` and the pre-existing TASK-132 → TASK-101. This approval
    clears TP-001 → TS-008 and adds TASK-175 → RISK-012, which is expected until TASK-181. The
    re-run after the status changes gives the same totals;
  - W6 5: TASK-165 → SOUP-033, and SOUP-023 from TASK-175, CR-002, RISK-010 and RISK-012;
  - `soup_unintegrated` and `soup_without_risk` on SOUP-036 (TASK-176 and TASK-181 scope);
  - W1 3, W2 5 (SR-040 has no TR until release), W7 1, all pre-existing apart from SR-040.

  PRB-039 has its incoming `resolves` link from CR-002 (E9 OK).
