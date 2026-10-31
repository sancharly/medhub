---
id: "PRB-007"
type: problem-report
title: "Runtime container runs as root and Compose ships insecure default secrets"
status: open
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-31"
criticality: major
links: []
tags: ["security", "configuration-management"]
---

# PRB-007 — Runtime container runs as root and Compose ships insecure default secrets

## Observed

`backend/Dockerfile` defines no `USER`, so the runtime image runs as root. `infra/docker-compose.yml` supplies `changeme` and `minioadmin` style defaults via `${VAR:-default}`, so a deployment boots successfully with known credentials.

## Impact

A container escape or a forgotten `.env` becomes a full compromise of PHI. Touches SR-022, SR-031 and NFR-007.

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role; CR-004 Q-1). **Partly stale.
What is still true is listed last.**

No longer true:

- `backend/Dockerfile:18-19` creates `medhub` and sets `USER medhub` (commit `a928072`,
  2026-06-30). The backend, the worker, `object-store-preflight` and `object-store-init` all run
  this image, so none of them runs as root.
- `infra/docker-compose.yml` has no `${VAR:-default}` on a secret any more. The object-store keys
  have `:?` guards (`docker-compose.yml:52-53,124-125,144-145,176-177`) and the preflight
  (CR-002). `AT_REST_ENCRYPTION_KEY` has a `:?` guard where the store reads it (`:147`).

Still true:

1. **Frontend image runs as root.** `frontend/Dockerfile:11-13` is `nginx:1.31.8-alpine` with no
   `USER`; the master process runs as root and listens on port 80 (`frontend/nginx.conf:2`).
2. **Known placeholder secrets in the template.** `infra/.env.example` ships
   `DATABASE_URL=postgresql://medhub:changeme@…` (`:14`), `SESSION_SIGNING_KEY=change-me-to-a-…`
   (`:38`), `SMTP_PASSWORD=changeme` (`:46`) and `AT_REST_ENCRYPTION_KEY=change-me-to-a-…` (`:52`).
   Nothing refuses them: `backend/app/core/config.py:31,37,40` only require the settings to be
   present. `POSTGRES_PASSWORD` is not in the template at all, and the Compose file passes it
   without a guard (`docker-compose.yml:92`), so an unset value reaches the database image
   instead of stopping Compose with a message naming it. The backend and worker take everything
   from `env_file: .env` (`:47,197`) with no guard.
3. **The application connects as the database superuser** (`medhub`, `POSTGRES_USER`;
   `docker-compose.yml:90-91`, `.env.example:14`), so a leaked application credential is a
   superuser credential. Tracked with PRB-005 (ADR-0017).
4. **One key for two stores.** The object store's SSE key is `AT_REST_ENCRYPTION_KEY`
   (`docker-compose.yml:146-147`), the field-encryption key. Losing or changing it makes every
   attachment unreadable (SOUP-036 F-4); a compromise of it exposes both stores (RISK-011).
5. SMTP: `config.py:36-37` makes `SMTP_USER` and `SMTP_PASSWORD` required although the sender
   already skips authentication when the user is empty (`backend/app/workers/email_tasks.py:44-45`).
   CR-004 Q-5 (decided 2026-10-31): SMTP without authentication is supported, and
   `SMTP_PASSWORD` is required only when `SMTP_USER` is set.

Not recommended for rejection: items 1, 2, 4 and 5 stand.

## Safety evaluation

Contributes to RISK-001 (unauthorized disclosure) and RISK-005 (account takeover). No deployment incident known.

## Resolution

Planned in CR-004: TASK-197 (start-up refusal of missing or placeholder secrets by the backend,
the worker and the preflight), TASK-203 (no default in Compose, empty template, generation guide), TASK-198 (non-root frontend image;
UID checks on the images and the running stack), TASK-196 (separate object-store SSE key, with a
rehearsed migration of the existing attachments), TASK-191 (runtime database role, PRB-005).
TASK-140 removes `SESSION_SIGNING_KEY` (PRB-018). Not yet fixed in full; see the interim note below.

**Interim note (2026-10-31, TASK-197).** The start-up refusal is in place: the backend, the worker
and beat refuse to start when `DATABASE_URL` (its password), `SMTP_PASSWORD` (when `SMTP_USER` is
set), `AT_REST_ENCRYPTION_KEY`, the object-store keys or the optional owner URL, retired keys and
SSE key are unset, empty or a known placeholder, and when the encryption key does not decode to 32
bytes (`backend/app/core/secret_settings.py`; TS-015 TC-015.3). This part of item 2 is
fixed for the application processes. Still open: the template still ships the placeholders and
Compose has no `:?` guard on `POSTGRES_PASSWORD` (TASK-203), the frontend image runs as root
(TASK-198), key separation (TASK-196) and the runtime database role (TASK-191). The report stays `open`.

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

## Version history

- 1.2 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
- 1.3 (2026-10-31) — TASK-197: interim note under Resolution (start-up refusal in place). Status and criticality unchanged.
