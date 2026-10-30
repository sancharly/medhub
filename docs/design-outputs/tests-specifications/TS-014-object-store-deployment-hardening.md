---
id: "TS-014"
type: test-specification
title: "Object-store deployment hardening verification"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-040"
    relation: verifies
tags: ["level:unit", "level:integration", "class:B", "cr:CR-002"]
---

# TS-014 — Object-store deployment hardening verification

## Scope

Software requirement covered: SR-040 (this version: AC 2, credential refusal, and AC 4, bucket
initialisation; TASK-176 and TASK-177 extend the specification for the remaining acceptance
criteria). Software items under test: SI-OBJSTORE units `U-OBJ-Preflight`
(`backend/app/core/object_store_credentials.py`) and `U-OBJ-Init`
(`backend/app/core/object_store_init.py`) (ADD-025), and their Compose wiring. Levels: unit
(TC-014.2, TC-014.4), integration (TC-014.1, TC-014.2 and TC-014.4 started stack), static check
(TC-014.3).

## Preconditions and environment

Branch `bug/minio-object-store`. Backend Python 3.12 with the dependencies locked in
`backend/uv.lock`. TC-014.1 and TC-014.3 need Python 3 (standard library) and, for the Compose
parts, Docker Compose v2 (`docker compose config` needs no daemon). The started-stack part of
TC-014.2 needs a Docker daemon and the pinned images of `infra/docker-compose.yml`; it is run by
editing `infra/.env` with throwaway test values only.

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-014.1 | SR-040 (AC 2) | `infra/tests/test_compose_object_store.py` (`python3 -m unittest discover -s infra/tests -v`): `ComposeWiring` | `object-store-preflight` has `network_mode: none`, `restart: "no"`, the module as entrypoint and no `env_file`; its `OBJECT_STORE_*` values use the same `${...:?}` expressions as `minio` and, with a key overridden in the shell environment, resolve to the same values as `minio`'s `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`; `minio` and `object-store-init` depend on it with `service_completed_successfully`; Compose itself refuses an unset or empty key (`:?` guard); `object-store-init` takes its keys through `environment:` with the same expressions (no `env_file`), runs once from the backend image with the module as entrypoint, and depends on `minio` with `service_healthy` (which has a healthcheck); `backend` depends on `object-store-init` with `service_completed_successfully`; no `createbuckets` service and no `minio/mc` image remain | All tests of `ComposeWiring` pass (skipped with a message when `docker` is absent) |
| TC-014.2 | SR-040 (AC 2) | Unit: `backend/tests/core/test_object_store_credentials.py` (`cd backend && uv run pytest tests/core/test_object_store_credentials.py -v`). Started stack: manual, steps in TASK-174 Verification | Each of the four cases, for each key (unset, empty, known default, secret shorter than 16 characters), is rejected with a message naming `OBJECT_STORE_ACCESS_KEY` or `OBJECT_STORE_SECRET_KEY` and never the value; `python -m app.core.object_store_credentials` exits 1 (0 and silent for good keys); in the started stack the preflight exits 1 and `minio` and `object-store-init` stay `Created`, not started; with good keys the preflight exits 0 and both start | Unit: all tests pass. Started stack: exit codes and container states as stated, recorded in TASK-174 "Verification results" (including a shell override with default keys, which the preflight rejects). Unset and empty keys are refused earlier by the Compose `:?` guard (TC-014.1); the preflight is run directly for those two cases |
| TC-014.3 | SR-040 (AC 2) | `infra/tests/test_compose_object_store.py`: `NoDefaultStrings`; `backend/tests/test_env_example.py` (`test_env_example_object_store_keys_are_empty`, `test_env_example_has_no_object_store_default_strings`); `git grep -n -i minioadmin -- ':!docs'` | The template holds empty object-store keys; the template, the Compose file, DEPLOY.md and the CI workflow hold no default credential string; test fixtures use non-default synthetic values | Tests pass; the `git grep` matches only the rule module and its tests, which name the default set |
| TC-014.4 | SR-040 (AC 4) | Unit: `backend/tests/core/test_object_store_init.py` (`cd backend && uv run pytest tests/core/test_object_store_init.py -v`). Started stack: manual, steps in TASK-175 Verification | The initialiser creates a missing bucket, sets and reads back `AES256` default encryption and expects `NoSuchBucketPolicy`; a second run changes nothing. It exits 1 with one line naming the failed step for an unreachable store, a failing create or encryption call, an unexpected read-back and a bucket policy present, and prints no key value. In the started stack, on a fresh volume `docker compose up -d` starts the initialiser after `minio` is healthy and creates the bucket; with a store it cannot reach, the initialiser exits 1 and `backend` stays `Created`, not started | Unit: all tests pass. Started stack: states and exit codes as stated, recorded in TASK-175 "Verification results" |

## Acceptance criteria (class B unit level)

Unit acceptance (§5.5.3): the rule returns one rejection per problem, each naming its setting;
it accepts a short non-default access key; whitespace is stripped before the empty and default checks; the known-default comparison ignores case; the secret
boundary is 15 (rejected) and 16 (accepted) characters; no key value reaches stdout or stderr.
