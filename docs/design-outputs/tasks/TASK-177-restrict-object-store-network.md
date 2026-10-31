---
id: "TASK-177"
type: task
title: "Restrict the object store to the backend and the bucket initialiser"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-040"
    relation: implements
  - target: "RISK-012"
    relation: mitigates
  - target: "RISK-001"
    relation: mitigates
  - target: "CR-002"
    relation: relates_to
  - target: "PRB-043"
    relation: relates_to
  - target: "TASK-176"
    relation: relates_to
tags: ["security", "network", "cr:CR-002", "issue:sancharly/medhub#33", "control:design"]
---

# TASK-177 — Restrict the object store to the backend and the bucket initialiser

- **Software item / unit:** SI-OBJSTORE `U-OBJ-Server` (ADD-025), deployment topology
- **Depends on:** TASK-176 (`relates_to`)
- **Branch:** `bug/minio-object-store`
- **Size:** S (Compose, smoke test, TS-014)
- **Needs:** a Docker host

## Objective

SR-040 AC 3. Only `backend` and `object-store-init` can reach the object store. Every other
service is refused, and nothing is published to the host. An actor with a foothold in any other
container can no longer reach the store (RISK-012).

## Interfaces to honor

- Add a network `object-store` with `internal: true`. The store needs no egress.
  - `object-store` and `object-store-init` join it only.
  - `backend` joins `medhub` and `object-store`.
  - `reverse-proxy`, `frontend`, `postgres`, `redis` and `celery-worker` stay on `medhub` only.
  - `object-store-preflight` keeps `network_mode: none`.
- Confirm CR-002 A-2 first: `celery-worker` never uses the object store
  (`grep -rn "ObjectStorageClient\|object_storage" backend/app/workers`). If it does, stop and
  report.
- Docker cannot publish a port from a container that is only on an `internal` network. The CI
  override of TASK-179 must therefore attach the store to a CI-only network as well. Record that
  in TS-014.

## Implementation detail

1. Make the Compose changes above.
2. Extend `infra/smoke-test.sh` with a started-stack section that is skipped, with a message,
   when the stack is not running, as the login check already is:
   - for each of `reverse-proxy`, `frontend`, `postgres`, `redis` and `celery-worker`: a
     connection attempt from inside the container to `object-store:<s3 port>` fails, because the
     name does not resolve or the connection is refused. Use a tool present in each image
     (`getent`, `nc`, `python` or bash `/dev/tcp`), and document the one chosen per image;
   - from `backend`: `ObjectStorageClient().put_object` and `get_object` round trip a test object,
     which is then deleted;
   - from the host: no port of the store is published (`docker compose port` is empty, and
     `docker inspect` shows no `HostPort`).
3. **TS-014** TC-014.6: the network membership assertions (static, from
   `docker compose config --format json`) and the started-stack checks above.

## Acceptance criteria

- [x] CR-002 **AC-3** / SR-040 AC 3: the store joins a network that only the backend and the
      initialiser join, and publishes no host port. Connections from the proxy, frontend,
      PostgreSQL, Redis and worker containers are refused. The backend can write and read an
      object.
- [x] SR-040 AC 5: verified against the deployment definition and a started stack.

## Verification

```sh
python3 -m unittest discover -s infra/tests -v
docker compose -f infra/docker-compose.yml up -d && bash infra/smoke-test.sh     # all checks pass, count recorded
```

Also an attachment upload and download through `https://localhost`, as in TASK-161 step 5, using
a test account created and removed for the run.

## Definition of Done

- [x] Infrastructure tests and smoke pass. The backend suite passes.
- [x] `traceability-check` shows no error for this task and TS-014.

## Verification results (software developer, 2026-10-30)

