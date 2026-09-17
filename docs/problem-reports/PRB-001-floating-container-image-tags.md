---
id: "PRB-001"
type: problem-report
title: "Container images use floating tags, so builds are not reproducible"
status: open
criticality: major
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["soup", "regulatory", "configuration-management"]
---

# PRB-001 — Container images use floating tags

## Observed

Every container image is referenced by a moving tag rather than a unique designation:

- `infra/docker-compose.yml`: `minio/minio:latest`, `minio/mc:latest`, `nginx:alpine`,
  `redis:7-alpine`, `postgres:16`
- `backend/Dockerfile`: `python:3.12-slim` (builder and runtime stages)
- `frontend/Dockerfile`: `node:20-slim` (build stage), `nginx:alpine` (runtime)

Two identical `docker compose up` runs on different days can therefore produce different software.

## Impact

- **IEC 62304 §8.1.2** requires each SOUP item to carry a unique designation (exact version).
  `latest` and `alpine` are not versions, so [ADD-004](../design-outputs/architecture/ADD-004-soup-list.md)
  cannot state what is actually deployed.
- **§5.8.5–5.8.7** require the released software to be reproducible and archived. A floating tag
  breaks that claim for a release.
- **§7.1.2** anomaly review is meaningless against a version that can change without notice, and a
  silent MinIO or nginx upgrade can invalidate a verified risk control (TLS/HSTS headers, SSE-AES256).
- No patient-facing failure has been observed; this blocks a release claim, not current use, hence
  `major` rather than `critical`.

## Root cause

The Docker Compose topology and Dockerfiles were written in phase 0 (TASK-004) for local
development convenience, before a SOUP list existed to require exact versions.

## Safety evaluation

No hazard is realized today. The hazard is indirect: an unreviewed upgrade of nginx (TLS
termination, security headers) or MinIO (server-side encryption) could weaken a risk control
without anyone noticing. Assessed with the RISK records once the register exists; this PRB is
referenced there rather than duplicating the analysis.

## Proposed resolution

Pin every image to an immutable digest (`image@sha256:…`) or at minimum a full patch version, in
`infra/docker-compose.yml` and both Dockerfiles; record the pinned versions in ADD-004; and add a
CI check that fails when an image reference has no digest or patch version. Requires a CR that
links `resolves` → PRB-001.
