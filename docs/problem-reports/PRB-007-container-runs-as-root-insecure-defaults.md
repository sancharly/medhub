---
id: "PRB-007"
type: problem-report
title: "Runtime container runs as root and Compose ships insecure default secrets"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-30"
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

## Note: object-store credentials resolved by CR-002 (2026-10-30)

The object-store part of this report is resolved by
[CR-002](../change-requests/CR-002-secure-or-replace-the-minio-object-store.md) (TASK-174, commit
`8c46bcc`): `OBJECT_STORE_ACCESS_KEY` and `OBJECT_STORE_SECRET_KEY` have no Compose default
(`${…:?}` guards), `infra/.env.example` ships them empty, and the `object-store-preflight` service
refuses an unset, empty or known-default key (`minioadmin`, `changeme`, `admin`, `password`,
`secret`, any case) or a secret key shorter than 16 characters before the store starts (TS-014
TC-014.1..3). MinIO itself is replaced by SeaweedFS (TASK-176).

This report stays `open` for the rest: the runtime container running as root, the other
`${VAR:-default}` secrets, and `AT_REST_ENCRYPTION_KEY`. CR-002 decided (Q-3, Q-7, D-6) to carry
over the reuse of `AT_REST_ENCRYPTION_KEY` for both field encryption and the object store's SSE key,
and to track **key separation** here. Losing or changing that key makes the stored attachments
unreadable as well as the encrypted fields (SOUP-036 F-4; RISK-011 1.3).

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Medium.
