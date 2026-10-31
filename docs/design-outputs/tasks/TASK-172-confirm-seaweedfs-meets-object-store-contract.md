---
id: "TASK-172"
type: task
title: "Confirm SeaweedFS meets the object-store contract and review its anomaly list"
status: approved
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
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-002"
    relation: relates_to
  - target: "PRB-042"
    relation: relates_to
  - target: "PLAN-002"
    relation: relates_to
  - target: "SOUP-036"
    relation: relates_to
tags: ["soup", "object-store", "spike", "cr:CR-002", "issue:sancharly/medhub#33", "control:design", "control:protective"]
---

# TASK-172 — Confirm SeaweedFS meets the object-store contract and review its anomaly list

- **Software item / unit:** SI-OBJSTORE `U-OBJ-Server` (ADD-025), SOUP (new SOUP-036)
- **Depends on:** the human's answer to CR-002 Q-1 and ADR-0015 moved to `Accepted`. This is the
  gate task: no task that changes the object-store server (TASK-176..179) starts before its
  go/no-go result.
- **Branch:** `bug/minio-object-store`
- **Size:** M (1 new SOUP record, PLAN-002 revision, ADR evidence note; no product code)
- **Needs:** a Docker host and network access (Docker Hub, GitHub API, OSV, NVD)
- **Under another Q-1 answer:** (a) AIStor: same steps against `quay.io/minio/aistor/minio` with a
  licence file, after the human has accepted the licence. SOUP-036 is "MinIO AIStor". (c) Interim:
  this task becomes the binary-verification design (minisign key source, pinned base image).

## Objective

Before MedHub depends on it, prove with the real image that SeaweedFS does what ADR-0015 claims,
and give it a SOUP record with a dated, sourced anomaly review. This is the evidence for CR-002
AC-8 and for the "replace" control of RISK-012. It re-implements RISK-010's review control for the
new item.

## Interfaces to honor

- The contract is what `ObjectStorageClient` and the planned initialiser call, with boto3
  1.43.117 from `backend/uv.lock`. Do not change the client.
- Scratch work only: a throwaway container and network, and a script in the scratchpad. Nothing
  under `infra/` changes in this task.
- Test credentials and keys are generated for the run and never recorded.

## Implementation detail

1. **Image.** Re-resolve `docker buildx imagetools inspect chrislusf/seaweedfs:4.51`. The ADR
   value is `sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8`. If a newer
   4.x release exists, choose it only if its review is clean, and say so.
   - Record the index digest, the platforms (amd64, arm64 at least) and the `weed version`
     output.
   - Record the base OS from `/etc/os-release` (the upstream Dockerfile's final stage is an
     unpinned `alpine`, so read it from the image).
   - Record the result of `cosign verify` if cosign is available. That is informative only: no
     AC requires it.
   - Pull both platforms on a daemon or builder with no cached copy.
2. **Contract run.** Start the server in its all-in-one mode with one data directory.
   - Credentials go in as the admin identity through environment variables, and the SSE key
     through `WEED_S3_SSE_KEY`.
   - With a scratch Python script on boto3 1.43.117 (`cd backend && uv run python <script>`),
     check:
     - `create_bucket`;
     - `put_bucket_encryption` with SSE `AES256`, then `get_bucket_encryption` returns it;
     - `put_object` with `ServerSideEncryption="AES256"`, then `head_object` reports `AES256`;
     - `put_object` with no SSE argument, then `head_object` reports `AES256` (bucket default);
     - `get_object` returns identical bytes;
     - `get_bucket_policy` returns `NoSuchBucketPolicy`;
     - `delete_object` works;
     - a wrong secret key gets `403`;
     - boto3's default request checksums are accepted.
   - Then restart the container and check that the objects still decrypt.
   - Search the data directory for a plaintext marker written in an object. It must not be found.
