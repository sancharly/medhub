---
id: SOUP-023
type: soup
title: MinIO client (mc)
status: obsolete
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-30"
manufacturer: MinIO, Inc.
soup_version: RELEASE.2025-08-13T08-35-41Z
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:infrastructure
  - class:B
---

# SOUP-023 — MinIO client (mc) RELEASE.2025-08-13T08-35-41Z

## Functional and performance requirements

Bucket creation and policy at bring-up.

## Required hardware and software environment

`minio/mc:RELEASE.2025-08-13T08-35-41Z` container image (Go 1.24.6, linux/arm64 as cached; base OS Red Hat Enterprise Linux 9.6, UBI 9 micro, A-5), run once at bring-up.

| Full image reference | Used by |
|---|---|
| `minio/mc:RELEASE.2025-08-13T08-35-41Z@sha256:a7fe349ef4bd8521fb8497f55c6042871b2ae640607cf99d9bede5e9bdf11727` | `infra/docker-compose.yml`: `createbuckets` service |

The registry refused this repository on 2026-10-22 (Docker Hub "pull access denied", `quay.io/minio/*` 401), so the digest could not be checked against a registry. It is the `RepoDigest` of the locally cached image (`docker image inspect --format '{{json .RepoDigests}}'`), the release from `mc --version` inside it. The cached image is arm64 only. The release is `RELEASE.2025-08-13T08-35-41Z` (image created 2025-09-07). `docker compose pull` cannot obtain it and a fresh or amd64 host cannot build the stack; CR-001 AC-5 (build, start and smoke test of the pinned stack) is therefore reproducible only on a host that holds the cached image. The distribution status is confirmed or refuted by TASK-154 (CR-001 D-4); the component is not changed here.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11, AC-12, D-4) by the Software Architect role, at
the pinned version `minio/mc:RELEASE.2025-08-13T08-35-41Z@sha256:a7fe349e…1727` (Go 1.24.6; base
OS Red Hat Enterprise Linux 9.6, UBI 9 micro).

Sources checked:

| Source | URL | What was checked |
|---|---|---|
| mc GitHub Security Advisories (vendor) | https://github.com/minio/mc/security/advisories | None published |
| GitHub Advisory Database, Go ecosystem | https://github.com/advisories?query=ecosystem%3Ago+github.com%2Fminio%2Fmc | None for `github.com/minio/mc` |
| mc releases and README (vendor) | https://github.com/minio/mc/releases | Last release; repository state |
| MinIO download site (vendor notice) | https://dl.min.io/client/mc/release/linux-amd64/archive/mc.RELEASE.2025-08-13T08-35-41Z | Distribution notice (HTTP 410) |
| Docker Hub registry API | https://hub.docker.com/v2/repositories/minio/mc/ | Whether the image repository still exists |
| NVD CVE API 2.0 | https://services.nvd.nist.gov/rest/json/cves/2.0 | Keyword `minio`, published 2026-07-01..2026-10-22: no entry for the client |
| OSV (Go, `stdlib`) | https://api.osv.dev/v1/query | Go standard library 1.24.6, the toolchain the binary was built with |

Method for the base OS: the same 22-package UBI 9 micro base as SOUP-022 (RPM database read from
the image without running it). Package versions were not checked one by one against Red Hat
errata: no RPM tool or image scanner was available (`docker scout cves`, CLI 0.20.0, crashed).
**This gap is explicit.** The image has not been updated since September 2025 and will not be
rebuilt.

**Distribution status (CR-001 D-4): confirmed**, as for SOUP-022. The `minio/mc` repository is
archived (`archived: true`, last push 2025-11-20). The pinned `RELEASE.2025-08-13T08-35-41Z`
(published 2025-09-07) is its **last release**. `dl.min.io` returns HTTP 410 with the notice that
the open-source server, client and KES projects are archived and receive no security updates or
advisories. Docker Hub returns 404 for `minio/mc`. The GitHub release still lists its 48 assets,
and an HTTP HEAD request for `mc.linux-amd64.RELEASE.2025-08-13T08-35-41Z` returned 200 on
2026-10-22. So the binary, but not the image, can still be obtained.

Findings:

| ID | Summary | Fixed in | Applies | MedHub affected | Hazard relevance |
|---|---|---|---|---|---|
| Go 1.24.6 standard library: 59 OSV entries (GO-2025-4006 … GO-2026-6809) | `net/http`, `crypto/tls`, `crypto/x509`, `net/url` and parser issues | Go 1.24.8 … 1.27.3; the binary will not be rebuilt | Yes | Marginally: `mc` runs once at bring-up, as a client of the local `minio` service over plain HTTP on the internal network, and talks to no other host | None |
| Item unmaintained (D-4) | No fixes, no images | — | Yes | Yes: `backend` `depends_on` `createbuckets`, so a host without the cached image cannot bring the stack up | Deployment availability (RISK-007), escalated with SOUP-022 |

No vendor advisory exists for `mc` at any version. The commands MedHub runs (`alias set`, `mb
--ignore-existing`, `anonymous set none`) are not named by any anomaly. `anonymous set none`,
which keeps the bucket private (RISK-001), behaves as documented at this version.

Hazard relevance: no anomaly of the client itself is hazard-relevant. The consequence of D-4 for
this item is the loss of obtainability on a fresh host (RISK-007, §5.8.5). Escalated together
with SOUP-022 under CR-001 AC-12 (2026-10-22), as
[RISK-012](../risks/RISK-012-object-store-compromised-or-unpatchable.md) (new, 4 × 2 alarp) and
[PRB-042](../problem-reports/PRB-042-minio-community-edition-unmaintained.md) (major). The fix is
in the separate CR-002 (human decision, 2026-10-22). The component is not changed by CR-001 (D-4).

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — `minio/mc:latest` → `minio/mc:RELEASE.2025-08-13T08-35-41Z@sha256:a7fe349ef4bd8521fb8497f55c6042871b2ae640607cf99d9bede5e9bdf11727`; pinned at the locally cached `latest` because the registry refused the pull (CR-001 Q-2), no upgrade (CR-001 A-4, TASK-155); PRB-001.
- 2026-10-22 — Version 1.2: first anomaly-list review at RELEASE.2025-08-13T08-35-41Z (TASK-154,
  CR-001 AC-11, AC-12, D-4). No vendor advisory. The Go 1.24.6 stdlib entries are not
  hazard-relevant for a one-shot internal client. Distribution status confirmed: repository
  archived, this is the last release, no image in any registry. Escalated with SOUP-022 under AC-12
  as RISK-012 and PRB-042 (fix in CR-002). Base-OS packages not reviewed individually (gap stated).
  `anomaly_review` set. No version change. Approval record cleared for re-approval.
- 2026-10-30 — Version 1.3: status `obsolete`, retired by CR-002 TASK-175 (ADR-0015 D2), replaced by the
  boto3 initialiser (`backend/app/core/object_store_init.py`, SOUP-019). The `createbuckets` service and
  the `minio/mc` image reference left `infra/docker-compose.yml`. No component of this record remains
  in the deployment. Approval record cleared.