Environment: `DOCKER_CONTEXT=desktop-linux`, arm64 host. Started stack: project `cr002net` (fresh
volumes, not `infra`), temporary `infra/.env` made from the dev file with generated
`OBJECT_STORE_*` keys, `AT_REST_ENCRYPTION_KEY` (base64, 32 bytes), `POSTGRES_PASSWORD`,
`OBJECT_STORE_ENDPOINT=http://object-store:8333`. The dev `infra/.env` was restored byte-identical
(sha256 `a4933b8c...` before and after). No image or volume was removed; `infra_minio_data` and the
default `infra` project were not touched. Containers and networks of `cr002net` were removed; its
volumes `cr002net_*` were left.

Changes: `infra/docker-compose.yml` (network `object-store`, `internal: true`; `object-store` and
`object-store-init` on it only; `backend` on `medhub` and `object-store`), `infra/smoke-test.sh`
(section 10), `infra/tests/test_compose_object_store.py` (one test), TS-014 1.4 (TC-014.6,
`in_review`).

CR-002 A-2: `grep -rn "ObjectStorageClient\|object_storage" backend/app/workers` prints nothing; the
worker never uses the store.

- Static: `python3 -m unittest discover -s infra/tests` 25 tests OK (24 before; new
  `test_object_store_network_is_internal_and_joined_only_by_backend_and_initialiser`).
  `python3 infra/check_image_pins.py` exit 0.
- Smoke test on the started stack (`COMPOSE_PROJECT_NAME=cr002net bash infra/smoke-test.sh`):
  **27 passed, 0 failed**, including 8 new checks: five "cannot reach object-store:8333"
  (reverse-proxy and frontend with `nc -z`, as the nginx:alpine images have no bash; postgres, redis,
  celery-worker with bash `/dev/tcp`), each preceded by a positive control with the same tool,
  "backend reaches object-store:8333", "backend stores and reads back an object" (`ObjectStorageClient`
  put, get, delete) and "object-store publishes no host port". Stack not running: section skipped
  with a message.
- A container on the default network (`docker run --network cr002net_medhub`, backend image):
  `object-store:8333` gives `gaierror [Errno -2] Name or service not known`; to the store's IP
  (172.19.0.2) 8333, 9333 and 8888 all time out. From `backend`: `object-store:8333` and the IP
  connect. A container on `cr002net_object-store` only connects (the initialiser's position; the
  initialiser also ran successfully at start-up and `backend` started after it).
- `docker network inspect`: `cr002net_object-store` `internal=true`, members `backend`,
  `object-store`; `cr002net_medhub` `internal=false`, members reverse-proxy, frontend, postgres,
  backend, redis, celery-worker.
- Host: `docker compose port object-store 8333` empty; `docker inspect` `Ports` and `PortBindings`
  both `{}`.
- Upload and download through `https://localhost` (doctor and patient test accounts, consent
  granted, clinical entry created): 4096-byte upload, download HTTP 200, sha256 identical
  (`244aa831...`). The stored object has `ServerSideEncryption` `AES256`; bucket default encryption
  `AES256`. Test object deleted. The accounts could not be deleted (`fk_group_membership_account_id`
  and the clinical rows keep them), so they remain only in the throwaway volumes `cr002net_postgres_data`.
- Backend CI: `uv run pytest --cov=app --cov-fail-under=85` 554 passed, 91.31%; `ruff check` clean;
  `black --check` clean; `mypy app` no issues in 126 files.

Notes for QA and TASK-179: the CI override must attach `object-store` to a CI-only network as well
(recorded in TS-014 TC-014.6). Rerun: unit tests, the smoke test on a started stack with its own `-p`
project, and the network inspection above. `traceability-check` not run by the developer.

## QA review (qa-engineer, 2026-10-30) — APPROVED

QA reran everything itself, on `DOCKER_CONTEXT=desktop-linux` (arm64), Compose project `qa177`, with fresh
volumes. The temporary `infra/.env` had generated `OBJECT_STORE_*` keys, a base64 32-byte
`AT_REST_ENCRYPTION_KEY`, a `POSTGRES_PASSWORD` taken from `DATABASE_URL` and
`OBJECT_STORE_ENDPOINT=http://object-store:8333`. The dev `infra/.env` was restored byte-identical
(`cmp` clean; sha256 `a4933b8c82d6f81e35acd40b3188c21bf1b40419ac73e3dff2e3636823c696da` before and after).
QA removed only the containers and networks of `qa177`. The volumes `qa177_object_store_data`,
`qa177_postgres_data` and `qa177_redis_data` are left in place. `infra_minio_data` and the `infra` project
were not touched, and no image was removed.