3. **Listeners.** Switch off the admin UI, WebDAV, SFTP, Iceberg, Lance and metrics (see the
   `weed` flags, for example `-admin.ui=false`, `-webdav=false`, `-s3.port.iceberg=0`,
   `-s3.port.lance=0`).
   - List every listening port inside the container.
   - Bind every non-S3 listener to loopback where a flag allows it.
   - Record the final command line and the remaining listeners with their purpose. That is the
     input for TASK-176 and TASK-177 (AC-1).
4. **Healthcheck.** Find a command that uses a tool present in the image (for example
   `wget -q --spider http://127.0.0.1:<s3 port>/status` or the S3 health endpoint) and that
   succeeds only once S3 accepts requests. Record it.
5. **SOUP-036** (new, `in_review`). Follow `soup-management`:
   - manufacturer: the SeaweedFS project (Chris Lu); exact version; the full reference with
     digest;
   - functional and performance requirements: the contract list in step 2;
   - environment: the base OS and its support status, single node, one volume;
   - anomaly review, with each source named and its URL:
     - GitHub Security Advisories for `seaweedfs/seaweedfs` (all 2026 entries, against 4.51);
     - NVD keyword `seaweedfs`;
     - OSV (Go module `github.com/seaweedfs/seaweedfs`, and the Go standard library at the
       version `weed version` reports);
     - OSV for the base-OS packages.
   - Set `anomaly_review` to the review date.
   - Support policy: no published end-of-life, rolling releases, fixes in the latest release
     only. Record this as PLAN-002 requires.
   - Monitoring: a monthly advisory check (step 6).
   - Hazard-relevant findings become RISK records and defects become PRBs. List them under
     CR-002 "Escalations".
6. **PLAN-002.** Revise to the next version (`in_review`). Add a rule to "SOUP monitoring": an
   item that has rolling releases and a recent critical advisory is checked monthly, and a
   hazard-relevant fix is adopted by a reviewed digest change within that interval. Name
   SOUP-036 as the current such item.
7. **Go/no-go.** Add a short "Spike result (TASK-172)" paragraph to ADR-0015 with the date and the
   outcome. If any contract item in steps 2–4 fails, stop. Report to the human with ADR-0015's
   option (a) or (c), and do not start TASK-176.

## Acceptance criteria

- [x] CR-002 **AC-8** (evidence): SSE-S3 support, image availability and the digest are
      confirmed by a recorded run. The licence is confirmed as Apache-2.0 from the repository.
- [x] CR-002 **AC-10**: ADR-0015 states that no image is built from downloaded binaries, and the
      spike confirms that the image is used as published.
- [x] CR-002 **AC-12** (SOUP-036 part): the record exists with an exact version, a dated and
      sourced anomaly review, relied-on requirements and an environment section.

## Verification

Scratch script output (every contract check, with its result), the listener list, the healthcheck
result, `docker buildx imagetools inspect` output, and the SOUP-036 review. Then
`traceability-check` for SOUP-036, PLAN-002 and this task.

## Definition of Done

- [x] Every contract check passes, or the no-go is reported to the human.
- [x] SOUP-036 and PLAN-002 are `in_review`. ADR-0015 carries the spike result.
- [x] `traceability-check` shows no error for the touched records.

## Evidence

Run on 2026-10-30 by the Software Developer role, on Docker Desktop 24.0.5 (context
`desktop-linux`, arm64 host). The daemon held no SeaweedFS image before the run. Result:
**GO**. Every contract item passed, on both configurations tried. AC-8, AC-10 and AC-12
(SOUP-036 part) are met by the records named below; the checkboxes are left for QA.

