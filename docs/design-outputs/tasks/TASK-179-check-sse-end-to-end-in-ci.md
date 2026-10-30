---
id: "TASK-179"
type: task
title: "Check encryption end to end against the real object store in CI"
status: draft
version: "1.0"
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
- **Size:** S (1 test module, a pytest marker, 1 Compose override, 1 CI job, TS-008, PRB-036)
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

- [ ] CR-002 **AC-7** / SR-022 AC 5: the check writes through `put_object` to a real store,
      asserts `AES256` and reads back the original bytes. It runs in CI on every pull request and
      is listed in TS-008.
- [ ] CR-002 **AC-4** re-checked in CI. **AC-9** CI part: the store is pulled and started on a
      fresh amd64 runner.
- [ ] CR-002 **AC-19** (PRB-036 part): PRB-036 is `resolved`.
- [ ] CR-002 **AC-15** (SR-022 part): TS-008 `verifies` SR-022 and lists TC-008.6 and TC-008.8.

## Verification

```sh
python3 infra/check_image_pins.py
docker compose -f infra/docker-compose.yml -f infra/compose.ci-object-store.yml up -d --wait object-store-preflight object-store object-store-init
cd backend && OBJECT_STORE_INTEGRATION=1 OBJECT_STORE_ENDPOINT=http://127.0.0.1:<port> uv run pytest -m object_store -v
cd backend && uv run pytest     # integration test skipped, rest unchanged
```

CI on the branch head: `object-store-integration` is green. Also show that the test fails when
`ServerSideEncryption` is removed from `put_object` and the bucket default is not set. Use a
scratch run, and record it.

## Definition of Done

- [ ] The new CI job and every existing job are green on the branch head.
- [ ] `traceability-check` shows no error for this task, TS-008 and PRB-036.
