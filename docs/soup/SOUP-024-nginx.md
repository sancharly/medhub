---
id: SOUP-024
type: soup
title: nginx
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: F5, Inc. / nginx authors
soup_version: 1.31.8
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-22"
approved_digest: 2a00a96bcab148e0f0c5c30394311528e35c9c4e37b456586d7e048ca4af7777
approval_note: self-approved
links: []
tags:
  - soup
  - layer:infrastructure
  - class:B
---

# SOUP-024 — nginx 1.31.8

## Functional and performance requirements

TLS termination, HSTS and security headers at the reverse proxy (SR-001, SR-031), and static serving of the frontend bundle.

## Required hardware and software environment

`nginx:1.31.8-alpine` container image; base OS Alpine Linux v3.24 (A-5); certificates in `infra/certs/`.

| Full image reference | Used by |
|---|---|
| `nginx:1.31.8-alpine@sha256:e2d97c2b8c016f12c2f1a27d095685063b2f281c4edf2babfde6001cf4fb77a8` | `infra/docker-compose.yml`: `reverse-proxy` service; `frontend/Dockerfile`: runtime stage (identical reference) |

Resolved on 2026-10-22 with `docker buildx imagetools inspect nginx:alpine` and `docker buildx imagetools inspect nginx:1.31.8-alpine`; both reported the same image configuration (`NGINX_VERSION=1.31.8`). The digest is the multi-arch image index digest (`Digest:` line of the second command). The tag `nginx:alpine` and `nginx:1.31.8-alpine` had the same image configuration but different index digests that day (`nginx:alpine` = `sha256:060849a174666c53439dc7cecbf8f67e225c7cbfb1a44ca97915d9a172a81e6d`); the full-release tag's digest is pinned.

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
- 2026-10-22 — `nginx:alpine` → `nginx:1.31.8-alpine@sha256:e2d97c2b8c016f12c2f1a27d095685063b2f281c4edf2babfde6001cf4fb77a8`; pinned at the version the tag resolved to, no upgrade (CR-001 A-4, TASK-155); PRB-001.
