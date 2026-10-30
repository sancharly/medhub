---
id: SOUP-036
type: soup
title: SeaweedFS object store
status: in_review
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-30"
updated: "2026-10-30"
manufacturer: SeaweedFS project (Chris Lu)
soup_version: "4.51"
anomaly_review: "2026-10-30"
links:
  - target: "ADD-025"
    relation: relates_to
tags:
  - soup
  - layer:infrastructure
  - class:B
  - cr:CR-002
---

# SOUP-036 — SeaweedFS object store 4.51

Replaces MinIO ([SOUP-022](SOUP-022-minio.md)) as the self-hosted S3-compatible store
([ADR-0015](../design/adr/0015-object-store-component-after-minio.md), CR-002 D-6). Created by
TASK-172 from a recorded run of the published image. Nothing under `infra/` uses it yet
(TASK-176).

## Identification

| Item | Value |
|---|---|
| Manufacturer | SeaweedFS project (Chris Lu), https://github.com/seaweedfs/seaweedfs |
| Version | 4.51 (`weed version`: `version 30GB 4.51 ffa87c25f`, same on linux/amd64 and linux/arm64) |
| Full image reference | `chrislusf/seaweedfs:4.51@sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8` |
| Digest type | Docker Hub OCI image index (re-resolved 2026-10-30 with `docker buildx imagetools inspect`; equal to the ADR-0015 value). Last pushed 2026-10-26 |
| Platform manifests | linux/amd64 `sha256:3a522c379599e163433a636e75022630848b63a74f08ea37bf06f8d776e9a707`; linux/arm64 `sha256:7e68a388de0806ed8d96f30cb7e927182a3d80d42920cb87d97d23311a7a1a77`; also arm/v7, 386, ppc64le, s390x |
| Licence | Apache-2.0 (GitHub repository licence and `LICENSE`, "Apache License Version 2.0", read 2026-10-30) |
| Provenance | The image is used as published. No MedHub image is built from downloaded binaries (CR-002 AC-10). A cosign signature artifact for the index digest exists on Docker Hub (tag `sha256-f7a49e3f….sig`, 2026-10-26). `cosign` was not installed on the review host, so the signature was not verified (informative only, no AC requires it) |
| Go toolchain | go1.26.10 (string embedded in `/usr/bin/weed`) |
| Used by | `infra/docker-compose.yml`: `object-store` service (TASK-176), described in [ADD-025](../design-outputs/architecture/ADD-025-object-store-deployment.md) |

## Functional and performance requirements

What MedHub relies on (SR-013, SR-022, SR-028, SR-040; ADR-0015 criteria 1 and 5). Each item was
checked on 2026-10-30 against the pinned image with boto3 1.43.117 (the version in
`backend/uv.lock`, SOUP-019) built as `ObjectStorageClient` builds its client. Evidence:
TASK-172, "Evidence".

1. `CreateBucket`.
2. `PutBucketEncryption` with SSE `AES256`, and `GetBucketEncryption` returns `AES256`.
3. `PutObject` with `ServerSideEncryption="AES256"` (the call `ObjectStorageClient.put_object`
   makes), and `HeadObject` reports `ServerSideEncryption: AES256`.
4. `PutObject` with no SSE argument is still stored encrypted (`HeadObject` reports `AES256`)
   once the bucket default is set.
5. `GetObject` returns identical bytes. `DeleteObject` removes the object.
6. `GetBucketPolicy` on a new bucket returns `NoSuchBucketPolicy` (no anonymous policy).
7. A wrong secret key gets HTTP 403.
8. boto3's default request checksums (`when_supported`) are accepted for streamed and
   in-memory bodies.
9. Objects survive a container restart on the same volume and still decrypt. The SSE key is
   required: with a different `WEED_S3_SSE_KEY` on the same volume, `GetObject` fails
   (`InternalError`). Losing the key therefore loses the data.
10. A plaintext marker written in an object is not found in the data directory.
11. Single node, one named volume, one process (master, volume, filer and S3), S3 on port 8333.
12. The start-up check is `wget -q --spider http://127.0.0.1:8333/status` (see TASK-172). A cold
    start accepts signed S3 requests about 2 s after the process starts.

No performance requirement beyond single-attachment `PutObject` and `GetObject` of the sizes
SR-013 allows (a 9 MiB multipart upload was also exercised, informative).

**Not relied on:** the admin UI, WebDAV, SFTP, Iceberg, Lance, S3 IAM management, bucket
policies, versioning, the filer and its HTTP interface, and erasure coding. They are switched
off or bound to loopback (below).