**Scratch files (not in the repository):**
`/private/tmp/claude-501/-Users-carlos-santiago-Dev-prototypes-medhub-01/332f5855-c49e-4d4e-a2c1-f7835ae95272/scratchpad/`
holds `spike172.py` (modes `run`, `delete`, `after-restart`), `ready.py` and the saved outputs
`run1.txt` (mini), `run4-hard.txt` (hardened), `run5-restart-hard.txt`, `ready.txt`,
`ready-cold.txt`, `ghsa.json`, `nvd.json`. `spike.env` holds the generated test credentials and
SSE key; it is never recorded. Two scratch volumes `spike172-data` and `spike172-data2`
were left in place (no volume was removed on this machine); containers and network were
removed.

### 1. Image

`docker buildx imagetools inspect chrislusf/seaweedfs:4.51`:

- Index digest `sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8`,
  **equal to ADR-0015**. Docker Hub tag list: 4.51 (pushed 2026-10-26) is the newest release;
  GitHub releases: 4.51 (2026-10-25), 4.50, 4.49, 4.48, 4.47. No newer 4.x exists.
- Platforms: linux/amd64 `sha256:3a522c37…a707`, linux/arm64 `sha256:7e68a388…1a77`,
  ppc64le, 386, arm/v7 (each with an attestation manifest).
- Both platforms pulled by platform digest and run (amd64 under emulation on the arm64 host):
  `weed version` → `version 30GB 4.51 ffa87c25f linux arm64` and `… linux amd64`.
- `/etc/os-release` on both: Alpine Linux 3.24.3 (`PRETTY_NAME="Alpine Linux v3.24"`).
  Go toolchain go1.26.10 (embedded string). 29 apk packages.
- `cosign verify`: `cosign` is not installed on this host, not run (informative). A signature
  artifact tag for the index digest exists on Docker Hub (`sha256-f7a49e3f….sig`).
- Licence: GitHub reports `Apache-2.0`; `LICENSE` is "Apache License Version 2.0".
- Image used as published; no binary download or image build (AC-10).

### 2. Contract run (boto3 1.43.117 via `cd backend && uv run python spike172.py run`)

Client built as `ObjectStorageClient` builds it (`boto3.client("s3", endpoint_url=…, keys)`,
default `Config`: `request_checksum_calculation=when_supported`,
`response_checksum_validation=when_supported`). Output of the hardened configuration
(`run4-hard.txt`); the `weed mini` configuration gave the identical nine PASS lines (`run1.txt`):

```
PASS  create_bucket: 200
PASS  put/get_bucket_encryption AES256: AES256
PASS  put_object explicit SSE AES256 + head_object: put status=200 put-resp SSE=AES256 head SSE=AES256
PASS  put_object no SSE arg -> bucket default + head_object: head SSE=AES256
PASS  get_object identical bytes: bytes identical for both objects
PASS  get_bucket_policy -> NoSuchBucketPolicy: NoSuchBucketPolicy
PASS  wrong secret key -> 403: 403 403
PASS  boto3 default request checksums accepted: ... put(BytesIO)=200 put(bytes)=200 get=200 resp-checksum=K8PRBg==
PASS  multipart upload_fileobj (informative): 9 MiB multipart upload, identical, SSE AES256 (informative)
SUMMARY mode=run pass=9 fail=0
PASS  delete_object: delete status=204; head afterwards 404
```

- **Restart** (`docker restart`, same volume): `spike172.py after-restart` → both objects decrypt
  to identical bytes, `HeadObject` still `AES256`, `GetBucketEncryption` still `AES256`, in both
  configurations (`run3-restart.txt`, `run5-restart-hard.txt`).
- **Plaintext marker:** `grep -rl PLAINTEXT-MARKER-TASK172 /data` in the container: not found
  (exit 1) before and after restart, in both configurations. **Control:** a second container
  with no SSE key and no bucket default, same marker, same grep: found in `ctl_1.dat`, so the
  search method detects plaintext (control container removed).
- **Key is in force:** the same volume started with a different `WEED_S3_SSE_KEY` → `GetObject`
  fails with `InternalError`. The log says "SSE-S3 KeyManager: Derived KEK from s3.sse.key config".
