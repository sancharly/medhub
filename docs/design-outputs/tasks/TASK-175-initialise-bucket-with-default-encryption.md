---
id: "TASK-175"
type: task
title: "Initialise the bucket from the backend image with default encryption, and retire mc"
status: draft
version: "1.0"
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
     - built from `../backend`, with `env_file: .env`;
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

- [ ] CR-002 **AC-6** / SR-040 AC 4: the initialiser starts after the healthcheck passes. It exits
      non-zero against an unreachable store and on a failing command. On a fresh volume,
      `docker compose up -d` creates the bucket with no manual step.
- [ ] CR-002 **AC-4** / SR-022 AC 4 (on the current store): after the initialiser on a fresh
      volume, the bucket's default encryption is SSE-S3, and a plain upload is reported `AES256`.
- [ ] CR-002 **AC-12** (SOUP-023 part): SOUP-023 is `obsolete`, and ADD-012 no longer links it.
- [ ] CR-002 **AC-19** (PRB-039 part): PRB-039 is `resolved` with its `## Resolution`.

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

- [ ] Lint, type-check and the backend suite pass (coverage ≥ 85 %). The pin check and the
      infrastructure tests pass. Smoke passes.
- [ ] `traceability-check` shows no error for the touched records.
