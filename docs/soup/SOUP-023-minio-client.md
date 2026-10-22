---
id: SOUP-023
type: soup
title: MinIO client (mc)
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: MinIO, Inc.
soup_version: "RELEASE.2025-08-13T08-35-41Z"
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
- 2026-10-22 — `minio/mc:latest` → `minio/mc:RELEASE.2025-08-13T08-35-41Z@sha256:a7fe349ef4bd8521fb8497f55c6042871b2ae640607cf99d9bede5e9bdf11727`; pinned at the locally cached `latest` because the registry refused the pull (CR-001 Q-2), no upgrade (CR-001 A-4, TASK-155); PRB-001.