- **Readiness:** from container start to the first success, signed S3 request 1.7 s / 2.4 s
  (restart / cold start), `/status` 2.0 s / 2.7 s, `/healthz` 2.1 s / 2.7 s.

### 3. Listeners and the command line

`weed mini` with the TASK flags (`-admin.ui=false -webdav=false -s3.port.iceberg=0
-s3.port.lance=0`, plus `-master.telemetry=false`): master 9333/19333, volume 9340/19340, filer
8888/18888 and S3 8333/18333 all on `:::`; the admin server still on 127.0.0.1 12535, 22535,
23646, 33646; `-ip.bind` is global in `mini`, so master, volume and filer cannot be moved to
loopback without moving S3. From a peer container with no credentials: `GET :9333/cluster/status`,
`:9340/status`, `:8888/buckets/…` → 200 (WebDAV 7333, admin 12535, Iceberg 8181 refused). A
`PUT :8888/buckets/<bucket>/planted.txt` → **201** and S3 `GetObject` returned the planted bytes
with no `ServerSideEncryption`. Filer `GET` of an SSE object returned ciphertext. So `mini` is
**not acceptable** (SOUP-036 F-1).

**Final command (works, all contract items pass):**

```
weed server -dir=/data -ip=127.0.0.1 -ip.bind=127.0.0.1 -filer -s3 -s3.ip.bind=0.0.0.0 \
  -s3.port.iceberg=0 -s3.port.lance=0 -master.volumeSizeLimitMB=1024 -master.telemetry=false
```

environment `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (admin identity) and `WEED_S3_SSE_KEY`
(64 hex characters), one named volume at `/data`, image entrypoint `/entrypoint.sh`.

| Port | Purpose | Bind |
|---|---|---|
| 8333 | S3 HTTP | 0.0.0.0 |
| 18333 | S3 gRPC (follows `-s3.ip.bind`; no flag binds it separately) | 0.0.0.0 |
| 9333 / 19333 | master HTTP / gRPC | 127.0.0.1 |
| 8080 / 18080 | volume HTTP / gRPC | 127.0.0.1 |
| 8888 / 18888 | filer HTTP / gRPC | 127.0.0.1 |

From a peer container the same probes now: 9333, 9340 and 8888 → connection refused; 8333
`/status` → 200; 18333 resets plain HTTP. Admin UI, WebDAV, SFTP, Iceberg, Lance and metrics do
not listen. No stray key file (`.mini_kek_passphrase`, written by `mini`) is in the `/data` of
the `weed server` run. Inputs for TASK-176 (command, `--ip` is the loopback address because
the process is single-node) and TASK-177 (only 8333 and 18333 need the `object-store` network).

### 4. Health check

`wget -q --spider http://127.0.0.1:8333/status` (busybox `wget` is in the image). It exits 0
with S3 up and 1 ("Connection refused") with nothing listening (checked on a wrong port); the
signed request succeeded no later than `/status` in both start-up timings above. `curl` is also
in the image. Compose form: `test: ["CMD", "wget", "-q", "--spider", "http://127.0.0.1:8333/status"]`.
Plain `GET /` returns 403, so it is not a usable probe.

### 5. SOUP-036, PLAN-002, ADR-0015

- [SOUP-036](../../soup/SOUP-036-seaweedfs.md) created, `in_review`: exact version 4.51 and full
  reference with digest; relied-on requirements; environment (Alpine 3.24.3, single node, one
  volume, listeners); anomaly review dated 2026-10-30 against GitHub advisories (25, none naming
  4.51; newest affected 4.45), NVD (14, none), OSV Go module (14, none), OSV `stdlib` 1.26.10
  (0), OSV Alpine v3.24 packages (29 queried, 0; control query with a known-vulnerable older
  version returned 7); support policy; monthly monitoring.