| Check | Result |
|---|---|
| `python3 -m unittest discover -s infra/tests` | 25 tests OK |
| `python3 infra/check_image_pins.py` | exit 0 |
| CR-002 A-2: `grep -rn "ObjectStorageClient\|object_storage\|boto" backend/app/workers` | no match. The worker does not use the store |
| `cd backend && uv run pytest --cov=app --cov-fail-under=85` | 554 passed, 91.31 % |
| `ruff check .`, `black --check .`, `mypy app` | clean, 227 files unchanged, no issues in 126 files |
| `docker compose -p qa177 up -d --build` on fresh volumes | preflight exit 0. The store became healthy, then `object-store-init` exited 0 with `object-store init ok: bucket medhub private, AES256` (so the initialiser reaches the store from the `object-store` network). The backend became healthy after that |
| `COMPOSE_PROJECT_NAME=qa177 bash infra/smoke-test.sh` | **27 passed, 0 failed**. All 8 section-10 checks passed |
| `docker network inspect` | `qa177_object-store` has `internal=true` and members `backend`, `object-store`. `qa177_medhub` has `internal=false` and members redis, reverse-proxy, celery-worker, postgres, backend, frontend |
| Probe by name and by IP (172.19.0.2) from `docker run --network qa177_medhub` (backend image) | name: `gaierror -2` for 8333, 18333, 9333, 8888, 8080. IP: `TimeoutError` on all five ports. From the `celery-worker` container by IP, `/dev/tcp` to 8333 and 18333 timed out (rc 124) |
| Controls | `backend` → IP 8333 and 18333 connect. A container on `qa177_object-store` only (the initialiser's position) connects to 8333 and 18333 by name and by IP. 9333, 8888 and 8080 give `ECONNREFUSED`, because they are on loopback in the store. That network has no egress: 1.1.1.1:443 timed out |
| Host | `docker compose port object-store 8333` printed "no port", rc 1. `docker inspect` showed `Ports` `{}` and `PortBindings` `{}` |
| HTTPS round trip through `https://localhost` | Temporary doctor and patient accounts were created in the backend container. Login 200/200, consent 201, entry 201, then a 4096-byte upload: 201. Download 200, sha256 identical (`e177ec9a…ab3a`). `HeadObject` showed `ServerSideEncryption` `AES256`, and the bucket default is `AES256`. The test object was deleted (bucket `KeyCount` 0, and no `smoke/` key was left). The accounts stay in the throwaway `qa177_postgres_data` volume only |
| Smoke-test mutation M1: `docker network connect qa177_object-store qa177-redis-1` | `[FAIL] 'redis' cannot reach object-store:8333: connection succeeded`. Disconnected afterwards |
| Smoke-test mutation M2: a scratch copy with the `nc` tool for postgres (absent there) | `[FAIL] probe tool works in 'postgres' (control localhost:5432)`, and the negative probe is not counted |
| Smoke-test mutation M3: `docker stop qa177-object-store-1` with the rest of the stack up | section 10 `[SKIP]`, `19 passed, 0 failed`. See finding 1 |
| `traceability-check` (fallback parsers) on TASK-177, TS-014, SR-040, ADD-025, and on the whole project (373 records) | 0 errors, E10 0. Warnings in scope: W2 SR-040 (no TR yet, TASK-182), W5 SR-040 → RISK-012 (`in_review`), W5 TASK-176 → ADD-025. After this approval: W5 TASK-177 → RISK-012 (`in_review` until TASK-181), which is expected |

Positive-control design: the negative probes cannot pass as "cannot reach" because a tool is missing, an
`exec` fails or a container is stopped. Each of those makes the control fail, and the probe is then not
counted (M2). A wrong network membership is detected (M1). If the store is down, the negative probes still
pass, but `'backend' reaches object-store:8333` and the round trip then fail, so the section as a whole
fails. That holds only while the section runs at all (finding 1).

### Findings (none blocking)

1. **[MEDIUM] Section 10 skips instead of failing when the stack is up but the store or the backend is
   not** — `infra/smoke-test.sh:175` (`if [ -n "$(compose ps -q object-store …)" ] && [ -n "$(compose ps -q backend …)" ]`).
   With the store stopped and the rest of the project running, all 8 checks skip and the run reports
   `19 passed, 0 failed` with exit 0 (M3). This is a false green for the AC 5 evidence, and for the CI job
   if TASK-179 or TASK-182 run the script there. → Skip only when no container of the project is running
   (`[ -z "$(compose ps -q 2>/dev/null)" ]`). When the project is up, report a missing `object-store` or
   `backend` as `[FAIL]`. Carried to TASK-179, which edits the script for CI, unless fixed before this commit.
2. **[LOW] Three controls are loopback-only** — `infra/smoke-test.sh:177-178` (`frontend:nc:localhost:80`,
   `postgres:bash:localhost:5432`, `redis:bash:localhost:6379`). These controls prove that the tool and
   `exec` work. They do not prove that the container's resolver and bridge path work, yet the negative
   probe relies on name resolution failing. → Use peer-name controls on `medhub`, for example
   `frontend:nc:backend:8000`, `postgres:bash:redis:6379` and `redis:bash:postgres:5432`, as
   reverse-proxy and celery-worker already do. Optionally print a line when a control passes, so the
   output shows that it ran.
3. **[LOW] "Refused" wording** — SR-040 AC 3, CR-002 AC-3 and TS-014 TC-014.6 pass criteria ("every probe
   refused") versus what was observed: no TCP RST. By name the probe fails at DNS; by IP the
   connection times out, because the packets are dropped. → In the TASK-182 test report, read "refused"
   as "no connection established (name not resolved, or timed out)". TC-014.6's expected result
   already says that the name does not resolve.
4. **[LOW, evidence gap now closed] 18333** — the developer's by-IP probe covered 8333, 9333 and 8888,
   but not 18333, the port that SOUP-036 F-2 hands to TASK-177. QA probed it: it times out from
   `medhub`, and connects from the backend and from the store network. → TASK-181 can cite this
   result in the RISK-012 residual statement.

### Ruling on the developer's defect candidate (`backend/scripts/setup_test_data.py`)

This is a PRB. Raise it as a new PRB with criticality **minor**, outside CR-002. It is not a defect
of TASK-177. Hard-coded seed identities alone would be acceptable in a developer seeder. The defect
is this:

- The script ships in the runtime backend image: `backend/Dockerfile:15` has `COPY scripts/ ./scripts/`,
  and `ls scripts` in `qa177-backend-1` lists `setup_test_data.py`. So PRB-049's statement "not part
  of the shipped application" is inaccurate.
- It creates `ACTIVE` doctor and patient accounts with fixed, published passwords (`doctor123` and
  `patient123`, at `:214`, `:218` and `:220`, and printed at `:230`-`:232`; also listed in `docs/implementation-plan/SMOKE-RESULTS.md:7`).
  Those passwords are 9 characters, below `MIN_LENGTH = 12` (`backend/app/auth/password.py:28`). The
  script bypasses the policy and the activation flow because it hashes directly, and it writes no
  audit event.
- It adds the first SYSADMIN to the group "Test Clinic" (`:210`-`:211`), and it has no guard on
  `ENVIRONMENT`.

Why minor rather than major: running it needs a shell in the backend container, which already holds
`DATABASE_URL` and the keys. So it adds no capability for an attacker. The harm path needs an operator
error in production, and the seeded doctor still needs a patient's consent to see clinical data. No
version has been released, so no notification is needed.

Proposed resolution:
- Leave the script out of the runtime image.
- Make it refuse to run when `ENVIRONMENT=production`.
- Generate random passwords that meet the policy and print them once, or read them from arguments.
- Take the emails and group name as arguments.
