---
id: "TASK-176"
type: task
title: "Replace the MinIO server with SeaweedFS pinned by tag and digest"
status: approved
version: "1.2"
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
  - target: "SOUP-036"
    relation: relates_to
  - target: "ADD-025"
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

- [x] CR-002 **AC-1** / SR-040 AC 1: no console listener, console option or console port; a
      connection to the former console port is refused from the backend and from the host.
- [x] CR-002 **AC-9** / SR-028 AC-7 (local evidence; CI evidence in TASK-179, final in
      TASK-182): on a daemon with no cached images, on amd64, `docker compose build` and
      `docker compose up -d` succeed from registries and version-controlled sources only.
- [x] CR-002 **AC-4** and **AC-6** re-run on the new server.
- [x] CR-002 **AC-12** (SOUP-022 part, pin check): SOUP-022 is `obsolete`, and
      `python3 infra/check_image_pins.py` exits 0.
- [x] CR-002 **AC-19** (PRB-042 part): PRB-042 is `resolved`.

## Verification

```sh
python3 infra/check_image_pins.py && python3 -m unittest discover -s infra/tests -v
grep -n "9001\|console\|minio/minio\|minio/mc" infra/docker-compose.yml     # empty
# fresh daemon (as run on 2026-10-30, arm64 host): a disposable docker:dind with an empty data root.
#   An amd64 docker:dind does not start on an arm64 host (iptables under emulation), so the inner
#   daemon is arm64-native and only the inner client targets amd64.
#   Do NOT prune images on the reference workstation: it holds the only copy of the MinIO image TASK-178 needs.
export DOCKER_CONTEXT=<live daemon>
docker run -d --name cr002-dind --privileged -e DOCKER_TLS_CERTDIR= \
  docker@sha256:cb160a57fcb936668f8ab8e4a9d73c66b7975226aa87e466233734edbcd83ccc   # arm64 entry of docker:dind index sha256:9e79b879b177fbd72c34376a3dd3d91747da5db49e1f560f76aea59561471977
docker exec cr002-dind docker info --format 'images={{.Images}}'                    # 0
# the version-controlled tree (docs/ left out) plus a temporary infra/.env and the gitignored dev cert pair:
( git ls-files -co --exclude-standard; echo infra/.env ) | sort -u | grep -v '^docs/' > files.txt
docker exec cr002-dind mkdir -p /work
tar -cf - -T files.txt infra/certs/server.crt infra/certs/server.key | docker exec -i cr002-dind tar -xf - -C /work
docker exec -e DOCKER_DEFAULT_PLATFORM=linux/amd64 -w /work/infra cr002-dind sh -c \
  'docker compose -p cr002-fresh build && docker compose -p cr002-fresh up -d && docker compose -p cr002-fresh ps -a'
docker exec cr002-dind docker exec cr002-fresh-object-store-1 weed version          # ... 4.51 ... linux amd64
docker rm -f -v cr002-dind                                                          # only this container and its anonymous volume
# On an amd64 host: the same, with an amd64 daemon and no DOCKER_DEFAULT_PLATFORM.
docker compose -f infra/docker-compose.yml up -d && bash infra/smoke-test.sh
cd backend && uv run pytest
```

## Definition of Done

- [x] Pin check, infrastructure tests, backend suite (coverage ≥ 85 %) and smoke all pass.
- [x] SOUP-022 is `obsolete`, SOUP-036 is linked from ADD-025, and PRB-042 is `resolved`.
- [x] `traceability-check` shows no error for the touched records.

## Verification results (software developer, 2026-10-30)

Environment: `DOCKER_CONTEXT=desktop-linux` (Docker Desktop 24.0.5, arm64 host). Started-stack runs
used project `cr002-seaweed` (fresh volumes, not `infra`) and a temporary `infra/.env` made from
the dev file with generated `OBJECT_STORE_*` keys, a generated `AT_REST_ENCRYPTION_KEY` (base64 of
32 bytes, as `backend/app/db/crypto.py` requires) and `POSTGRES_PASSWORD`. The dev `infra/.env`
was restored byte-identical (`cmp` OK, sha1 `714c7630...`). No volume and no image was removed;
`infra_minio_data` and the cached MinIO images were not touched. Containers and networks of
`cr002-seaweed` and the dind container were removed; volumes `cr002-seaweed_*` were left.

