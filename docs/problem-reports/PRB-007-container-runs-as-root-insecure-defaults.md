---
id: "PRB-007"
type: problem-report
title: "Runtime container runs as root and Compose ships insecure default secrets"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
criticality: major
links: []
tags: ["security", "configuration-management"]
---

# PRB-007 — Runtime container runs as root and Compose ships insecure default secrets

## Observed

`backend/Dockerfile` defines no `USER`, so the runtime image runs as root. `infra/docker-compose.yml` supplies `changeme` and `minioadmin` style defaults via `${VAR:-default}`, so a deployment boots successfully with known credentials.

## Impact

A container escape or a forgotten `.env` becomes a full compromise of PHI. Touches SR-022, SR-031 and NFR-007.

## Safety evaluation

Contributes to RISK-001 (unauthorized disclosure) and RISK-005 (account takeover). No deployment incident known.

## Resolution

Not yet tracked by a task. Proposed: add a non-root `USER` with an owned writable path, and make every secret required (no `:-default`) so bring-up fails loudly. Needs a task and a CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Medium.
