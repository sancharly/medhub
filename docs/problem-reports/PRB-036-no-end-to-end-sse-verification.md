---
id: "PRB-036"
type: problem-report
title: "Server-side encryption of attachments is never verified against a real object store"
status: resolved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-30"
criticality: minor
links: []
tags: ["verification", "security", "encryption"]
---

# PRB-036 — Server-side encryption of attachments is never verified end to end

## Observed

`ObjectStorageClient` writes attachment objects with `ServerSideEncryption="AES256"`
(`backend/app/core/object_storage.py`). The only tests of that path assert that a mocked
`put_object` receives the parameter; no test writes an object to a real MinIO (or S3) endpoint and
confirms it is stored encrypted. CI runs no object-store service.

## Impact

- The at-rest encryption control for attachments (SR-022, RISK-001) is claimed verified, but the
  evidence covers only the call, not the store's behaviour.
- Until boto3 is declared (PRB-002, CR-001) the path never ran outside tests, so the gap was latent.

## Investigation

Root cause: the only tests of the encryption path mock the S3 client. `ObjectStorageClient.put_object`
passes `ServerSideEncryption="AES256"` (`backend/app/core/object_storage.py:40`), and the tests
assert that the mock received the parameter. No test or CI job starts an object store, so what the
store does with the parameter (stores the object encrypted, or rejects the write) was never
observed. CI has no object-store service container.

## Safety evaluation

No hazard is realized. The store (SeaweedFS since ADR-0015, replacing MinIO) has SSE-S3 default
encryption set on the attachment bucket by the initialiser (TASK-175, `AES256`, read back), so an
object written without an encryption request is still stored encrypted; a store that rejected the
parameter would fail the write loudly (attachment unavailable, RISK-007) rather than store
plaintext silently. The gap was in verification evidence, hence `minor`. No released version is
affected (PLAN-001 has no `release` record and the repository has no release tag), so no
notification is needed.

## Resolution

CR-002 (TASK-179) adds an automated check of the encryption path against the real object store
(the store is SeaweedFS since ADR-0015, which replaced MinIO):

- `backend/tests/integration/test_object_store_sse.py` (pytest marker `object_store`, registered in
  `backend/pyproject.toml`; skipped unless `OBJECT_STORE_INTEGRATION=1`, so the normal suite is
  unchanged). Test 1 writes through `ObjectStorageClient.put_object`, asserts a raw
  `head_object` reports `ServerSideEncryption: AES256` and that `get_object` returns the original
  bytes. Test 2 asserts `get_bucket_encryption` has an `AES256` rule. Test 3 asserts a raw
  `put_object` with no encryption request is reported `AES256`. Test 4 creates a uniquely named
  bucket with no default (`get_bucket_encryption` raises
  `ServerSideEncryptionConfigurationNotFoundError`), points `OBJECT_STORE_BUCKET` at it and shows
  that `ObjectStorageClient.put_object` alone makes `head_object` report `AES256`; the bucket
  default would otherwise mask a missing request parameter.
- CI job `object-store-integration` (`.github/workflows/ci.yml`) runs on every push and pull
  request: it generates throwaway credentials, starts the store with
  `infra/docker-compose.yml` plus the CI-only `infra/compose.ci-object-store.yml` (a service
  container cannot take the server's command line; the override publishes the S3 port on
  `127.0.0.1` over an extra network), runs the marked tests, and always runs `down -v`.
- Listed as TC-008.8 in TS-008 (`verifies` SR-022).

Verification (reproducible): the job's steps run locally in their own Compose project
(the job uses project `medhub-ci`; `OBJECT_STORE_CI_PORT=18333` locally): 4 passed. With
`ServerSideEncryption` removed from `put_object`, test 4 fails (`KeyError: 'ServerSideEncryption'`)
and tests 1 to 3 pass because of the bucket default; with the bucket default also deleted, tests 1
to 3 fail too. Commands and output are in
TASK-179 "Verification results". The run on a GitHub-hosted runner is pending until the branch is
pushed (TASK-182).

## Source

Raised during the Risk stage of CR-001 (2026-10-22), Q-4; out of scope for that CR.
