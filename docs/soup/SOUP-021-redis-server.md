---
id: SOUP-021
type: soup
title: Redis server
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Redis Ltd.
soup_version: 7.4.11
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-22"
approved_digest: 37838636aa5259930948402247da931ae59815e9b7162d15bcc719bf56cf3d54
approval_note: self-approved
links: []
tags:
  - soup
  - layer:infrastructure
  - class:B
---

# SOUP-021 — Redis server 7.4.11

## Functional and performance requirements

Session store with TTL eviction (SR-030) and Celery broker/result backend.

## Required hardware and software environment

`redis:7.4.11-alpine` container image; base OS Alpine Linux v3.21 (A-5).

| Full image reference | Used by |
|---|---|
| `redis:7.4.11-alpine@sha256:892022f9f18c26c92c30e15194d132f90044af87b94a491a75429bbc3982eab1` | `infra/docker-compose.yml`: `redis` service; `.github/workflows/ci.yml`: `backend-tests` job, `redis` service container (identical reference) |

Resolved on 2026-10-22 with `docker buildx imagetools inspect redis:7-alpine` and `docker buildx imagetools inspect redis:7.4.11-alpine`; both reported the same image configuration (Redis 7.4.11). The digest is the multi-arch image index digest (`Digest:` line of the second command).

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
- 2026-10-22 — `redis:7-alpine` → `redis:7.4.11-alpine@sha256:892022f9f18c26c92c30e15194d132f90044af87b94a491a75429bbc3982eab1`; pinned at the version the tag resolved to, no upgrade (CR-001 A-4, TASK-155); PRB-001.