## Required hardware and software environment

- **Image base OS:** Alpine Linux 3.24.3 (`/etc/os-release`, read from the image; identical on
  amd64 and arm64). The upstream Dockerfile's final stage is an unpinned `alpine`
  (`docker/Dockerfile.go_build`, tag 4.51), so the base is whatever Alpine was current when
  upstream built the image. 29 apk packages are installed: busybox 1.37.0, musl 1.2.6, OpenSSL
  libs 3.5.9, curl 8.23.0, c-ares, nghttp2, zlib, zstd, `fuse` 2.9.9 and others.
- **Base OS support (PLAN-002 end-of-support rule), source
  https://alpinelinux.org/releases.json, read 2026-10-30:** Alpine v3.24 `main` repository
  supported until **2028-06-01** (more than 12 months). The `community` repository of v3.24 is
  listed with end date **2026-11-01**. One installed package comes from `community`: `fuse`
  2.9.9 (checked with `apk policy`). MedHub does not mount FUSE in this container. This is
  raised as PRB candidate P-1 (below).
- **Process model:** one container, command `weed server …` (hardened command line below), user
  `seaweed` after the entrypoint, one persistent volume at `/data`. The entrypoint sets
  `GODEBUG=fips140=on`.
- **Listeners** (hardened command line; `netstat -tln` in the container, 2026-10-30):

  | Port | Purpose | Bind | Reachable from the network |
  |---|---|---|---|
  | 8333 | S3 HTTP (the only port the backend uses) | 0.0.0.0 | Yes, by design |
  | 18333 | S3 gRPC (cannot be bound separately: it follows `-s3.ip.bind`) | 0.0.0.0 | Yes. TASK-177 limits it to the `object-store` network |
  | 9333, 19333 | master HTTP, gRPC | 127.0.0.1 | No (connection refused from a peer container) |
  | 8080, 18080 | volume server HTTP, gRPC | 127.0.0.1 | No |
  | 8888, 18888 | filer HTTP, gRPC | 127.0.0.1 | No |

  Admin UI, WebDAV, SFTP, Iceberg (8181), Lance (9101) and metrics do not listen. `weed server`
  has no admin UI and WebDAV and SFTP are off by default. Iceberg and Lance are off with
  `-s3.port.iceberg=0` and `-s3.port.lance=0`.
- **Required configuration (final command line, from TASK-172):**
  `weed server -dir=/data -ip=127.0.0.1 -ip.bind=127.0.0.1 -filer -s3 -s3.ip.bind=0.0.0.0
  -s3.port.iceberg=0 -s3.port.lance=0 -master.volumeSizeLimitMB=1024 -master.telemetry=false`.
  Environment: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (the admin identity, from
  `OBJECT_STORE_ACCESS_KEY` and `OBJECT_STORE_SECRET_KEY`) and `WEED_S3_SSE_KEY` (64 hex
  characters; the log reads "SSE-S3 KeyManager: Derived KEK from s3.sse.key config").
- **Not `weed mini`.** The all-in-one `weed mini` command binds master, volume and filer to
  every interface, and its `-ip.bind` is global, so only `weed server` with `-s3.ip.bind` can
  keep them on loopback. `-master.telemetry=false` is needed because telemetry to
  `telemetry.seaweedfs.com` is on by default.
- **Other SOUP it depends on:** none at run time. The backend side is boto3 (SOUP-019).

## Anomaly list review

**Reviewed 2026-10-30** (TASK-172, CR-002 AC-8, AC-12) by the Software Developer role for the
Software Architect, at `chrislusf/seaweedfs:4.51@sha256:f7a49e3f…134b8` (Go go1.26.10, Alpine
3.24.3). Only published information was read for this review. The contract run is separate and
used a throwaway container.