- [PLAN-002](../../plans/PLAN-002-maintenance-plan.md) revised to 1.2, `in_review`, approval
  record cleared: "Items with rolling releases" rule, SOUP-036 named.
- [ADR-0015](../../design/adr/0015-object-store-component-after-minio.md): "Spike result
  (TASK-172)" added, dated 2026-10-30, outcome go, with the `weed mini` to `weed server` change.
- [CR-002](../../change-requests/CR-002-secure-or-replace-the-minio-object-store.md) 1.3:
  "Escalations" updated (no new RISK; findings F-1..F-5 as inputs; PRB candidate P-1).

### Rerun for QA

```
export DOCKER_CONTEXT=desktop-linux
D=chrislusf/seaweedfs@sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8
docker network create qa-net; docker volume create qa-data
# env file with generated AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, WEED_S3_SSE_KEY=$(openssl rand -hex 32)
docker run -d --name qa-seaweed --network qa-net -p 127.0.0.1:18335:8333 --env-file qa.env \
  -v qa-data:/data $D server -dir=/data -ip=127.0.0.1 -ip.bind=127.0.0.1 -filer -s3 \
  -s3.ip.bind=0.0.0.0 -s3.port.iceberg=0 -s3.port.lance=0 -master.volumeSizeLimitMB=1024 \
  -master.telemetry=false
cd backend && set -a && . qa.env && set +a && SPIKE_ENDPOINT=http://127.0.0.1:18335 \
  uv run python <scratchpad>/spike172.py run      # then: delete, docker restart, after-restart
docker exec qa-seaweed sh -c 'netstat -tln; grep -rl PLAINTEXT-MARKER-TASK172 /data'
```

Remove only `qa-seaweed`, `qa-net` and `qa-data` afterwards.

### Defects and findings outside this task

None fixed. PRB candidate **P-1** (minor): `fuse` 2.9.9 in the pinned image comes from Alpine
v3.24 `community`, support ending 2026-11-01. See CR-002 "Escalations". Not related to this
task's code: `docs/medtrace.yml` `soup_anomaly_max_age_days` (365) cannot enforce PLAN-002 1.2's
monthly cadence; that is a process rule only.

## QA review (2026-10-30)

**Verdict: APPROVED** (`in_review → approved`). QA ticked AC-8 (evidence), AC-10, AC-12
(SOUP-036 part) and the three Definition of Done items. There is no CRITICAL or HIGH finding.

**Rerun by QA** (Docker Desktop 24.0.5, arm64, context `desktop-linux`; QA's own container,
network and volume, removed afterwards; credentials and SSE key generated for the run and
deleted):

- `docker buildx imagetools inspect chrislusf/seaweedfs:4.51` → index
  `sha256:f7a49e3f…134b8`, amd64 `sha256:3a522c37…a707`, arm64 `sha256:7e68a388…1a77`, plus
  386, arm/v7, ppc64le and s390x. Equal to ADR-0015 and SOUP-036. GitHub releases: 4.51
  (2026-10-25) is the newest. Repository licence `Apache-2.0`, not archived.
- The final `weed server …` command of §3, run by index digest. `wget -q --spider
  http://127.0.0.1:8333/status` succeeded about 4 s after start (refused before).
- `spike172.py run` with boto3 1.43.117: 9 PASS, 0 FAIL. Both `head_object` checks report
  `AES256` (explicit SSE and bucket default). `delete`: 204, then 404. Anonymous `GET` and
  `PUT` on S3: 403.
- `netstat -tln`: only 8333 and 18333 on `:::`; 8080, 18080, 8888, 18888, 9333, 19333 on
  127.0.0.1. From a peer container on the same network, 9333, 19333, 8080, 18080, 8888, 18888
  (and 9340, 7333, 12535, 8181, 9101, 9327, 2022) are refused. The filer `PUT` that planted an
  object under `weed mini` is refused. 8333 `/status` gives 200.
