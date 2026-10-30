---
id: SOUP-022
type: soup
title: MinIO object storage
status: obsolete
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-30"
manufacturer: MinIO, Inc.
soup_version: RELEASE.2025-09-07T16-13-09Z
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:infrastructure
  - class:B
---

# SOUP-022 — MinIO object storage RELEASE.2025-09-07T16-13-09Z

## Functional and performance requirements

S3-compatible object storage for attachments with server-side encryption (SR-013, SR-022).

## Required hardware and software environment

`minio/minio:RELEASE.2025-09-07T16-13-09Z` container image (Go 1.24.6, linux/arm64 as cached; base OS Red Hat Enterprise Linux 9.6, UBI 9 micro, A-5) with a persistent volume.

| Full image reference | Used by |
|---|---|
| `minio/minio:RELEASE.2025-09-07T16-13-09Z@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e` | `infra/docker-compose.yml`: `minio` service |

The registry refused this repository on 2026-10-22 (Docker Hub "pull access denied", `quay.io/minio/*` 401), so the digest could not be checked against a registry. It is the `RepoDigest` of the locally cached image (`docker image inspect --format '{{json .RepoDigests}}'`), the release from `minio --version` inside it. The cached image is arm64 only. The release is `RELEASE.2025-09-07T16-13-09Z` (image created 2025-09-07). `docker compose pull` cannot obtain it and a fresh or amd64 host cannot build the stack; CR-001 AC-5 (build, start and smoke test of the pinned stack) is therefore reproducible only on a host that holds the cached image. The distribution status is confirmed or refuted by TASK-154 (CR-001 D-4); the component is not changed here.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11, AC-12, D-4) by the Software Architect role, at
the pinned version `minio/minio:RELEASE.2025-09-07T16-13-09Z@sha256:14cea493…936e` (Go 1.24.6;
base OS Red Hat Enterprise Linux 9.6, UBI 9 micro).

Sources checked:

| Source | URL | What was checked |
|---|---|---|
| MinIO GitHub Security Advisories (vendor) | https://github.com/minio/minio/security/advisories | Every advisory published since 2025-01-01, with its affected range and "Fixed in" release |
| GitHub Advisory Database, Go ecosystem | https://github.com/advisories?query=ecosystem%3Ago+github.com%2Fminio%2Fminio | Same set, to catch advisories not filed in the repository |
| MinIO README and its history (vendor notice) | https://github.com/minio/minio/blob/master/README.md, https://github.com/minio/minio/commits/master/README.md | Distribution and maintenance notices, dated by commit |
| MinIO releases (vendor) | https://github.com/minio/minio/releases | Last release with binaries; assets of the pinned release |
| MinIO download site (vendor notice) | https://dl.min.io/server/minio/release/linux-amd64/ | Distribution notice (HTTP 410) |
| Docker Hub and quay.io registry APIs | https://hub.docker.com/v2/repositories/minio/minio/, https://quay.io/api/v1/repository/minio/minio | Whether the image repository still exists |
| NVD CVE API 2.0 | https://services.nvd.nist.gov/rest/json/cves/2.0 | Keyword `minio`, published 2026-07-01..2026-10-22 (32 results, filtered to the MinIO server) |
| OSV (Go, `stdlib`) | https://api.osv.dev/v1/query | Go standard library 1.24.6, the toolchain the binary was built with |

Method for the base OS: the image's RPM database lists 22 packages (`glibc`, `bash`,
`coreutils-single`, `pcre2`, `ncurses`, `tzdata` and their dependencies; no OpenSSL, because the
Go binary carries its own TLS stack). Package versions were not decoded or checked one by one
against Red Hat errata: no RPM tool or image scanner was available (`docker scout cves`, CLI
0.20.0, crashed). The image was built on 2025-09-07 and will not be rebuilt (see D-4 below), so its
base OS has had no update for 13 months. It must be assumed to carry every RHEL 9 fix published
since then as an open anomaly. **This gap is explicit: base-OS packages of this image were not
reviewed individually.**

### Distribution status (CR-001 D-4): confirmed

From MinIO's own notices:

1. **2025-10-15**, README commit `9e49d5e7a6` ("point to source only releases"): the community
   edition is distributed as source code only. MinIO publishes no more pre-compiled community
   binaries, and the legacy binaries will receive no updates.
2. **2025-10-16**, release `RELEASE.2025-10-15T17-29-55Z`: the first and last source-only release
   (no assets). Its notes tell container users to build their own image from source. The pinned
   `RELEASE.2025-09-07T16-13-09Z` is therefore the **last community release published with
   binaries and images**.
3. **2025-12-03**, README commit `27742d4694`: project in maintenance mode. No new changes;
   critical security fixes only "evaluated on a case-by-case basis".
4. **2026-02-12**, README commit `7aac2a2c5b`: the repository is declared no longer maintained.
   The alternatives offered are the proprietary AIStor Free and AIStor Enterprise editions.
5. **By 2026-04-24** (last push) the `minio/minio` repository is archived (`archived: true`, GitHub
   API, 2026-10-22). NVD CVE-2026-97731 also records the archiving in April 2026.