What changed: `infra/docker-compose.yml` (service `object-store`, volume `object_store_data`,
`minio_data` kept declared and unmounted, `backend` `environment:` block), `infra/.env.example`,
`infra/smoke-test.sh`, `infra/tests/test_compose_object_store.py`,
`backend/app/core/object_store_init.py` and its test, SOUP-022, SOUP-036, ADD-025, ADD-012,
TS-013, TS-014, PRB-042, this TASK.

Commands and results:

- `python3 infra/check_image_pins.py`: exit 0. `python3 -m unittest discover -s infra/tests -v`:
  24 tests OK (22 before; +2 new wiring tests).
- `grep -n "9001\|console\|minio/minio\|minio/mc" infra/docker-compose.yml`: no output (exit 1).
- `cd backend && uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85`: 554
  passed, 91.31 %. `uv run ruff check .`, `uv run black --check app tests`, `uv run mypy app`
  (126 files): clean. `uv run pytest tests/core/test_object_store_init.py`: 15 passed (13 + 2).
- Started stack, fresh volumes: `docker compose -p cr002-seaweed -f infra/docker-compose.yml up -d
  --build`: preflight Exited (0), `object-store` Healthy, `object-store-init` Exited (0)
  ("object-store init ok: bucket medhub private, AES256"), `backend` started, no manual step.
  The base64 `AT_REST_ENCRYPTION_KEY` works as `WEED_S3_SSE_KEY` (log: "Derived KEK from s3.sse.key
  config").
- `bash infra/smoke-test.sh`: **19 passed, 0 failed** (the 17 earlier checks, with `minio` replaced
  by `object-store`, plus "object store has no console or admin option (SR-040 AC 1)" and the
  `object_store_data` volume check; the SSE check is now "object-store SSE key configured
  (SR-022)").
- From `backend` (boto3, endpoint and bucket as the backend's own environment holds them,
  `http://object-store:8333`, `medhub`): `get_bucket_encryption` gave `AES256`; a plain
  `put_object` with no SSE argument then `head_object` gave `ServerSideEncryption: AES256`; an
  explicit `AES256` put also gave `AES256` and `get_object` returned the bytes;
  `get_bucket_policy` gave `NoSuchBucketPolicy`; test objects deleted (`KeyCount` 0). A marker
  object was not found in `/data` (`grep -rl`, exit 1), and after `docker restart object-store` it
  still decrypted (`AES256`).

Per acceptance criterion:

- **AC-1 / SR-040 AC 1:** the command has no console, admin, WebDAV or SFTP option; no `ports:`;
  `expose: 8333` only. TCP connect from `backend` to `object-store`: 9001, 9000, 9333, 19333,
  8080, 18080, 8888, 18888, 7333, 12535, 8181 and 9101 all `ConnectionRefusedError`; 8333 and
  18333 open (by design, 18333 is TASK-177's). From the host (`/dev/tcp/127.0.0.1`): 9001, 9000,
  8333, 18333, 8888 and 9333 refused (nothing published; only the reverse proxy publishes 80/443).
  `netstat -tln` in the store: 8333 and 18333 on `:::`; 9333, 19333, 8080, 18080, 8888, 18888 on
  127.0.0.1. (The `docker ps` PORTS column lists 7333, 8080 and others: they come from the
  image's `EXPOSE` metadata and are not published or listening.) Correction to TASK-172 Evidence
  section 3: the sentence "from a peer container the same probes now: 9333, 9340 and 8888 refused"
  names 9340, a `weed mini` port. Under `weed server` the volume server is 8080 and 18080, as the
  SOUP-036 table says; those are the ports probed here. TASK-172 itself was not edited (approved).
- **AC-9 / SR-028 AC-7, local part:** disposable `docker:dind` (arm64 digest
  `sha256:cb160a57fcb936668f8ab8e4a9d73c66b7975226aa87e466233734edbcd83ccc`, index
  `sha256:9e79b879b177fbd72c34376a3dd3d91747da5db49e1f560f76aea59561471977`; commands in
  Verification), empty image store (`images=0`), no
  cached image of the host reachable. An amd64 `docker:dind` cannot start on this arm64 host
  (iptables under emulation), so the inner daemon is native and the inner client ran with
  `DOCKER_DEFAULT_PLATFORM=linux/amd64` (inner `alpine uname -m` gave `x86_64`). The branch's
  version-controlled files (`git ls-files -co --exclude-standard`, minus `docs/`) plus the
  temporary `.env` and the dev `infra/certs` pair (operator-supplied, gitignored) were streamed in.
  `docker compose -p cr002-fresh build` and `up -d`: both exit 0 (12:48:29 to 12:50:57 UTC). SeaweedFS,
  postgres, redis and nginx were pulled by digest; the other images were built. In the result
  `object-store` healthy (`weed version`: `4.51 … linux amd64`), preflight and `object-store-init`
  Exited (0), `backend`, `reverse-proxy`, `postgres`, `redis`, `frontend`, `celery-worker` Up. The tree sent
  to dind predates the one-line `BotoCoreError` change in `object_store_init.py`; no other
  source file differed. The hosted-runner evidence is TASK-179, the final run TASK-182.
- **AC-4 and AC-6 (re-run on the new server):** AC-4 (every attachment path encrypted at rest)
  as above: the bucket default and a plain put report `AES256`, an explicit put reports `AES256`
  and the plaintext marker is not in `/data`. AC-6 (initialiser): ran in the stack (exit 0,
  bucket private, AES256), and the unit suite for it passes. The TASK-175 negative run was
  repeated against SeaweedFS: project `cr002-neg176`,
  `OBJECT_STORE_ENDPOINT=http://127.0.0.1:1 docker compose up -d backend`: `object-store-init`
  exited 1 ("object-store init failed: object store unreachable: Could not connect to the endpoint
  URL"), Compose reported "service object-store-init didn't complete successfully: exit 1", and
  `backend` was not started. The initialiser started only after `object-store` was Healthy
  (Compose log order in the fresh runs). The policy-present step was not repeated (unit-tested).
- **AC-12 (SOUP-022 part):** SOUP-022 1.3 `obsolete`, approval record cleared, change-log entry
  added; `python3 infra/check_image_pins.py` exit 0.
- **AC-19 (PRB-042 part):** PRB-042 1.2 `resolved` with `## Resolution` (commit by subject,
  commands, fresh-host result). Its Safety evaluation already states that no released version is
  affected and no notification is needed; CR-002 already carries the `resolves` link.

Carry-overs:

1. [MEDIUM] `backend` now has an `environment:` block with `OBJECT_STORE_ENDPOINT`,
   `OBJECT_STORE_BUCKET` and both keys, using the initialiser's exact expressions. The keys use
   the `:?` guard, so an unset key is refused by Compose itself. `celery-worker` does not use the
   store (only the attachment service does) and keeps `env_file`. New test
   `test_backend_and_initialiser_resolve_the_same_store_settings` sets all four in the shell
   (decoy endpoint and bucket) and asserts the initialiser and the backend resolve identical
   values, plus the identical defaults without overrides. Done.
2. [LOW] `object_store_init.initialise` catches `BotoCoreError` after the specific handlers:
   `object-store init failed: object store error: <ClassName>`. Tests for `ConnectionClosedError`
   and `ReadTimeoutError`. The `from` word on the raise line trips `test_no_raw_sql` (PRB-053), so
   the exception is built on its own line. Done.
3. [LOW] TS-014 1.3: TC-014.4-style started-stack environment in the preconditions (own `-p`
   project, fresh volumes, temporary `.env` with `POSTGRES_PASSWORD`), and the `U-OBJ-Init` unit
   acceptance criteria. Done; TS-014 is `in_review`.
4. [LOW] The TASK-172 port 9340 correction is recorded in AC-1 above, where the evidence is
   reused. TASK-172 was not edited.
5. [LOW] SOUP-036 1.1: the misleading start-up log line ("KEK will be stored on the filer in
   plaintext") and the checks that nothing is stored. Re-confirmed here: the filer root lists only
   `/buckets`, and the key value is not in `/data`. Done.
6. ADD-025 1.1 links `relates_to` SOUP-036, which clears `soup_unintegrated`. ADD-012 1.2 drops
   `relates_to` SOUP-022. Done.

Notes and decisions for QA:

- The `object-store` service stays on the `medhub` network; the separate `object-store` network
  is TASK-177's scope.
- `minio_data` is declared in `volumes:` but no service mounts it; Compose omits unused volumes
  from `config`, so the test reads the file.
- The `infra/.env` of the dev machine has `OBJECT_STORE_ENDPOINT=http://minio:9000`. The new
  `${OBJECT_STORE_ENDPOINT:-http://object-store:8333}` expression reads that file, so a developer
  must update the line from `.env.example` (and `DEPLOY.md` still describes `mc`, TASK-180 scope).
  I did not edit the dev file.
- Not run: `traceability-check` (left for QA). Records left `in_review`: this TASK, SOUP-036,
  ADD-025, ADD-012, TS-013 1.5, TS-014 1.3. Not approved by me.
- Defects outside this task: none new. PRB-053 (raw-SQL guard test) was hit again by a harmless
  `from exc`; PRB-038 (no `POSTGRES_PASSWORD` default) needed the usual workaround.

## QA review (2026-10-30): CHANGES REQUESTED

The code, the Compose change and the started-stack behaviour are sound. QA reran everything on the working
tree and reproduced the developer's results. The verdict rests on one records finding: PRB-042's Resolution
is not reproducible as written, and it misstates the platform of the fresh-host evidence.

### Findings

- **[HIGH] PRB-042 Resolution misstates the fresh-host environment, and its fresh-host step cannot be
  repeated.** Location: `docs/problem-reports/PRB-042-minio-community-edition-unmaintained.md`,
  `## Resolution`, the code block and the "Fresh-host evidence" paragraph. The comment says "inside an
  empty amd64 docker:dind". The evidence above says the opposite: an amd64 dind cannot start on this
  host, so the daemon was arm64-native and only the inner client used `DOCKER_DEFAULT_PLATFORM=linux/amd64`.
  The step is a placeholder comment with no dind image digest and no description of how the sources
  reached the daemon. This record's "Verification results" give the dind digests truncated (`cb160a57…3ccc`,
  `9e79b879…1977`). Neither record says that the tree streamed into dind predates the `BotoCoreError` edit.
  The `## Verification` block above also still says "on arm64 run it with --platform linux/amd64", which
  the run showed does not work, and TS-013 TC-013.10 points to that block for its steps.
  Fix:
  1. In PRB-042, describe the environment as it was: an arm64-native `docker:dind` with an empty image store,
     with images pulled and built for linux/amd64 through `DOCKER_DEFAULT_PLATFORM`, and amd64 binaries run
     under emulation.
  2. Give the full dind digest and the exact commands, so a second person can repeat the run:
     `docker run --privileged …`, how the `git ls-files -co --exclude-standard` tree, `.env` and certs were
     streamed in, and `DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose -p cr002-fresh … build` / `up -d`.
  3. State which tree ran: the working tree before the one-line `BotoCoreError` change in
     `backend/app/core/object_store_init.py`.
  4. Replace the dind comment in the `## Verification` block with the same commands.

  On the tree difference itself, QA's judgement is that it is acceptable for AC-9 (local). The edit changes
  exception handling in one Python module only. It changes no image reference, Dockerfile, lock file or base
  image. QA's own started stack built and ran the current tree, and TASK-182 reruns on the branch head.
- **[LOW] SOUP-036 describes the SSE key format as the spike used it, not as the deployment passes it.**
  Location: `docs/soup/SOUP-036-seaweedfs.md`, "Required configuration": "`WEED_S3_SSE_KEY` (64 hex
  characters …)". Compose passes `AT_REST_ENCRYPTION_KEY`, which is base64 of 32 bytes (44 characters).
  SeaweedFS 4.51 accepts any string for `s3.sse.key` and derives the KEK with HKDF-SHA256 (no salt,
  deterministic): upstream `weed/s3api/s3_sse_s3.go` at tag 4.51, lines 300, 441 and 531-552. The hex
  format applies only to `s3.sse.kek`. Fix: state "any string; KEK derived by HKDF-SHA256; MedHub passes
  `AT_REST_ENCRYPTION_KEY` (base64 of 32 bytes)", and cite the source line.
- **[LOW] Optional SOUP-036 note on 18333.** The S3 gRPC port carries only the `SeaweedS3IamCache` RPCs
  (Put/RemoveIdentity, Put/Get/List/DeletePolicy, Put/RemoveGroup). With no filer signing key, every one
  of them accepts only local peers (`checkAdminAuth` → `CheckLocalGrpcPeer`, upstream
  `weed/s3api/s3api_server_grpc.go` lines 25-58 at 4.51). This supports the "Yes, by design until TASK-177"
  row. Fix: add one sentence to the listener table. Not blocking.

### Checked and accepted

- Carry-overs 1-6: the backend `environment:` block uses the initialiser's exact expressions, and the
  started stack's backend env shows `http://object-store:8333` / `medhub`. The `BotoCoreError` handler is
  placed after its subclasses `EndpointConnectionError`/`NoCredentialsError`, so they keep their own
  messages, and its message prints no key. The TS-014 preconditions and the `U-OBJ-Init` criteria are
  present. The 9340 correction is recorded above. The SOUP-036 KEK note is correct: the
  `s3.sse.key` path derives the KEK and stores nothing, the filer root holds only `/buckets` and
  `/etc/` returns 404. ADD-025 links `relates_to` SOUP-036.
- `minio_data` stays declared, and the smoke test checks it. No service mounts it. Nothing in the change
  runs `down -v` or removes a volume. `infra_minio_data` CreatedAt was 2026-06-20T17:29:26Z before and
  after the review.
- SOUP-022 1.3 is `obsolete` with a change-log entry and its approval record cleared, so it is obsolete
  per soup-management. The W6 links from RISK-007/010/011/012 to it are TASK-181's (CR-002 AC-12, "risk
  links"). CR-002 and TASK-176 are the retiring records that AC-12 allows. `soup_without_risk` on SOUP-036
  is also TASK-181's.
- The PRB-042 Safety evaluation is complete: hazard contribution, the justification for `major`, and
  "no release record, no released version affected, no notification". CR-002 at HEAD carries
  `resolves` PRB-042.
- The remaining `minio` text (`infra/DEPLOY.md` §5, comments in `backend/app/core/config.py` and
  `object_storage.py`) is TASK-180's (AC-20). It is not a deployment reference.

### Verification run (QA, 2026-10-30, DOCKER_CONTEXT=desktop-linux, working tree)

- `python3 infra/check_image_pins.py`: exit 0. `python3 -m unittest discover -s infra/tests -v`: 24 OK.
  The `grep` for 9001, console, `minio/minio` and `minio/mc` in the Compose file: no output.
- `cd backend && uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85`: 554 passed,
  91.31 %. `uv run ruff check .`, `uv run black --check .` (as CI runs it) and `uv run mypy app` (126
  files): clean.
- Started stack, own project `qa176`, fresh volumes, temporary `infra/.env` (generated keys, base64
  `AT_REST_ENCRYPTION_KEY`, `POSTGRES_PASSWORD`): `up -d --build` exit 0. The preflight exited 0, then
  `object-store` became Healthy, then `object-store-init` exited 0 ("object-store init ok: bucket medhub
  private, AES256"), then the backend started. The log shows "Derived KEK from s3.sse.key config".
  `bash infra/smoke-test.sh`: **19 passed, 0 failed**.
- AC-4 from `backend` (boto3): the bucket default is `AES256`. A plain put reports `AES256` on `head`,
  and so does an explicit `AES256` put, whose `get` returns the same bytes. The bucket policy check gives
  `NoSuchBucketPolicy`, and a wrong secret gets 403. The plaintext marker is not in `/data` (`grep -rl`
  exit 1). The same grep does find the object key name in the filer log, so the grep works. The key value
  is not in `/data`. After `docker restart`, the object reads back as `AES256` with identical bytes. Test
  objects were deleted (`KeyCount` 0).
- AC-1: `netstat -tln` shows only 8333 and 18333 off loopback. From `backend`, ports 9001, 9000, 9333,
  19333, 8080, 18080, 8888, 18888, 7333, 12535, 8181, 9101, 23646, 33646, 8111, 2022, 7000 and 9327 all
  gave `ConnectionRefusedError`, and 8333 and 18333 were open. From the host, 9001, 9000, 8333, 18333,
  8888, 9333, 8080 and 23646 were refused. `docker port`: empty.
- AC-6 negative: project `qa176neg`, `OBJECT_STORE_ENDPOINT=http://127.0.0.1:1 … up -d backend`. The
  init exited 1 ("object store unreachable"), Compose reported "didn't complete successfully: exit 1",
  and the backend stayed `Created`.
- Image: `docker buildx imagetools inspect` on the index digest lists linux/amd64 `3a522c37…a707` and
  linux/arm64 `7e68a388…1a77`, as SOUP-036 records. The amd64 fresh-daemon run was not repeated (see the
  HIGH finding).
- Clean-up: containers and networks of `qa176` and `qa176neg` removed, volumes `qa176_*` and
  `qa176neg_*` left. The dev `infra/.env` was restored byte-identical (`cmp` OK, sha1 `714c7630…0b64`).
- `traceability-check` (fallback parser) on the eight touched records: 0 errors. Warnings: W6 TASK-176 →
  SOUP-022 (intended), `soup_unintegrated` on obsolete SOUP-022 (parser artefact), `soup_without_risk`
  SOUP-036 (TASK-181). Whole project: 373 records, **0 errors**, W5 18, W6 11, W2 5, W1 3, W7 1, gated
  `soup_without_risk` 1. Every one is expected or pre-existing.

### Pre-existing (not blocking)

- `infra/smoke-test.sh` "Port exposure" runs `grep -A5 "^  ${svc}:"`. For `object-store`, the five lines
  cover only the image and the folded command, so a `ports:` entry lower in the block would pass. The
  infra unit test asserts that `ports` is absent, which covers it. Recommendation: parse
  `docker compose config --format json` instead.
- Dev workstation: `infra/.env` still has `OBJECT_STORE_ENDPOINT=http://minio:9000`. The default `infra`
  stack's initialiser now fails closed until the line is updated from `.env.example`. Attachments in
  `minio_data` cannot be read until TASK-178. Both are as planned. No release exists.

## QA review round 2 (2026-10-30): APPROVED

Round 2 changed records only: PRB-042 1.3, TASK-176 1.2 and SOUP-036 1.2. All three round-1 findings are closed.

- **HIGH, closed.** PRB-042 `## Resolution` now describes the run as it was. The `docker:dind` daemon was
  arm64-native with an empty image store, and only its inner client set `DOCKER_DEFAULT_PLATFORM=linux/amd64`.
  The record gives the full digests and the exact command sequence, and states the tree, which predates
  the `BotoCoreError` edit. QA checked both digests. Local `docker image inspect` shows that
  `docker@sha256:cb160a57…edbcd83ccc` is arm64. `docker buildx imagetools inspect` of the index
  `sha256:9e79b879…561471977` lists `cb160a57…83ccc` as its linux/arm64/v8 entry. It also lists
  `97545b7b…41574f` as linux/amd64, which is why the per-platform digest is the one to run on this host.
  The TASK-176 Verification block uses the same sequence, plus cleanup and an amd64-host variant.
  - QA correction: PRB-042's sequence lacked the TASK's `docker exec cr002-dind mkdir -p /work`, without
    which `tar -C /work` fails. QA copied that one line into PRB-042 from the TASK. It adds the step only
    and changes no result.
- **LOW (SSE key format), closed.** SOUP-036 1.2 now reads "any string, HKDF-SHA256 (unsalted); only
  `s3.sse.kek` is hex". QA checked the cited lines against upstream 4.51 `weed/s3api/s3_sse_s3.go`.
  Line 300 is the `s3.sse.key` "any secret string" comment, line 441 calls `hkdf.New(…, nil, …)`, and
  lines 531-552 are the `s3.sse.key` case and its "Derived KEK" log line.
- **LOW (18333), closed.** The SOUP-036 18333 row cites `s3api_server_grpc.go` lines 25-58. Those lines
  hold `checkAdminAuth` (line 25) and `checkLocalPeer` → `CheckLocalGrpcPeer` (lines 56-58), which matches
  the upstream source.
- `traceability-check` on PRB-042, TASK-176, SOUP-036, TS-013 and TS-014: 0 errors. Two warnings, both
  expected: W6 TASK-176 → SOUP-022, the retiring task (CR-002 AC-12), and `soup_without_risk` on
  SOUP-036, which is TASK-181's. No stack rerun was needed, because code, Compose and stack are unchanged
  since round 1.

TASK-176, TS-013 1.5 and TS-014 1.3 are set `in_review → approved`. ADD-012, ADD-025 and SOUP-036 stay
`in_review` for the human.
