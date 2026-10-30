---
id: "TS-014"
type: test-specification
title: "Object-store deployment hardening verification"
status: approved
version: "1.4"
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

Software requirement covered: SR-040 (this version: AC 1, no console or admin listener; AC 2,
credential refusal; AC 3, network restriction; AC 4, bucket initialisation; and AC 5 for AC 3;
the remaining criteria are added by later tasks). Software items under test: SI-OBJSTORE units `U-OBJ-Preflight`
(`backend/app/core/object_store_credentials.py`), `U-OBJ-Server` (the Compose service
`object-store`) and `U-OBJ-Init` (`backend/app/core/object_store_init.py`) (ADD-025), and their
Compose wiring and the network topology. Levels: unit (TC-014.2, TC-014.4), integration (TC-014.1, TC-014.2, TC-014.4 and
TC-014.5, TC-014.6 started stack), static check (TC-014.3, TC-014.5, TC-014.6).

## Preconditions and environment

Branch `bug/minio-object-store`. Backend Python 3.12 with the dependencies locked in
`backend/uv.lock`. TC-014.1 and TC-014.3 need Python 3 (standard library) and, for the Compose
parts, Docker Compose v2 (`docker compose config` needs no daemon). The started-stack part of
TC-014.2 needs a Docker daemon and the pinned images of `infra/docker-compose.yml`; it is run by
editing `infra/.env` with throwaway test values only.

Started-stack cases (TC-014.2, TC-014.4, TC-014.5, TC-014.6) use: a Compose project of their own
(`docker compose -p <name> …`, never the default `infra` project, whose volumes hold dev data);
fresh volumes (new project name); a temporary `infra/.env` with generated `OBJECT_STORE_*` keys
that pass the preflight, `AT_REST_ENCRYPTION_KEY` and `POSTGRES_PASSWORD` (PRB-038: the file has
no default for it), backed up beforehand and restored byte-identical afterwards; and
`DOCKER_CONTEXT` set to a live daemon. Only containers and networks of that project are removed;
no volume of the `infra` project is touched, `infra_minio_data` least of all (TASK-178 migrates
from it). The object-store image is `chrislusf/seaweedfs:4.51` by index digest (SOUP-036).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-014.1 | SR-040 (AC 1, AC 2, AC 4) | `infra/tests/test_compose_object_store.py` (`python3 -m unittest discover -s infra/tests -v`): `ComposeWiring` | `object-store-preflight` has `network_mode: none`, `restart: "no"`, the module as entrypoint and no `env_file`; its `OBJECT_STORE_*` values use the same `${...:?}` expressions as `object-store` and, with a key overridden in the shell environment, resolve to the same values as `object-store`'s `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`; `object-store` and `object-store-init` depend on it with `service_completed_successfully`; Compose itself refuses an unset or empty key (`:?` guard); `backend` takes `OBJECT_STORE_ENDPOINT`, `OBJECT_STORE_BUCKET` and both keys through `environment:` with the same expressions as `object-store-init`, so a shell value reaches both identically; `object-store-init` takes its keys through `environment:` with the same expressions (no `env_file`), runs once from the backend image with the module as entrypoint, and depends on `object-store` with `service_healthy` (which has a healthcheck); `backend` depends on `object-store-init` with `service_completed_successfully`; no `createbuckets` service and no `minio` service or `minio/*` image remain; `object-store` is `chrislusf/seaweedfs:4.51` by digest, has no `ports:`, exposes only 8333, mounts only `object_store_data`, takes `WEED_S3_SSE_KEY` from `AT_REST_ENCRYPTION_KEY`, and its command has no console, admin, WebDAV or SFTP option and keeps master, volume and filer on loopback (`TestCase test_object_store_is_pinned_internal_and_has_no_console_or_admin_option`, `test_backend_and_initialiser_resolve_the_same_store_settings`) | All tests of `ComposeWiring` pass (skipped with a message when `docker` is absent) |
| TC-014.2 | SR-040 (AC 2) | Unit: `backend/tests/core/test_object_store_credentials.py` (`cd backend && uv run pytest tests/core/test_object_store_credentials.py -v`). Started stack: manual, steps in TASK-174 Verification | Each of the four cases, for each key (unset, empty, known default, secret shorter than 16 characters), is rejected with a message naming `OBJECT_STORE_ACCESS_KEY` or `OBJECT_STORE_SECRET_KEY` and never the value; `python -m app.core.object_store_credentials` exits 1 (0 and silent for good keys); in the started stack the preflight exits 1 and `object-store` and `object-store-init` stay `Created`, not started; with good keys the preflight exits 0 and both start | Unit: all tests pass. Started stack: exit codes and container states as stated, recorded in TASK-174 "Verification results" (including a shell override with default keys, which the preflight rejects). Unset and empty keys are refused earlier by the Compose `:?` guard (TC-014.1); the preflight is run directly for those two cases |
| TC-014.3 | SR-040 (AC 2) | `infra/tests/test_compose_object_store.py`: `NoDefaultStrings`; `backend/tests/test_env_example.py` (`test_env_example_object_store_keys_are_empty`, `test_env_example_has_no_object_store_default_strings`); `git grep -n -i minioadmin -- ':!docs'` | The template holds empty object-store keys; the template, the Compose file, DEPLOY.md and the CI workflow hold no default credential string; test fixtures use non-default synthetic values | Tests pass; the `git grep` matches only the rule module and its tests, which name the default set |
| TC-014.4 | SR-040 (AC 4) | Unit: `backend/tests/core/test_object_store_init.py` (`cd backend && uv run pytest tests/core/test_object_store_init.py -v`). Started stack: manual, steps in TASK-175 Verification | The initialiser creates a missing bucket, sets and reads back `AES256` default encryption and expects `NoSuchBucketPolicy`; a second run changes nothing. It exits 1 with one line naming the failed step for an unreachable store, a failing create or encryption call, any other botocore transport error (closed connection, read timeout), an unexpected read-back and a bucket policy present, and prints no key value. In the started stack, on a fresh volume `docker compose up -d` starts the initialiser after `object-store` is healthy and creates the bucket; with a store it cannot reach, the initialiser exits 1 and `backend` stays `Created`, not started | Unit: all tests pass. Started stack: states and exit codes as stated, recorded in TASK-175 "Verification results" |
| TC-014.5 | SR-040 (AC 1) | Static: `infra/smoke-test.sh` check "object store has no console or admin option (SR-040 AC 1)" and `infra/tests/test_compose_object_store.py` (`test_object_store_is_pinned_internal_and_has_no_console_or_admin_option`). Started stack: manual, steps in TASK-176 Verification | The `object-store` command names no console, admin, WebDAV, SFTP or former console port (9001); no `ports:` entry; in the started stack a TCP connect to 9001 and to the other admin and internal SeaweedFS ports (9333, 19333, 8080, 18080, 8888, 18888, 7333, 12535, 8181, 9101) is refused from the `backend` container, and 9001 is refused from the host; `netstat` in the store shows only 8333 and 18333 off loopback | Static checks pass. Started stack: every probe refused as stated, S3 8333 answers, recorded in TASK-176 "Verification results" |
| TC-014.6 | SR-040 (AC 3, AC 5) | Static: `infra/tests/test_compose_object_store.py` (`test_object_store_network_is_internal_and_joined_only_by_backend_and_initialiser`). Started stack: `infra/smoke-test.sh` section "Object-store network isolation" (run with `COMPOSE_PROJECT_NAME=<project>`) and the upload/download steps in TASK-177 Verification | From `docker compose config --format json`: network `object-store` has `internal: true`; only `object-store`, `object-store-init` (that network only) and `backend` (`medhub` and `object-store`) join it; `reverse-proxy`, `frontend`, `postgres`, `redis` and `celery-worker` are on `medhub` only; `object-store-preflight` keeps `network_mode: none`; only `reverse-proxy` has `ports:`. Started stack: from each of the five containers a connection to `object-store:8333` fails (the name does not resolve), each probe preceded by a positive control with the same tool (`nc -z` in the nginx:alpine images, bash `/dev/tcp` elsewhere); from `backend` the connection succeeds and `ObjectStorageClient` stores, reads back and deletes an object; `docker compose port object-store 8333` is empty and `docker inspect` shows no `HostPort`; an attachment uploaded and downloaded through `https://localhost` is byte-identical and its object carries `AES256`. CI note (TASK-179): Docker cannot publish a port from a container on `internal` networks only, so the CI override attaches `object-store` to a CI-only network too | Static test passes. Started stack: every probe refused, backend round trip and download identical, no host port; counts recorded in TASK-177 "Verification results" |