6. **2026-10-22**, `dl.min.io`: every community download path returns HTTP 410. The notice says the
   open-source server, client and KES projects are archived, and MinIO gives them no support, no
   security updates and no security advisories. It no longer accepts vulnerability reports for
   them.
7. Every MinIO advisory published in 2026 states that it affects all releases up to the final
   open-source release, and gives its fix **only in MinIO AIStor** (below).
8. Registries, 2026-10-22: Docker Hub returns 404 ("object not found") for `minio/minio`, so the
   repository no longer exists. quay.io returns 401.

**Obtainability of the pinned release.** The container image cannot be obtained from any
registry, so the digest in the environment section exists only in local caches. The GitHub release
`RELEASE.2025-09-07T16-13-09Z` still lists its 48 assets (linux-amd64/arm64 binaries, `.deb`,
`.rpm`, with `.sha256sum`, `.asc` and `.minisig` files). An HTTP HEAD request for
`minio.linux-amd64.RELEASE.2025-09-07T16-13-09Z` returned 200 on 2026-10-22, so the **binary** of the
pinned release can still be obtained from an archived repository, which can disappear without
notice. Building an image from it would change how this item is packaged, which D-4 keeps out of
CR-001.

**Since when:** no community binaries or images since October 2025, no maintenance since
February 2026. Security fixes have shipped only in the proprietary AIStor line since December
2025 (the first AIStor-only fix is in AIStor `RELEASE.2025-12-20T04-58-37Z`, CVE-2026-39414).

### Findings

How MedHub uses the item (`infra/docker-compose.yml`): single node, one drive (`server /data`),
console enabled (`--console-address ":9001"`). Ports 9000 and 9001 are `expose`d on the internal
`medhub` network only; nothing publishes them to the host, and nginx does not proxy them. SSE-S3
uses a static KMS key (`MINIO_KMS_SECRET_KEY`). The backend (`backend/app/core/object_storage.py`)
writes with `ServerSideEncryption="AES256"` and reads and deletes with the root credentials
(`OBJECT_STORE_ACCESS_KEY`, whose example value is the well-known default `minioadmin`). It issues
no presigned URLs and uses no replication, S3 Select, LDAP, OIDC, STS or service accounts.
`createbuckets` sets no bucket default encryption. The backend stores a SHA-256 `checksum` per
attachment at upload but does not check it on download.

| ID | Summary | Fixed in | Applies | MedHub affected | Hazard relevance |
|---|---|---|---|---|---|
| CVE-2026-41145 (GHSA-hv4r-mvr4-25vw) | Unauthenticated object write: `STREAMING-UNSIGNED-PAYLOAD-TRAILER` with the credential in the query string skips signature checking; only a valid access key is needed | AIStor RELEASE.2026-04-11T03-20-12Z only | Yes (≥ 2023-05-18) | **Yes**, from any process that can reach `minio:9000`. The access key is not a secret, and the example value is the default | **Yes**: an attachment can be replaced or planted without the secret key, and the replacement need not request SSE. Integrity: RISK-002, RISK-003 (the checksum is not checked on read). Confidentiality at rest: RISK-011. Requires a foothold on the internal network |
| CVE-2026-40344 (GHSA-9c4q-hq6p-c237) | Unauthenticated object write through Snowball auto-extract (`PutObjectExtractHandler`) | AIStor RELEASE.2026-04-11T03-20-12Z only | Yes | **Yes**, same precondition | **Yes**, same as above |
| CVE-2026-113466 (NVD/VulDB) | Embedded console: hard-coded key in console session-token authentication, publicly disclosed admin takeover. Applies to products "no longer supported by the maintainer" | None (up to RELEASE.2025-10-15T17-29-55Z) | Yes | **Yes**: the console is enabled on `:9001`, internal network | **Yes**: an admin can read every object, which SSE-S3 decrypts transparently (RISK-001, RISK-011), and can modify or delete objects (RISK-002, RISK-003, RISK-007). Requires a foothold on the internal network |
| CVE-2026-34204 (GHSA-3rh2-v3gr-35p9) | SSE metadata injection through `X-Minio-Replication-*` headers on a normal PutObject: the object becomes permanently unreadable | AIStor RELEASE.2026-03-26T21-24-40Z only | Yes (≥ 2024-03-30) | Yes, by a writer: the root credential holder, or an unauthenticated writer through CVE-2026-41145 | **Yes**: targeted, permanent loss of attachments, a failure mode of the SR-022 SSE function itself (RISK-007, RISK-011 "orphaned data") |
| CVE-2026-39414 (GHSA-h749-fxx7-pwpg) | S3 Select CSV memory exhaustion (DoS) | AIStor RELEASE.2025-12-20T04-58-37Z only | Yes | Only by a holder of the root credential; MedHub does not use S3 Select | Availability only (RISK-007) |
| Go 1.24.6 standard library: 59 OSV entries (GO-2025-4006 … GO-2026-6809) | For example `net/http` Range-header and MIME-header limits (CVE-2026-78667, CVE-2026-94440), HTTP/2 and `crypto/tls`/`crypto/x509` issues | Go 1.24.8 … 1.27.3; the binary will not be rebuilt | Yes | Partly: the HTTP/1 server paths are reachable on the internal network. TLS and HTTP/2 are not used (plain HTTP) | Availability only (RISK-007) |
| CVE-2025-62506 (GHSA-jjjj-jwhf-8rgr) | Session-policy bypass for service accounts and STS | Community RELEASE.2025-10-15T17-29-55Z (source only) | Yes | No: no service accounts or STS | None |
| CVE-2026-33322, CVE-2026-33419 | OIDC JWT algorithm confusion; LDAP brute force | AIStor RELEASE.2026-03-17T21-25-16Z only | Yes | No: no OIDC or LDAP | None |
| CVE-2026-42600 (GHSA-xh8f-g2qw-gcm7) | Path traversal in the internode `ReadMultiple` storage-REST endpoint | AIStor only | Distributed mode only | No: single-node deployments do not register the route | None |
| CVE-2026-97731 | Unsigned `x-amz-*` headers accepted, so a presigned PUT can be turned into a CopyObject | None (archived) | Yes | No: MedHub issues no presigned URLs | None |

