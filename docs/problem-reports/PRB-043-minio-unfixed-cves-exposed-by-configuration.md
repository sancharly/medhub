---
id: "PRB-043"
type: problem-report
title: "Unfixed MinIO vulnerabilities are exposed by MedHub's object-store configuration"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-30"
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

## Investigation

Root cause: nothing in the deployment limits who can reach the object store or what it exposes, and
the application trusts the store's content without checking it.

- `infra/docker-compose.yml:97` starts the server with the console; `:105-107` expose ports 9000
  and 9001 to the whole `medhub` network (`:108-109` is the only network).
- `infra/docker-compose.yml:99-100` take the root credentials from `OBJECT_STORE_ACCESS_KEY` and
  `OBJECT_STORE_SECRET_KEY`; `infra/.env.example:24,26` set them to `minioadmin` and `changeme`, and
  no start-up check rejects them.
- `infra/docker-compose.yml:118-124` (`createbuckets`) creates the bucket and sets it private but
  sets no default encryption. Only the backend's own write requests `ServerSideEncryption="AES256"`
  (`backend/app/core/object_storage.py:40`).
- `backend/app/attachments/service.py:79` computes the SHA-256 and `:92` stores it; the read path
  `AttachmentService.open` (`:115-137`) fetches the object and returns it without comparing it.

Root cause of the exposure is therefore configuration plus a missing integrity check. The component
defects themselves cannot be fixed (PRB-042).

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

After resolution (2026-10-30, TASK-181): every exposure below is closed by a verified control, and
RISK-012 is re-scored from that evidence to severity 4 × probability 1 → `acceptable` (`in_review`,
the human accepts it). The `criticality` stays `critical`: it records the actual impact of the
problem as found, and the resolution does not lower it. PRB-043 is `resolved` under CR-002 AC-19.
Under the `iec62304-sdlc` release gate and MedTrace E10 (`release_with_open_critical`) it still
counts as an open `critical` PRB until it is `closed`. Closing it is planned for the release (REL)
record commit, after the release test report (TR) confirms the resolution.

## Resolution

Resolved by CR-002 (`resolves` PRB-043) on branch `bug/minio-object-store`, under ADR-0015 option
(b): MinIO is replaced by SeaweedFS 4.51 (SOUP-036) and the configuration is hardened. Each
exposure is closed by the control and commit named below, verified by the recorded evidence (all
tasks approved by QA on 2026-10-30).

**The four CVEs: removed with the component.**

| CVE | Exposure in MedHub | Closed by | Evidence |
|---|---|---|---|
| CVE-2026-41145 | Write any object with the access key alone | MinIO server no longer deployed: TASK-176 (`9d3b395`). Defence in depth: TASK-177 (reach), TASK-174 (no default access key), TASK-173 (a written object is refused on download if it differs) | TS-014 TC-014.1: no `minio` service or `minio/*` image in `infra/docker-compose.yml`; `grep -n "9001\|console\|minio/minio\|minio/mc" infra/docker-compose.yml` → no output (TASK-176 QA). SOUP-022 `obsolete`. SOUP-036 review: no advisory affects 4.51 |
| CVE-2026-40344 | Same, through the Snowball auto-extract handler | As above | As above |
| CVE-2026-113466 | Console admin takeover | MinIO and its console removed (TASK-176); the replacement has no console or admin listener | TS-014 TC-014.5: from `backend`, 9001 and every admin or internal port refused; `netstat` shows only 8333 and 18333 off loopback |
| CVE-2026-34204 | SSE metadata injection makes an object unreadable | MinIO removed (TASK-176) | TS-014 TC-014.1; SOUP-022 `obsolete`. Remaining unreadability cause (key loss, SOUP-036 F-4) is RISK-011's |

**The five configuration findings: each closed by its own control.**

| Finding (Investigation) | Closed by | Evidence (reproducible) |
|---|---|---|
| 1. Console enabled (`--console-address ":9001"`) | TASK-176 (`9d3b395`): `object-store` runs `weed server` with no console, admin, WebDAV or SFTP option; internal master, volume and filer ports bound to 127.0.0.1 | `python3 -m unittest discover -s infra/tests -v` (`test_object_store_is_pinned_internal_and_has_no_console_or_admin_option`); `infra/smoke-test.sh` check "object store has no console or admin option (SR-040 AC 1)"; started-stack probes of TS-014 TC-014.5 (TASK-176 "Verification results" and QA review) |
| 2. Ports reachable from every container on `medhub` | TASK-177 (`d4cdba0`): internal network `object-store`, joined only by `object-store`, `object-store-init` and `backend`; `expose: 8333` only, no `ports:` | `test_object_store_network_is_internal_and_joined_only_by_backend_and_initialiser`; `COMPOSE_PROJECT_NAME=<p> bash infra/smoke-test.sh` section 10 (27/27 in TASK-177 QA, mutations M1..M3); QA probes by name and IP from `medhub` on 8333, 18333, 9333, 8888, 8080: not resolved or timed out (TS-014 TC-014.6) |
| 3. Default credentials accepted (`minioadmin`, `changeme`) | TASK-174 (`8c46bcc`): `object-store-preflight` rejects an unset, empty or known-default key, or a secret shorter than 16 characters, before the store starts; `.env.example` ships empty keys; Compose `:?` guards | `cd backend && uv run pytest tests/core/test_object_store_credentials.py tests/test_env_example.py -v`; `git grep -n -i minioadmin -- ':!docs'` matches only the rule module and the tests that name the default set; started-stack cases in TASK-174 "Verification results (round 2)" (TS-014 TC-014.1..3) |
| 4. No default bucket encryption | TASK-175 (`684ee7b`): `object-store-init` (backend image, `mc` retired) sets and reads back `AES256` default encryption and fails closed; re-run on SeaweedFS by TASK-176. TASK-179 (`aa2fd61`) checks it end to end in CI | `cd backend && uv run pytest tests/core/test_object_store_init.py -v`; started stack: `get_bucket_encryption` → `AES256`, a plain `put_object` reported `AES256` (TS-008 TC-008.6, TS-014 TC-014.4); CI job `object-store-integration` (TS-008 TC-008.8: 4 passed in QA's run of the job steps; hosted run is TASK-182's) |
| 5. Checksum stored but never checked on download | TASK-173 (`0e01b2a`): `AttachmentService.open` compares the SHA-256 of the fetched bytes with `Attachment.checksum`; a mismatch is refused with 502 `attachment-integrity-failure` and a committed `ATTACHMENT_ACCESS` FAILURE audit event; both callers (attachment route, DICOM route) covered | `cd backend && uv run pytest --cov=app --cov-fail-under=85` and `uv run pytest modules/dicom_viewer/tests` (TS-007 TC-007.6..8); mutation: comparison replaced by `if False:` → 4 tests fail (TASK-173 QA) |

Existing objects were migrated by a rehearsed procedure (TASK-178, `db0b480`; TS-008 TC-008.7), and
the operator documentation describes the new store, its keys and the migration (TASK-180,
`d2b557a`). RISK-012 1.1 records each control with its verification and the re-scored residual.

**Not covered here:** the shared `AT_REST_ENCRYPTION_KEY` (field encryption and SSE) stays with
PRB-007 (CR-002 Q-3, Q-7); the backup and restore of the store with its key is PRB-057. The hosted
CI run and the fresh-host run are verified by TASK-182 before CR-002 closes.

## Source

Raised by TASK-154, the first SOUP anomaly-list review (CR-001 AC-12), on 2026-10-22. The evidence
is in SOUP-022's "Anomaly list review" section. Not resolved by CR-001 (A-4, D-4).