| Source | URL | What was checked | Result |
|---|---|---|---|
| SeaweedFS GitHub Security Advisories (vendor) | https://github.com/seaweedfs/seaweedfs/security/advisories (API `repos/seaweedfs/seaweedfs/security-advisories`) | All 25 published advisories (2026-06-10 to 2026-09-23), affected range against 4.51 | None names 4.51. The newest affected version is 4.45 (GHSA-q9rj-8p2j-whg4, GHSA-qmx6-fpcw-q3xg, GHSA-5fx4-c9qp-36jc). 9 are critical, 12 high, 4 medium |
| NVD CVE API 2.0 | https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=seaweedfs | Keyword `seaweedfs`, 14 results | None affects 4.51: the CVEs are for versions up to 4.41 and CVE-2024-40120 for v3.68. Several are still "Deferred" in NVD |
| OSV, Go module | https://api.osv.dev/v1/query (`github.com/seaweedfs/seaweedfs`, ecosystem Go) | All 14 entries compared with 4.51 | None affects 4.51. They are the same advisories fixed up to 4.34, plus CVE-2024-40120 (fixed 2024). OSV cannot match a tag such as `4.51.0` (the module uses pseudo-versions), so a query with the version returns nothing and the full list was read |
| OSV, Go standard library | https://api.osv.dev/v1/query (`stdlib`, version 1.26.10) | The toolchain `weed` was built with | 0 entries |
| OSV, base-OS packages | https://api.osv.dev/v1/querybatch (ecosystem `Alpine:v3.24`, the 29 packages and versions from `apk info -v`) | Every installed package | 0 entries. Control: `busybox 1.36.1-r0` in `Alpine:v3.20` returns 7 entries, so the query path works. OSV coverage for v3.24 itself is not verified |
| Alpine release data (base-OS support) | https://alpinelinux.org/releases.json | End dates of v3.24 | `main` 2028-06-01, `community` 2026-11-01 (see above) |
| SeaweedFS open issues mentioning SSE or HeadObject | https://github.com/seaweedfs/seaweedfs/issues (search, 7 open results) | Open reports touching encryption, `HeadObject` or integrity | See "Open issue reviewed" |

Advisory limits that apply to this review: the GitHub API leaves `patched_versions` empty for
most advisories, so "fixed" is read as "4.51 is outside the stated affected range". The ranges are the maintainers' own.
The fix release is named only for some (4.24, 4.30, 4.34, 4.40). The 2026 advisory rate is high: 25 in about 3.5
months, 9 critical. That is why the monitoring below is monthly.

**Advisories by affected range** (all fixed before 4.51 by their stated range):

| Newest affected version | Advisories (GHSA) and subject |
|---|---|
| 4.45 | q9rj-8p2j-whg4 (SFTP empty password), qmx6-fpcw-q3xg (bucket policy not enforced on POST Object), 5fx4-c9qp-36jc (S3 gateway gRPC `PutIdentity` and `RemoveIdentity` unauthenticated) |
| 4.44 | jcgp-4284-p6g2 (Lance path traversal) |
| 4.42 | 3j72-rgq3-c2j7 (inline GCS credentials SSRF), 3883-fr8h-xrqg (ArangoDB AQL injection), vwwx-w898-9f4r (SFTP chroot escape) |
| 4.41 | cprc-whx4-v3f5, 939f-xh28-2q48, fjm8-2g3v-ffjw (SSRF family), 39jr-32mg-hjwj (volume server missing authorization, Rust volume server) |
| 4.40 | jw56-gm6j-34mp (standalone `weed iam`), hqp5-j79g-vr89 (SFTP Helm host key) |
| 4.39 | 9x53-cjpr-m682 (PutObjectAcl scope), fvpg-g364-j8vh (SFTP path ACL), 757h-cm9x-wprg (S3 OIDC bearer), 99q7-x53r-6j4g (filer TUS cross-prefix) |
| 4.34 or older | gv5w-hfx8-8cwq, 2v6v-25fm-p4fg (filer IAM gRPC unauthenticated), 87fv-vqqr-m4jr (FetchAndWriteNeedle SSRF), 56wq-x3wv-3ff4, hgpf-8634-g44c, w62w-66v9-vvgv, 7fw3-5g74-c7p9, h249-8wvq-pc5v |

**Hazard-relevant for MedHub's configuration (§7.1.3).** No advisory in the lists above affects
4.51. The advisory classes are nevertheless the reason for the configuration findings below,
because they are the same class as the four MinIO CVEs of PRB-043 (unauthenticated writes to
the store, identity injection, SSRF):