### Hazard relevance and consequences

- **SR-022 SSE-AES256 (RISK-011, RISK-010).** SSE works for the backend's own writes: no anomaly
  makes MinIO store a correctly requested SSE object in plaintext. But the anomalies above let
  anyone with network reach bypass the control, by writing unencrypted or substituted objects
  (CVE-2026-41145, CVE-2026-40344) or by making encrypted objects permanently unreadable
  (CVE-2026-34204). None of them will be fixed in this item. RISK-011's protective control
  "server-side encryption enforced on the object store" therefore holds for the legitimate write
  path only.
- **RISK-010.** Its protective control (anomaly review) can detect anomalies in this item but can
  no longer lead to a patch: no fixed community version exists, or ever will. The "risk introduced
  by controls" that RISK-010 records ("pinning delays security patches; the monitoring cadence in
  PLAN-002 is the counterweight") does not hold for MinIO. The residual P = 1 that RISK-010 assumes
  does not hold for this item.
- **RISK-007.** No registry serves the image, so a fresh or amd64 host cannot deploy the object
  store from the Compose file (§5.8.5). The cached image is arm64 only. The anomalies above add
  availability paths (DoS, unreadable objects).
- **RISK-001, RISK-002, RISK-003.** Through CVE-2026-113466 and the unauthenticated-write CVEs,
  an actor on the internal network can disclose, substitute or plant attachments, including DICOM
  studies.
- **Precondition common to all of them:** network reach to `minio:9000`/`:9001`, which today means
  a compromised container on the `medhub` network or the host. This keeps the probability low but
  not negligible, since the item will never be patched.

**Escalated under CR-001 AC-12 (2026-10-22):**
- [RISK-012](../risks/RISK-012-object-store-compromised-or-unpatchable.md): new, 4 × 2, alarp.
- [PRB-042](../problem-reports/PRB-042-minio-community-edition-unmaintained.md): major. Covers the
  distribution status and the lack of upstream fixes.
- [PRB-043](../problem-reports/PRB-043-minio-unfixed-cves-exposed-by-configuration.md): critical.
  Covers the four hazard-relevant CVEs in MedHub's configuration and blocks any release.

By the human's decision of 2026-10-22, the mitigation is a separate CR-002, and no release is
made before it. The input to RISK-010 for the MinIO path is stated in RISK-012 and applied by
TASK-159. The component is not changed by CR-001 (D-4).

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — `minio/minio:latest` → `minio/minio:RELEASE.2025-09-07T16-13-09Z@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e`; pinned at the locally cached `latest` because the registry refused the pull (CR-001 Q-2), no upgrade (CR-001 A-4, TASK-155); PRB-001.
- 2026-10-22 — Version 1.2: first anomaly-list review at RELEASE.2025-09-07T16-13-09Z (TASK-154,
  CR-001 AC-11, AC-12, D-4). Distribution status confirmed from the vendor's notices: community
  edition source-only since 2025-10-15, unmaintained since 2026-02-12, archived April 2026, no
  images in any registry. Four hazard-relevant anomalies with no community fix (CVE-2026-41145,
  CVE-2026-40344, CVE-2026-113466, CVE-2026-34204). Escalated under AC-12 as RISK-012 (new,
  4 × 2 alarp), PRB-042 (major) and PRB-043 (critical; no release before CR-002, per the human's
  decision of 2026-10-22). Base-OS packages not reviewed individually (gap stated). `anomaly_review` set. No version change.
  Approval record cleared for re-approval.
- 2026-10-30 — Version 1.3: status `obsolete`, replaced by [SOUP-036](SOUP-036-seaweedfs.md)
  (SeaweedFS 4.51), CR-002 TASK-176, ADR-0015. The `minio` service and the
  `minio/minio:RELEASE.2025-09-07T16-13-09Z` image reference left `infra/docker-compose.yml`; no
  component of this record remains in the deployment definition. The `minio_data` volume is kept
  declared, unmounted, until TASK-178 migrates its objects. Approval record cleared.