## Acceptance criteria (class B unit level)

Unit acceptance (§5.5.3): the rule returns one rejection per problem, each naming its setting;
it accepts a short non-default access key; whitespace is stripped before the empty and default checks; the known-default comparison ignores case; the secret
boundary is 15 (rejected) and 16 (accepted) characters; no key value reaches stdout or stderr.

Unit acceptance of `U-OBJ-Init` (§5.5.3): it exits 0 only when the bucket exists, `GetBucketEncryption` reads back exactly `AES256` and `GetBucketPolicy` reports `NoSuchBucketPolicy`; any other outcome exits 1 with one line `object-store init failed: <step> …` naming the failed step (no traceback, also for transport errors other than "unreachable"); no key value reaches stdout or stderr; a second run on an initialised bucket changes nothing (idempotent); a missing `OBJECT_STORE_*` variable exits 1 naming it.

## Version history

- 1.3 (2026-10-30): TASK-176. Version 1.2 was approved, so this change bumps the version and clears
  the approval record. `minio` becomes `object-store` in TC-014.1 and TC-014.4; TC-014.1 adds the
  backend settings wiring and the pinned, internal, console-free server; TC-014.5 added for SR-040
  AC 1; TC-014.4 adds non-endpoint transport errors; the preconditions state the started-stack
  environment (own `-p` project, fresh volumes, temporary `.env` with `POSTGRES_PASSWORD`); the
  unit acceptance of `U-OBJ-Init` is stated (carried LOW findings of TASK-175 QA).
- 1.4 (2026-10-30): TASK-177. Version 1.3 was approved, so this change bumps the version and clears
  the approval record. Adds TC-014.6 (SR-040 AC 3 and AC 5: network membership and `internal: true`,
  started-stack probes from the five other containers and from the backend, no host port, upload and
  download) and the CI-only-network note for TASK-179.
