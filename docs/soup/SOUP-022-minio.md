---
id: SOUP-022
type: soup
title: MinIO object storage
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: MinIO, Inc.
soup_version: "RELEASE.2025-09-07T16-13-09Z"
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

**Not yet performed.** No published anomaly list, release notes or advisory database has been
reviewed for this exact version, so `anomaly_review` is absent. The first review is TASK-154; until
it lands this item fails the release gate's SOUP check.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — `minio/minio:latest` → `minio/minio:RELEASE.2025-09-07T16-13-09Z@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e`; pinned at the locally cached `latest` because the registry refused the pull (CR-001 Q-2), no upgrade (CR-001 A-4, TASK-155); PRB-001.
