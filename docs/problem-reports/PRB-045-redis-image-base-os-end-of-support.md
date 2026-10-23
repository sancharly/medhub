---
id: "PRB-045"
type: problem-report
title: "Redis image base OS Alpine 3.21 reaches end of support on 2026-11-01"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
criticality: minor
links: []
tags: ["soup", "maintenance", "configuration-management"]
---

# PRB-045 — Redis image base OS Alpine 3.21 reaches end of support on 2026-11-01

## Observed

The pinned Redis image [SOUP-021](../soup/SOUP-021-redis-server.md),
`redis:7.4.11-alpine@sha256:892022f9f18c26c92c30e15194d132f90044af87b94a491a75429bbc3982eab1`, is
built on Alpine Linux 3.21.9. That branch reaches end of support on **2026-11-01**
(https://alpinelinux.org/releases/, checked 2026-10-22). After that date its packages (OpenSSL
3.3.7, musl 1.2.5, busybox, zlib and the rest) receive no security fixes. The image is used by
`infra/docker-compose.yml` (service `redis`) and by `.github/workflows/ci.yml` (`backend-tests`
service container).

## Impact

On 2026-10-22, OSV reports no entry for any of the image's 13 source packages at its installed
version, so there is no open anomaly today. From 2026-11-01 on, new base-OS vulnerabilities will
stay unfixed in the pinned image, and the PLAN-002 review can only detect them.

## Safety evaluation

No hazard today: the anomaly review of 7.4.11 found nothing hazard-relevant. Redis carries
SR-030's session store (RISK-005) and the Celery broker (RISK-007). An unfixed base-OS flaw would
need a foothold on the internal `medhub` network to be reached. Criticality is `minor`: this is a
maintenance obligation (§6.1 f), not a realized defect.

Released versions (§9.3): no `release` record exists (`docs/releases/` is absent), so no released
version in use is affected and no notification is needed.

## Proposed resolution

In a separate CR (an image upgrade, which CR-001 A-4 excludes):

- Move to a `redis:7.4.x-alpine` image built on a supported Alpine branch, pinned by tag and
  digest, in both Compose and CI.
- Review that version's anomaly list and update SOUP-021.
- Re-run the backend suite and the Compose smoke test.

Do this before the first release, or before 2026-11-01 plus the next review, whichever comes
first.

## Source

Raised by TASK-154, the first SOUP anomaly-list review (CR-001 AC-12), on 2026-10-22. The evidence
is in SOUP-021's "Anomaly list review" section.
