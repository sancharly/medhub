---
id: "TASK-176"
type: task
title: "Replace the MinIO server with SeaweedFS pinned by tag and digest"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-028"
    relation: implements
  - target: "SR-022"
    relation: implements
  - target: "SR-040"
    relation: implements
  - target: "RISK-012"
    relation: mitigates
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-002"
    relation: relates_to
  - target: "PRB-042"
    relation: relates_to
  - target: "SOUP-022"
    relation: relates_to
  - target: "TASK-172"
    relation: relates_to
  - target: "TASK-175"
    relation: relates_to
tags: ["soup", "object-store", "configuration-management", "cr:CR-002", "issue:sancharly/medhub#33", "control:design"]
---

# TASK-176 — Replace the MinIO server with SeaweedFS pinned by tag and digest

- **Software item / unit:** SI-OBJSTORE `U-OBJ-Server` (ADD-025); SI-DEVINFRA `U-INF-CIPipeline`
  through the pin check (ADD-024)
- **Depends on:** TASK-172 (go result, the exact command line, the healthcheck and the digest)
  and TASK-175 (the initialiser that sets default encryption), as `relates_to` links
- **Branch:** `bug/minio-object-store`
- **Size:** M (Compose, `.env.example`, smoke test, SOUP-022, ADD-012, ADD-025, TS-013, TS-014,
  PRB-042)
- **Needs:** a Docker host and network access (Docker Hub). A second, empty Docker daemon is
  needed for the fresh-host check (see Verification).
- **Under another Q-1 answer:** (a) the image is AIStor's, and a licence file is mounted from the
  host and never committed. (c) the service is built from `infra/object-store/Dockerfile`, which
  verifies the archived binary's SHA-256 and minisign signature and fails on a mismatch. That
  variant also adds a tampered-binary negative test (AC-10), keeps SOUP-022 (updated, not
  obsolete) and moves no data.

## Objective

Resolve PRB-042. The object store becomes a maintained component that any host, amd64 included,
can pull from a public registry by pinned digest (SR-028 AC-7, CR-002 AC-9). It has no console or
admin UI (SR-040 AC 1). The MinIO server record goes `obsolete`.

## Interfaces to honor

- `ObjectStorageClient` does not change. Only `OBJECT_STORE_ENDPOINT` changes, to
  `http://object-store:<s3 port>`.
- Image reference: the multi-arch **index** digest recorded by TASK-172, never a per-platform
  digest.
- SSE key: `WEED_S3_SSE_KEY=${AT_REST_ENCRYPTION_KEY:?…}` (ADR-0015 D1). How that variable is
  handled stays with PRB-007 (Q-3).
- Keep the `minio_data` volume declared and untouched. TASK-178 migrates from it. Never run
  `docker volume rm` on it.

## Implementation detail

1. **Compose**: the `minio` service becomes `object-store`:
   - the pinned image and TASK-172's command line, with the admin UI, WebDAV, SFTP, Iceberg,
     Lance and metrics off;
   - the admin identity from `${OBJECT_STORE_ACCESS_KEY:?}` and `${OBJECT_STORE_SECRET_KEY:?}`;
   - a new volume `object_store_data`;
   - TASK-172's healthcheck;
   - `expose` the S3 port only;
   - the `depends_on` on the preflight from TASK-174.

   `object-store-init` now depends on `object-store: service_healthy`. Remove the
   `MINIO_KMS_SECRET_KEY` line and the `--console-address` option. The comment header names the
   component and ADR-0015.
2. **`infra/.env.example`**: set the new `OBJECT_STORE_ENDPOINT` and change the section heading.
3. **`infra/smoke-test.sh`**:
   - replace `minio` with `object-store` in the service lists;
   - the SSE check becomes "object-store SSE key configured (SR-022)";
   - add "object store has no console or admin option (SR-040 AC 1)", a static check on the
     command.

   Keep every existing check. Each added check counts towards AC-16.
4. **Started-stack checks (AC-1):** from the backend container (a Python socket connect) and
   from the host, a connection to the former console port 9001 and to the admin UI port is
   refused. Repeat AC-4 and AC-6 from TASK-175 on the new server.
5. **SOUP-022 → `obsolete`**:
   - bump the version and clear the approval record;
   - change-log entry "replaced by SOUP-036 (SeaweedFS), CR-002 TASK-176, ADR-0015".

   ADD-012 (version from TASK-175) drops `relates_to` SOUP-022. ADD-025 gains `relates_to`
   SOUP-036.
6. **TS-013** TC-013.10: the pinned object-store image is pulled, and the stack builds and
   starts, on a daemon with no cached images, amd64 included (SR-028 AC-7). **TS-014** TC-014.5:
   console and admin listeners absent.
7. **PRB-042** → `resolved`, with a `## Resolution` that names ADR-0015, the image and the
   fresh-host evidence.

## Acceptance criteria

- [ ] CR-002 **AC-1** / SR-040 AC 1: no console listener, console option or console port; a
      connection to the former console port is refused from the backend and from the host.
- [ ] CR-002 **AC-9** / SR-028 AC-7 (local evidence; CI evidence in TASK-179, final in
      TASK-182): on a daemon with no cached images, on amd64, `docker compose build` and
      `docker compose up -d` succeed from registries and version-controlled sources only.
- [ ] CR-002 **AC-4** and **AC-6** re-run on the new server.
- [ ] CR-002 **AC-12** (SOUP-022 part, pin check): SOUP-022 is `obsolete`, and
      `python3 infra/check_image_pins.py` exits 0.
- [ ] CR-002 **AC-19** (PRB-042 part): PRB-042 is `resolved`.

## Verification

```sh
python3 infra/check_image_pins.py && python3 -m unittest discover -s infra/tests -v
grep -n "9001\|console\|minio/minio\|minio/mc" infra/docker-compose.yml     # empty
# fresh daemon: a disposable docker:dind (pinned by digest) with an empty data root;
#   on arm64 run it with --platform linux/amd64. Inside: clone the branch, compose build + up.
#   Do NOT prune images on the reference workstation: it holds the only copy of the MinIO image TASK-178 needs.
docker compose -f infra/docker-compose.yml up -d && bash infra/smoke-test.sh
cd backend && uv run pytest
```

## Definition of Done

- [ ] Pin check, infrastructure tests, backend suite (coverage ≥ 85 %) and smoke all pass.
- [ ] SOUP-022 is `obsolete`, SOUP-036 is linked from ADD-025, and PRB-042 is `resolved`.
- [ ] `traceability-check` shows no error for the touched records.
