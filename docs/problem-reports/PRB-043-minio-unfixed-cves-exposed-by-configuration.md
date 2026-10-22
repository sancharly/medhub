---
id: "PRB-043"
type: problem-report
title: "Unfixed MinIO vulnerabilities are exposed by MedHub's object-store configuration"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
criticality: critical
links: []
tags: ["security", "soup", "configuration-management", "hazard:security", "hazard:data-integrity"]
---

# PRB-043 — Unfixed MinIO vulnerabilities are exposed by MedHub's object-store configuration

## Observed

The pinned MinIO server [SOUP-022](../soup/SOUP-022-minio.md) (`RELEASE.2025-09-07T16-13-09Z`) is
affected by four published vulnerabilities that no community release fixes. Their fixes ship only
in MinIO AIStor, or not at all (PRB-042):

| ID | Summary | Fixed in |
|---|---|---|
| CVE-2026-41145 (GHSA-hv4r-mvr4-25vw) | `STREAMING-UNSIGNED-PAYLOAD-TRAILER` upload with the credential in the query string skips the signature check: a valid **access key** alone allows writing any object | AIStor RELEASE.2026-04-11T03-20-12Z only |
| CVE-2026-40344 (GHSA-9c4q-hq6p-c237) | Snowball auto-extract handler skips the signature check: same precondition and effect | AIStor RELEASE.2026-04-11T03-20-12Z only |
| CVE-2026-113466 | Embedded console: hard-coded key in session-token authentication. The admin takeover is publicly disclosed | none |
| CVE-2026-34204 (GHSA-3rh2-v3gr-35p9) | `X-Minio-Replication-*` headers on a normal PutObject inject SSE metadata, so the object becomes permanently unreadable | AIStor RELEASE.2026-03-26T21-24-40Z only |

MedHub's configuration exposes all four:

- `infra/docker-compose.yml`, service `minio`: `command: server /data --console-address ":9001"`
  enables the console, and `expose: ["9000", "9001"]` makes both ports reachable from every
  container on the `medhub` network (reverse proxy, frontend, backend, Celery worker, PostgreSQL,
  Redis, `createbuckets`), not only from the backend.
- `infra/.env.example:24,26`: `OBJECT_STORE_ACCESS_KEY=minioadmin` (MinIO's well-known default) and
  `OBJECT_STORE_SECRET_KEY=changeme`, which `docker-compose.yml` passes as `MINIO_ROOT_USER` and
  `MINIO_ROOT_PASSWORD`. Nothing rejects these values at start-up. For CVE-2026-41145 and
  CVE-2026-40344 the access key alone is enough.
- `createbuckets` runs `mc mb` and `mc anonymous set none` but sets **no default bucket
  encryption**. An object written by any path other than the backend's own `put_object` (which
  requests `ServerSideEncryption="AES256"`, `backend/app/core/object_storage.py:40`) is stored
  unencrypted.
- `backend/app/attachments/service.py:79` computes a SHA-256 `checksum` at upload and stores it
  (`app/db/models/attachment.py:25`). No read path checks it, so a substituted object is served
  as the original.

## Impact

An actor with a foothold on the `medhub` network (a compromised container, or the host) can:

- write, replace or plant attachments and DICOM studies without the secret key, unencrypted at
  rest (CVE-2026-41145, CVE-2026-40344);
- take over the store as administrator through the console, and read every attachment, which
  SSE-S3 decrypts transparently, or modify and delete them (CVE-2026-113466);
- make chosen attachments permanently unreadable (CVE-2026-34204).

MedHub would then show substituted content to clinicians without any error. The control "server-side
encryption enforced on the object store" (RISK-011, SR-022) holds only for the backend's own write
path.

## Safety evaluation

This affects data integrity and a clinical decision: a clinician can be shown a substituted or
planted DICOM study or attachment for the patient. The hazard is recorded as
[RISK-012](../risks/RISK-012-object-store-compromised-or-unpatchable.md) (severity 4 ×
probability 2 → alarp), which also refers to the harms of RISK-002 and RISK-003 (integrity),
RISK-001 and RISK-011 (disclosure) and RISK-007 (availability).

Every path needs network reach to `minio:9000` or `:9001`. Neither port is published to the host
or proxied by nginx, which keeps the probability remote. But the vulnerabilities are public, will
never be fixed in this item, and the configuration gives them their full reach. `criticality:
critical`, as the human decided on 2026-10-22. It blocks any release (release gate of
`iec62304-sdlc`) until resolved.

Released versions (§9.3): no `release` record exists (`docs/releases/` is absent), so no released
version in use is affected and no notification is needed.

## Proposed resolution

CR-002 (human decision, 2026-10-22), configuration hardening plus checksum checking. These
measures do not depend on replacing the component (PRB-042):

1. Remove `--console-address ":9001"` and the `9001` `expose`. Bucket administration stays with
   `mc` (`createbuckets`), and `infra/DEPLOY.md` is updated with it.
2. Refuse to start with the default or example credentials (`minioadmin`, `changeme`), and
   document how to generate the access and secret keys.
3. Set default bucket encryption in `createbuckets` (`mc encrypt set sse-s3 …`), so every object
   is encrypted at rest whatever path wrote it.
4. Check the stored SHA-256 checksum on every attachment and DICOM download, and fail loudly on a
   mismatch (an error to the client, plus an audit event).
5. Put `minio` on a network that only `backend` and `createbuckets` join.
6. Test each measure: a negative test for the checksum mismatch, a configuration test for the
   console, credentials and network, and an end-to-end SSE check together with PRB-036.

Update RISK-012's control table and residual risk with the implementing tasks and their
verification.

## Source

Raised by TASK-154, the first SOUP anomaly-list review (CR-001 AC-12), on 2026-10-22. The evidence
is in SOUP-022's "Anomaly list review" section. Not resolved by CR-001 (A-4, D-4).