- `grep -rl PLAINTEXT-MARKER-TASK172 /data`: not found, before and after `docker restart`.
  `after-restart`: both objects decrypt, `HeadObject` and `GetBucketEncryption` still `AES256`.
- The same volume with a different `WEED_S3_SSE_KEY`: `GetObject` → `InternalError`. The key
  is in force.
- Spot-checks of the review: GitHub advisories (25 in total: 9 critical, 12 high, 4 medium;
  newest ranges `<= 4.45`), the latest releases, and Alpine `releases.json` (v3.24 `main`
  2028-06-01, `community` 2026-11-01). All match SOUP-036.
- `traceability-check` (QA's fallback parser, E1–E8, W5/W6, class B SOUP rules) over TASK-172,
  SOUP-036, PLAN-002, CR-002, ADD-025, RISK-010, RISK-012, SR-022, SR-028 and PRB-042 gives
  **0 errors**. Warnings:
  - SOUP-036 `soup_unintegrated`. It has an outbound `relates_to` ADD-025, and the ADD side is
    TASK-176's DoD.
  - SOUP-036 `soup_without_risk`. TASK-181 moves RISK-012's links.

  Both are expected at this point of the plan. TASK-182 has to see them cleared. The other two
  warnings, RISK-010 and SR-022 W5 → RISK-012 `in_review`, already existed before this task.

**Findings (not blocking):**

- **[MEDIUM] P-1 left as a candidate although PLAN-002 1.1 makes the PRB a step.** In
  `docs/plans/PLAN-002-maintenance-plan.md`, under "On a shortfall", step 1 reads "Raise a
  problem report". `fuse` 2.9.9 (Alpine v3.24 `community`, support ends 2026-11-01) is a
  shortfall unless the rule's "base OS release" is read as the `main` repository only. Fix:
  either raise the PRB (minor, remedy is the digest change of TASK-176 or the monthly rule), or
  have the human record in CR-002 "Escalations" that a `community` package end date is not a
  base-OS shortfall under PLAN-002. Decide this before 2026-11-01 or at the latest at TASK-181.
- **[LOW] Peer-probe evidence names a port that does not exist in the final mode.** §3 says that
  under the final command "9333, 9340 and 8888 → connection refused". 9340 is the `weed mini`
  volume port, and under `weed server` the volume server is on 8080/18080, so that probe proved
  nothing. QA's rerun above covers 8080, 18080, 19333 and 18888, so the result holds. Fix:
  correct the sentence when TASK-176 reuses this evidence.
- **[LOW] ADR-0015 "Negative" still describes the pre-spike port exposure.** In
  `docs/design/adr/0015-object-store-component-after-minio.md`, the bullet "Internal ports of
  the all-in-one server" says master, volume and filer "listen … on the `object-store`
  network". After the spike they are loopback-only, and only S3 HTTP/gRPC (8333/18333) are
  reachable. Fix: amend the bullet to point to "Spike result (TASK-172)" in TASK-180 (ADR/arc42
  update). The "Decision (recommended, pending …)" heading has the same staleness relative to
  the `Accepted` status.
- **[LOW] The SSE KeyManager start-up warning is not recorded.** At every start, `weed server`
  logs "neither s3.sse.kek.passphrase nor WEED_S3_SSE_KEK_PASSPHRASE is set; the KEK will be
  stored on the filer in plaintext", and then "Derived KEK from s3.sse.key config". QA checked
  the stored state: the filer has no `/etc` entry (root lists only `/buckets`), and the key's
  hex is not in `/data`. Nothing is stored. Fix: note this in SOUP-036's environment section
  (TASK-176 can do it with the deployment), so that the warning is not misread and no
  `WEED_S3_SSE_KEK_PASSPHRASE` is added without need.

**Pre-existing (not this task):** CR-002 is still `open` although the Plan gate passed and work
has started. The `open → in_progress` transition is the orchestrator's.
