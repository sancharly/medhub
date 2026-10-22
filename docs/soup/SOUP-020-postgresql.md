---
id: SOUP-020
type: soup
title: PostgreSQL server
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: PostgreSQL Global Development Group
soup_version: "16.15"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-22"
approved_digest: 48b8db4e8ecd15c3191ebabf0ce009eb1896aa5b8242206187f49dd38a558455
approval_note: self-approved
links: []
tags:
  - soup
  - layer:infrastructure
  - class:B
---

# SOUP-020 — PostgreSQL server 16.15

## Functional and performance requirements

Relational storage of all PHI and records, constraints, and transactional integrity.

## Required hardware and software environment

`postgres:16.15` container image with a persistent volume; base OS Debian GNU/Linux 13 (trixie) (A-5).

| Full image reference | Used by |
|---|---|
| `postgres:16.15@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97` | `infra/docker-compose.yml`: `postgres` service; `.github/workflows/ci.yml`: `backend-tests` job, `postgres` service container (identical reference) |

Resolved on 2026-10-22 with `docker buildx imagetools inspect postgres:16` and `docker buildx imagetools inspect postgres:16.15`; both reported the same image configuration (`PG_VERSION=16.15-1.pgdg13+2`). The digest is the multi-arch image index digest (`Digest:` line of the second command).

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
- 2026-10-22 — `postgres:16` → `postgres:16.15@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97`; pinned at the version the tag resolved to, no upgrade (CR-001 A-4, TASK-155); PRB-001.
