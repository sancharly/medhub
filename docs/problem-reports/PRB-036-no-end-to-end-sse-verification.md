---
id: "PRB-036"
type: problem-report
title: "Server-side encryption of attachments is never verified against a real object store"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
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

## Safety evaluation

No hazard is realized: a misconfigured encryption setting makes MinIO reject the write, so the
failure is loud (attachment unavailable, RISK-007) rather than silent plaintext storage. The gap is
in verification evidence, hence `minor`.

## Proposed resolution

Add an integration test (or a smoke-test step) that writes an object through `ObjectStorageClient`
to a MinIO service and asserts the stored object reports `ServerSideEncryption: AES256`, and record
it against SR-022. Depends on the object-store decision under CR-001 D-4. Needs a task and a CR.

## Source

Raised during the Risk stage of CR-001 (2026-10-22), Q-4; out of scope for that CR.
