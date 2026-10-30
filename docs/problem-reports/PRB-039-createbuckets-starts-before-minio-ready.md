---
id: "PRB-039"
type: problem-report
title: "Bucket initialisation runs before MinIO accepts connections"
status: resolved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-30"
criticality: minor
links: []
tags: ["infrastructure", "verification"]
---

# PRB-039 — Bucket initialisation runs before MinIO accepts connections

## Observed

In `infra/docker-compose.yml` the one-shot `createbuckets` service depends on `minio` with
`condition: service_started`, and `minio` has no healthcheck. On `docker compose up -d` the `mc`
container starts while MinIO is still initialising and its three commands fail with
`connection refused` (alias set, `mc mb`, `mc anonymous set`); the entrypoint ends with `exit 0`, so
the failure is silent at the Compose level. Observed on 2026-10-22 during TASK-155 verification of the
pinned stack. The compose dependency is unchanged by CR-001, so the pre-pinning stack has the same
race; it was not captured in the baseline run.

## Impact

On a fresh `minio_data` volume the `medhub` bucket is not created, and attachment storage (SR-013)
fails until the bucket is created by hand. On an existing volume (as on the reference workstation,
where the bucket already existed) the failure is hidden.

## Investigation

Root cause: `createbuckets` waits for `minio` with `condition: service_started`
(`infra/docker-compose.yml:115-117`), which only means that the container process was created, and
`minio` defines no healthcheck. The entrypoint (`infra/docker-compose.yml:118-124`) runs `mc alias
set`, `mc mb` and `mc anonymous set` once, each of which fails with `connection refused` while the
server initialises, and ends with `exit 0;`, which hides the failure. On a fresh volume the bucket is
never created.

## Safety evaluation

No hazard is realized: the failure is loud at first use (attachment unavailable, RISK-007), and no
data is stored unencrypted. Hence `minor`. No released version is affected (PLAN-001 has no `release`
record and the repository has no release tag), so no notification is needed.

## Proposed resolution

Give `minio` a healthcheck and make `createbuckets` depend on `service_healthy`, or retry the alias
command until it succeeds, and make the entrypoint fail when bucket creation fails. Needs a task and
a CR.

## Source

Found by the software developer while running TASK-155 verification (AC-5); out of scope for CR-001.

## Resolution

Resolved by CR-002 TASK-175 (ADR-0015 D2), in the commit "FIX: Initialise the bucket from the backend
image with default encryption (TASK-175)" on branch `bug/minio-object-store`.

- `infra/docker-compose.yml`: `minio` has a healthcheck (`curl -fsS http://localhost:9000/minio/health/ready`,
  every 5 s, 24 retries). The `createbuckets` service and its `minio/mc` image are replaced by
  `object-store-init`, built from the backend image, with the entrypoint
  `python -m app.core.object_store_init`, `restart: "no"`, and `depends_on` `minio: service_healthy` and
  `object-store-preflight: service_completed_successfully`. It takes the object-store keys through
  `environment:` with the same `${OBJECT_STORE_*:?...}` expressions as `minio` and the preflight.
  `backend` depends on `object-store-init: service_completed_successfully`, so a failed initialisation
  keeps the backend down.
- `backend/app/core/object_store_init.py`: boto3 calls only. Creates the bucket if `head_bucket` answers
  404, sets AES256 default encryption, reads it back, and expects `NoSuchBucketPolicy`. It exits 1 with one
  line naming the failed step on any error (unreachable store, create or encryption call refused,
  unexpected read-back, policy present) and exits 0 only when every step holds. The old `exit 0;` that hid
  failures is gone.
- Verification: unit tests (`backend/tests/core/test_object_store_init.py`, 13), wiring tests
  (`infra/tests/test_compose_object_store.py`) and a started stack on fresh volumes (Compose project
  `cr002-init`): `minio` reached healthy before the initialiser started, the initialiser exited 0 and the
  bucket existed with no manual step; with an unreachable endpoint (project `cr002-neg`) it exited 1 and
  `backend` stayed `Created`. Recorded in TASK-175 "Verification results"; TS-014 TC-014.4.
- To repeat it:
  - `cd backend && uv run pytest tests/core/test_object_store_init.py` (13 passed) and
    `uv run pytest --cov=app --cov-fail-under=85` (552 passed, 91.30 %);
  - `python3 -m unittest discover -s infra/tests -v` (22 OK);
  - with `DOCKER_CONTEXT` set to the Docker Desktop context and a temporary `infra/.env` holding
    generated object-store keys and a `POSTGRES_PASSWORD`, run
    `docker compose -f infra/docker-compose.yml -p <fresh project> up -d --build` on fresh volumes.
    Check that `minio` reports healthy before `object-store-init` starts (`docker events`), that the
    initialiser exits 0, and that `get_bucket_encryption` returns AES256. Then run
    `OBJECT_STORE_ENDPOINT=http://127.0.0.1:1 docker compose … -p <other project> up -d backend` and
    check that `object-store-init` exits 1 and `backend` stays `Created`. Reproduced by QA on
    2026-10-30 (projects `qa175`, `qa175o`, `qa175neg`).