| # | Finding | Evidence | Disposition |
|---|---|---|---|
| F-1 | In the all-in-one `weed mini` command, the filer (8888), master (9333) and volume server (9340) answer **unauthenticated** HTTP from any peer on the network. A `PUT` to the filer with no credentials planted an object that S3 then served; `HeadObject` reported no encryption for it. A `GET` through the filer returned ciphertext for an SSE object, so SSE itself held. This is a bypass of S3 authentication and of the encryption control | Run on 2026-10-30: `PUT http://<store>:8888/buckets/<bucket>/planted.txt` → 201; S3 `GetObject` returned the bytes; `ServerSideEncryption` absent | Avoided by design: `weed server` with `-ip.bind=127.0.0.1` and `-s3.ip.bind=0.0.0.0`. The same probes from a peer container are refused (9333, 9340, 8888). Input to TASK-176 (command), TASK-177 (network), TASK-173 (checksum on download detects a substituted object) and TASK-181 (RISK-012). The filer log warning "IAM gRPC service on filer is UNAUTHENTICATED" (seen in `weed mini` mode) is on a loopback listener in the hardened mode |
| F-2 | The S3 gRPC port (18333) stays on the non-loopback address. GHSA-5fx4-c9qp-36jc (≤ 4.45) shows that this service once accepted unauthenticated identity changes. 4.51 is outside the range; the fix was not exercised (no exploit test was run) | `netstat`; advisory text | TASK-177 limits reach to the backend and the initialiser. TASK-181 states it in RISK-012 as a residual reason |
| F-3 | Telemetry to `telemetry.seaweedfs.com` is on by default (`-master.telemetry`) | `weed mini -h` and `weed server -h` | Switched off in the command line. A start-up check that the flag is present belongs in TASK-176 |
| F-4 | The SSE key is the only key: a different `WEED_S3_SSE_KEY` on the same volume makes existing objects unreadable (`InternalError`) | Run on 2026-10-30 | Information for DEPLOY.md and the key-handling question Q-7 (PRB-007). No SOUP defect |
| F-5 | In `weed mini` mode, the admin server keeps listening on 127.0.0.1 (12535, 22535, 23646, 33646) although `-admin.ui=false`, and a `.mini_kek_passphrase` file is written to the data volume. Neither occurs under `weed server` | `netstat` and `ls /data` in both modes | Supports the choice of `weed server`. No action |

**Base OS.** Alpine v3.24.3 packages: 0 entries in OSV (above). One package (`fuse` 2.9.9) is
in the `community` repository, whose support ends 2026-11-01. It is not exercised by MedHub.
PRB candidate P-1 (minor). Upstream rebuilds the image on a newer Alpine with each release, so
the remedy is the reviewed digest change of the monitoring rule below.

**Open issue reviewed.** seaweedfs/seaweedfs#8908 (open, created 2026-04-03, reported against
4.18): the S3 API returns success for a blob-finalise copy (Docker Registry, 205 MB layer) that
later reads back with a different SHA-256. MedHub uses single `PutObject` and does not use
`CopyObject` or multipart finalisation for attachments, and TASK-173 verifies the stored
checksum on every download. Not hazard-relevant for this use; kept on the watch list. The
other open results (#12235, #8371, #7506, #6361, #4758, #3984) do not concern SSE or integrity
of the paths MedHub uses.

**Support policy (PLAN-002).** The manufacturer publishes no end-of-life date and no maintained
release line. Releases are rolling: 4.47 (2026-09-14), 4.48 (2026-09-28), 4.49 (2026-10-23),
4.50 and 4.51 (2026-10-25). Fixes ship only in the latest release. No newer release than 4.51
existed on 2026-10-30. Per PLAN-002 an item without a published end date is checked for whether its line has
stopped receiving fixes: it has not (repository not archived, last push 2026-10-30). The
pinned release is acceptable while it is no more than one review interval behind a release that
fixes a hazard-relevant advisory (ADR-0015, "Negative"; PLAN-002 1.2).

**Escalated under CR-002 (TASK-172):** no hazard-relevant anomaly in 4.51, so no new RISK.
F-1..F-5 are inputs to RISK-012 (TASK-181) and to TASK-176/177. One defect candidate, P-1,
is listed in CR-002 "Escalations" for the human's decision.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md) 1.2 (proposed, `in_review`): this item has
rolling releases and nine critical advisories in 2026, so it is checked **monthly**, not only at
every dependency change and yearly. Each month the Software Architect role re-reads the sources
in the table above (GitHub advisories, NVD, OSV for the Go module, `stdlib` and the Alpine
packages, Alpine release data) and updates `anomaly_review`. A fix for a hazard-relevant
advisory is adopted by a reviewed change of the pinned digest, with this change log updated,
no later than the next monthly check. Hazard-relevant anomalies go to `risk-management`;
defects affecting MedHub become PRBs. Next check due: 2026-11-30. The maximum review age in
`docs/medtrace.yml` (365 days) is not changed, so the monthly cadence is a process rule and not
a tool check.

## Change log

- 2026-10-30 — Version 1.0: record created at 4.51 (`sha256:f7a49e3f…134b8`), replacing
  MinIO SOUP-022 under CR-002 / ADR-0015 (TASK-172). First anomaly-list review. Contract
  confirmed against the published image. Pinned in `infra/` by TASK-176.
