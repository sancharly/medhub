---
id: "PRB-007"
type: problem-report
title: "Runtime container runs as root and Compose ships insecure default secrets"
status: open
version: "1.7"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-01"
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

**Interim note (2026-10-31, TASK-197; reworded 2026-11-01, TASK-203; TASK-198 added 2026-11-01).**

- *Application start-up refusal (TASK-197).* The backend refuses to start when a required secret
  is unset, empty or a known placeholder: `DATABASE_URL` (its password), `AT_REST_ENCRYPTION_KEY`
  and the two object-store keys; `AT_REST_ENCRYPTION_KEY` must also decode to 32 bytes.
  `SMTP_PASSWORD` is checked only when `SMTP_USER` is set. The optional owner URL, retired keys
  and SSE key are checked **only when set**; they are not refused when unset. The rule is
  `backend/app/core/secret_settings.py` (TS-015 TC-015.3).
- *The worker and beat enforce it in the Compose stack (TASK-191, PRB-061).* The `celery-worker`
  container now runs Celery and a `celery-beat` container runs the scheduler, so `worker_init` and
  `beat_init` run: with a placeholder `OBJECT_STORE_SECRET_KEY` both exit 1 naming the setting.
  `db-migrate` checks the secret settings before it connects, and a `DATABASE_URL` that names the
  owner's user or password is refused there.
- *Template and Compose (TASK-203).* `infra/.env.example` holds no value for any secret
  (`POSTGRES_PASSWORD` is now in it), `infra/docker-compose.yml` has a `:?` guard and no default
  on `POSTGRES_PASSWORD`, `DATABASE_URL`, `AT_REST_ENCRYPTION_KEY` and the object-store keys, and
  `infra/DEPLOY.md` has a "Secret settings" table (TS-015 TC-015.2, TC-015.4). Item 2 is fixed
  for the template and Compose.
- *Frontend image (TASK-198).* `frontend/Dockerfile` now ends with `USER nginx` (UID 101) and
  `frontend/nginx.conf` listens on 8080; the reverse proxy targets `frontend:8080` and Compose
  exposes 8080. On a started stack the `backend`, `celery-worker` and `frontend` containers run
  PID 1 as a non-zero UID and every built image has a non-root `Config.User`
  (`infra/tests/test_images_non_root.py`, `infra/smoke-test.sh` section 11; TS-015 TC-015.1).
  Item 1 is fixed. Since TASK-191 the `celery-worker` and `celery-beat` UID checks cover the Celery processes themselves (`infra/smoke-test.sh` sections 11 and 12).
- *Runtime database role (TASK-191, corrected in round 2).* `backend`, `celery-worker` and
  `celery-beat` connect as `medhub_app` (no superuser, no ownership, no membership; a password of its
  own that must differ from the owner's). Round 1 of the QA review found that `env_file: .env` still
  passed `POSTGRES_PASSWORD`, the owner (superuser) password, to those three services, so a
  compromised process could reconnect as the owner. Fixed: no service has `env_file` any more; each
  lists only the settings it reads, so the owner password and `DATABASE_OWNER_URL` reach `postgres`
  and `db-migrate` only. Verified by value: `infra/tests/test_compose_db_roles.py`
  (`test_no_owner_credential_value_reaches_a_service_but_postgres_and_db_migrate`) and smoke-test
  section 12 (the password read from `postgres` is absent from `/proc/1/environ` and `Config.Env` of
  every other running container; from `backend` an owner connection fails with no credential;
  TS-015 TC-015.2). Item 3 is fixed.
- *Reverse-proxy image (TASK-198 QA, MEDIUM 1).* The official nginx reverse-proxy image runs its
  master as UID 0; it is not built by MedHub and is outside SR-041 AC 1. The human is to accept
  this at release.
- *Still open.* Key separation (TASK-196). The report stays `open` until then.

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
- 1.4 (2026-11-01) — TASK-203: interim note reworded (what is refused when unset, the worker limit from PRB-061) and the template/Compose/guide part recorded. Status and criticality unchanged.
- 1.5 (2026-11-01) — TASK-198: interim note records the non-root frontend image (item 1). Status and criticality unchanged; TASK-196 and TASK-191 remain.
- 1.6 (2026-11-01) — TASK-191: interim note updated (worker and beat enforce the secret rule, runtime database role, reverse-proxy root sentence). Status and criticality unchanged; TASK-196 remains.
- 1.7 (2026-11-01) — TASK-191 round 2 (QA finding 1): the runtime-role paragraph corrected; the owner password no longer reaches the application services (no `env_file`). Status and criticality unchanged; TASK-196 remains.
