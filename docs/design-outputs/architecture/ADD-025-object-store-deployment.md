---
id: "ADD-025"
type: architecture-doc
title: "Object store deployment (SI-OBJSTORE)"
status: in_review
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
safety_class: B
links:
  - target: "SR-040"
    relation: implements
  - target: "SR-022"
    relation: implements
  - target: "SR-028"
    relation: implements
  - target: "RISK-012"
    relation: relates_to
  - target: "RISK-007"
    relation: relates_to
  - target: "RISK-011"
    relation: relates_to
  - target: "SOUP-019"
    relation: relates_to
  - target: "SOUP-036"
    relation: relates_to
tags:
  - software-item:SI-OBJSTORE
  - class:B
  - layer:infrastructure
  - cr:CR-002
---

# ADD-025 — Object store deployment (SI-OBJSTORE)

## Responsibility

The deployed object store that holds every attachment and DICOM study: the server, its start-up
gate on credentials, its bucket initialisation with default encryption, and its network reach.
`SI-ATTACH` ([ADD-012](ADD-012-attachment-service.md)) is the only runtime client. No PHI is
handled here in clear text beyond what the S3 server decrypts for an authorised backend request.

The component (product and version) is decided by
[ADR-0015](../../design/adr/0015-object-store-component-after-minio.md), which the human accepted
with Q-1 (SeaweedFS 4.51, [SOUP-036](../../soup/SOUP-036-seaweedfs.md)). TASK-176 added the
`relates_to` link to SOUP-036, and TASK-175 and TASK-176 removed the links to the retired MinIO
records.

## Software units (IEC 62304 §5.4.1)

- `U-OBJ-Preflight`: the Compose service `object-store-preflight`. It runs the credential rule
  (CR-002 Q-2) from the backend image with `network_mode: none` and exits non-zero, naming the
  rejected setting, when a key is unset, empty, a known default, or a secret key shorter than 16
  characters. `object-store` and `object-store-init` depend on its successful completion
  (SR-040 AC 2). Implemented by TASK-174.
- `U-OBJ-Server`: the Compose service `object-store`. It is the S3-compatible server pinned by
  tag and index digest. It has no console or admin UI, keeps its data on one named volume, derives
  its SSE-S3 key from `AT_REST_ENCRYPTION_KEY`, and has a healthcheck. It joins only the
  `object-store` network and publishes no host port (SR-040 AC 1 and AC 3, SR-022, SR-028 AC-5 and
  AC-7). Implemented by TASK-176 and TASK-177.
- `U-OBJ-Init`: the Compose service `object-store-init`, which runs a Python module in the
  backend image with boto3 (SOUP-019). It starts once `object-store` is `service_healthy`. It
  creates the bucket if missing, sets SSE-S3 default encryption (`PutBucketEncryption`, `AES256`),
  reads it back, checks that the bucket has no policy, and exits non-zero on any failure. The
  backend starts only after it has completed successfully (SR-040 AC 4, SR-022 AC 4).
  Implemented by TASK-175.

Class B requires decomposition down to software units only.

## Requirements implemented

- SR-040 AC 1 to 5 (console, credentials, network, initialisation, verification against a started
  stack).
- SR-022 AC 4 (default bucket encryption, whichever path wrote the object) and AC 5 (verification
  against a real store, with SI-ATTACH).
- SR-028 AC-5 and AC-7 (pinned image, obtainable on a host with no cached images).

Non-functional requirements constraining this item: NFR-007.

## Interfaces

- Provides: the S3 API on `object-store:<s3 port>` over the `object-store` network, consumed by
  `ObjectStorageClient` (`backend/app/core/object_storage.py`) through `OBJECT_STORE_ENDPOINT`.
- Consumes: `OBJECT_STORE_ACCESS_KEY`, `OBJECT_STORE_SECRET_KEY`, `OBJECT_STORE_BUCKET` and
  `AT_REST_ENCRYPTION_KEY` from `infra/.env`, which is never committed.

## Verification

- [TS-014](../tests-specifications/) (new, created by TASK-174; it `verifies` SR-040) covers the
  Compose-file assertions, the four preflight cases, the initialiser's failure exits and the
  started-stack connection checks.
- TS-008 (SR-022 AC 4 and AC 5) covers the default-encryption check and the CI job
  `object-store-integration` (TASK-179).
- TS-013 (SR-028 AC-7) covers the fresh-host pull and build (TASK-176, TASK-182).

## Architecture narrative

[07 deployment view](../../design/07-deployment-view.md) (topology, networks, operational
notes) and [05 building blocks](../../design/05-building-blocks.md) (the item and its units). The
deployment procedure is in `infra/DEPLOY.md`. TASK-180 updates all three. Governing decisions:
[ADR-0009](../../design/adr/0009-file-object-storage.md),
[ADR-0010](../../design/adr/0010-deployment-model.md) and
[ADR-0015](../../design/adr/0015-object-store-component-after-minio.md).

## Risk relevance

Carries controls of [RISK-012](../../risks/RISK-012-object-store-compromised-or-unpatchable.md)
(console, credentials, network, default encryption, a maintained component). It also supports
RISK-007 (reliable initialisation) and RISK-011 (SSE key material and its migration).

## Version history

- 1.0 (2026-10-30): created at the CR-002 Plan stage (Software Architect role).
- 1.1 (2026-10-30): TASK-176. `relates_to` SOUP-036 added; the Compose service `object-store`
  (SeaweedFS 4.51 by digest) implements `U-OBJ-Server`. Approval not yet given.
