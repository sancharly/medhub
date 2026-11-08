# 05 - Building Block View (Software Items & Units)

This section is the **hierarchical decomposition into software items and software units** required by the software development plan (IEC 62304). The system (level 0) decomposes into software items (level 1); each item decomposes into software units (level 2) — the smallest pieces, each independently unit-testable. Where an item cannot be meaningfully decomposed further, the item *is* the unit.

Diagram: [`../specifications/diagram-building-blocks.puml`](../specifications/diagram-building-blocks.puml)

## Level 0 — System

**MedHub** = Frontend SPA + Backend (modular monolith) + supporting stores (PostgreSQL, Redis, Object storage) + Worker, deployed behind a TLS reverse proxy. Decomposed into the items below. The deployment definition itself (Compose topology, secrets, database roles, runtime users) is the item SI-DEPLOY.

## Level 1 — Software items

| Item ID         | Name                           | Responsibility                                                                               | Key reqs                                       |
|-----------------|--------------------------------|----------------------------------------------------------------------------------------------|------------------------------------------------|
| SI-API          | API Layer / Routers            | HTTP endpoints, request/response DTOs, validation, error formatting, AuthZ dependency wiring, originating client address, CSRF enforcement | SR-001, SR-031, SR-042, all API SRs |
| SI-AUTH         | Authentication & Session       | Login, logout, password change, session lifecycle, lockout                                   | SR-002, SR-025, SR-029, SR-030                 |
| SI-AUTHZ        | Authorization & Consent        | Deny-by-default decisions; per-source consent grants; module access guard                    | SR-005–009, SR-011, SR-015, SR-036, SR-008     |
| SI-IDENTITY     | Identity & Account Lifecycle   | Account CRUD, role-constrained creation, activation, deactivate/reactivate/delete, erasure   | SR-003, SR-004, SR-024, SR-032, SR-033, SR-034 |
| SI-GROUPS       | Groups & Module Enablement     | Group CRUD, auto/manual membership, per-group module enablement                              | SR-014, SR-015                                 |
| SI-APPT         | Appointments & Notifications   | Appointment CRUD, state machine, confirmation, notification dispatch                         | SR-010, SR-011, SR-035                         |
| SI-CLINICAL     | Clinical Records               | Clinical-entry CRUD with required fields & attribution                                       | SR-012                                         |
| SI-ATTACH       | Attachment Service             | Upload/fetch attachment binaries via object storage, authorized                              | SR-013, SR-022                                 |
| SI-OBJSTORE     | Object Store Deployment        | The deployed S3-compatible store: credential preflight, server, bucket initialiser, isolated network | SR-040, SR-022, SR-028                         |
| SI-AUDIT        | Audit Service                  | Append-only audit log of security-relevant events; typed fields; source address              | SR-023                                         |
| SI-MODHOST      | Module Host / Plugin Registry  | Module discovery/registration, platform-service injection, router mounting                   | SR-016                                         |
| SI-MOD-DICOM-BE | DICOM Module (backend)         | Authorized DICOM byte/frame endpoints behind the module contract                             | SR-016, SR-017                                 |
| SI-PERSIST      | Persistence                    | SQLAlchemy models, repositories, Alembic migrations, database roles, field-encryption envelope and key rotation | SR-021, SR-022, SR-023 |
| SI-WORKER       | Async Worker                   | Celery worker and beat: send activation & appointment emails, session-revocation propagation, retention sweep; log redaction | SR-033, SR-035, SR-034, SR-043 |
| SI-FE-SHELL     | Frontend App Shell             | Layout, routing, responsive frame, navigation, route guard by role, module mounting, error/confirmation UX | SR-019, SR-020, SR-027, SR-005, SR-009 |
| SI-FE-AUTH      | Frontend Auth/Session UI       | Login, activation, password, inactivity warning/extend                                       | SR-002, SR-025, SR-030, SR-033                 |
| SI-FE-CORE      | Frontend Core Views            | Profile, patients, clinical entries, appointments, consent, admin (accounts/groups/modules)  | SR-003–016, SR-035, SR-036                     |
| SI-FE-MODREG    | Frontend Module Registry       | Dynamic module registration, gated nav, lazy chunk loading                                   | SR-015, SR-016                                 |
| SI-MOD-DICOM-FE | DICOM Viewer Module (frontend) | Cornerstone3D viewport, window/level, zoom, pan, slice nav                                   | SR-017, SR-018                                 |
| SI-FE-APICLIENT | Frontend API Client            | Hand-written typed `ApiClient` (types generated from OpenAPI); session/CSRF handling         | NFR-006, SR-031                                |
| SI-DEPLOY       | Deployment Configuration       | Compose topology and start-up order, environment template, secret-setting rule, database roles, runtime users, proxy logging | SR-041, SR-042, SR-023, SR-022, SR-043 |

## Level 2 — Software units (per item)

### SI-API
- `U-API-Routers` — endpoint definitions per resource (auth, accounts, groups, appointments, clinical, attachments, consents, modules).
- `U-API-DTO` — Pydantic request/response schemas (camelCase, FHIR-traceable).
- `U-API-ErrorHandler` — RFC 7807 problem+json mapping (SR-027.3, api-design.md).
- `U-API-Deps` — DI providers: current session, current user, `authorize(...)` guard.
- `U-API-ClientAddress` — pure ASGI middleware (`backend/app/core/client_address.py`), mounted first. It applies the trusted-proxy rule once per request: the TCP peer, unless the peer is in `TRUSTED_PROXIES`, then the right-most `X-Forwarded-For` entry that is not itself a trusted proxy; malformed entries are skipped and an empty setting trusts nothing. The result is published in `request.state` and a `ContextVar` for the audit writer and the rate limit. Gunicorn's own forwarded-header handling is off (`--forwarded-allow-ips=`) (SR-042 AC 1 to AC 3, [ADR-0019](adr/0019-originating-client-address-trusted-proxy-rule.md)).
- `U-API-RateLimit` — limit on `POST /anonymized-data/retrieve` (`backend/app/api/routers/anonymized_data.py`): 5 attempts per originating address in a fixed 3600 s window that starts at the first counted attempt (atomic `INCR` and `EXPIRE NX` in one `MULTI`/`EXEC`), refused with 429 before the code is evaluated; a request with no peer address is refused rather than put in a shared bucket (SR-042 AC 4, AC 5; limit values of ADR-0013).
- `U-API-Security` — security headers and CSRF enforcement (`backend/app/core/security_middleware.py`). CSRF exemptions are an exact set of paths plus one whole-path pattern for `POST /api/v1/activation/{token}`; a sibling or child path is enforced, and a route-inventory test keeps the set reviewed (SR-031 AC 3).
- Router access checks (`account:unlock`, `module:list`, `consent:grant`/`revoke`/`list`, `patient_roster:list`) and the admin projection test (`requires_admin_projection`) are asked of `AuthorizationService`; no router compares a role itself (see `U-AUTHZ-Policy`).
- `U-API-ErrorHandler` also answers `503` `session-cap-contention` with `Retry-After: 1` (the sign-in cap could not be applied) and `400` `validation-error` with a field-level `errors[]`, among them `filename_max_bytes` for an attachment name over 255 UTF-8 bytes (section 12). The 500 handler logs the matched route template, never the raw path (SR-043 AC 4).
- The API process installs the shared log redaction filter (`backend/app/core/logging.py`, SR-043 AC 2) and binds the configured Celery app as the process default in its lifespan (`_bind_celery_app()` in `backend/app/main.py`, PRB-071).

### SI-AUTH
- `U-AUTH-Login` — credential verification (Argon2id), generic failure (SR-002). The lockout service is a required, typed dependency, so no call path can omit it (SR-029 AC 1, PRB-018). A login that evicted a session reports it (`evicted_session`) for the notification of SR-030 AC 7; contention on the cap that does not clear is answered 503 and stores no session.
- `U-AUTH-Lockout` — failed-attempt counter, 5/30-min lock, admin unlock (SR-029).
- `U-AUTH-Session` — Redis session create/refresh/invalidate, role timeouts, absolute lifetime, concurrency cap (SR-030). The cap check, the eviction of the oldest live session and the insertion of the new one are one optimistic Redis transaction (`WATCH` on the account's sorted set, `MULTI`/`EXEC`, at most 20 attempts); only members whose `session:{id}` key exists count, and expired members are removed in the same transaction. The refresh is a conditional write (`SET … EX … XX`), so an ended session is never written again (SR-030 AC 5, AC 7; PRB-023, PRB-064, PRB-065, PRB-066).
- `U-AUTH-PasswordPolicy` — server-side complexity, history(12), max-age(180d), reuse/username checks (SR-025).
- `U-AUTH-Cookie` — Secure/HttpOnly/SameSite=Strict cookie issuing (SR-030.6).

### SI-AUTHZ
- `U-AUTHZ-Policy` — deny-by-default decision engine (user type + relationship + consent + module) (SR-005), and **the only place an access decision is taken** ([ADR-0006](adr/0006-authz-consent-model.md)). `AuthorizationService.decide()` returns a `Decision` (allow plus a basis: `OWNER`, `CONSENT:MANUAL`, `ROLE`, `MODULE:ENABLED`/`MODULE:DISABLED`, and for denials `TARGET`, `TARGET_UNSET`, `SELF`) and audits every decision with actor, action, target, outcome and source address (SR-023 AC 7). It decides appointment list scope and single-appointment visibility (`_eval_appointment_read`, SR-011), module access, the account actions `account:create`/`deactivate`/`reactivate`/`delete` and `activation:resend` (SR-032 AC 1, AC 4, AC 5; SR-034 AC 1), and the role-only router actions `account:unlock`, `module:list`, `consent:grant`/`revoke`/`list` and `patient_roster:list`. `account:create` is denied unless the requested type is stated. A refusal that the contract answers with 404 (SR-011 AC 4) is still audited as `AUTHZ_DENIED`. A static test fails when a `user_type` comparison that decides access appears outside `backend/app/authz/`; it does not see `getattr` dispatch on a role or `self.<attr>` aliases (stated limit, PRB-027).
- `U-AUTHZ-Consent` — `ConsentGrant` create/revoke, per-source union evaluation (SR-008, SR-036).
- `U-AUTHZ-AdminProjection` — non-clinical field projection for admin personnel (SR-009); `requires_admin_projection(actor)` tells the account routers when to apply it.
- `U-AUTHZ-ModuleGuard` — module-enabled-for-group check (SR-015); an input to `U-AUTHZ-Policy`, not called by services or dependencies to decide on its own.
- The unit `U-AUTHZ-ApptVisibility` no longer exists: its module was deleted and the rule is `AuthorizationService._eval_appointment_read` (PRB-026).

### SI-IDENTITY
- `U-ID-AccountCrud` — create (role-constrained, min fields, unique email), read (SR-003, SR-004, SR-032).
- `U-ID-Activation` — single-use 72h token, password-set, activate, resend (SR-033).
- `U-ID-Lifecycle` — deactivate/reactivate (session kill ≤30s), delete+confirm, email release (SR-034).
- `U-ID-Erasure` — deletion as anonymization into a retained anonymized dataset; generates the user-held anonymization code, stores only its salted KDF hash, sets the 5-year retention deadline, and authorizes code-based retrieval (SR-024, ADR-0013).

### SI-GROUPS
- `U-GRP-Crud` — group create/list (SR-014).
- `U-GRP-Membership` — auto-by-type + manual add/remove (SR-014.2/3).
- `U-GRP-ModuleEnable` — enable/disable module per group (SR-015).

### SI-APPT
- `U-APPT-Crud` — create (validate refs/datetime), list scoped (SR-010, SR-011).
- `U-APPT-State` — PENDING/CONFIRMED/DECLINED transitions, patient-only confirm/decline (SR-035).
- `U-APPT-Notify` — enqueue in-app + email notification via the `Notification` abstraction (best-effort send, `status` field + post-send hook as the extension point for future delivery/read tracking) (SR-035.2/3, section 8.12).
- `U-APPT-ConsentLink` — on confirm create / on decline revoke `APPOINTMENT:{id}` grant (SR-036).

### SI-CLINICAL
- `U-CLIN-EntryCrud` — create entry with required fields, author from session, list for patient (SR-012).

### SI-ATTACH
- `U-ATT-Upload` — validate, store object (SSE), bind to entry/patient transactionally (SR-013).
- `U-ATT-Upload` also refuses a file name over 255 UTF-8 bytes with a 400 before anything is written; the name is never truncated, as it is part of the clinical record (SR-013, PRB-069).
- `U-ATT-Fetch` — authorized stream / scoped pre-signed URL; verifies the stored SHA-256 checksum before serving and refuses a mismatch with an audit FAILURE (SR-005, SR-013.3). The `Content-Disposition` header is built only by `backend/app/api/content_disposition.py`: pure ASCII, an ASCII fallback `filename` (at most 150 characters) plus an RFC 5987 `filename*` (at most 255 bytes of the name), extension kept, bidi and control characters mapped to `_`, so the header fits the proxy's 4 KB buffer for any stored name (SR-013 AC 3, PRB-063, PRB-069).

### SI-OBJSTORE
Deployed infrastructure, not application code; design record ADD-025, component decision ADR-0015. `SI-ATTACH` is its only runtime client.
- `U-OBJ-Preflight` — Compose service `object-store-preflight`: rejects unset, empty, default or short keys before the store starts (SR-040 AC 2), and an SSE key that is unset, a placeholder, not base64 of exactly 32 bytes, or equal to `AT_REST_ENCRYPTION_KEY` or a retired field key (SR-041 AC 5). It is the only Python service that receives `OBJECT_STORE_SSE_KEY`.
- `U-OBJ-Server` — Compose service `object-store`: SeaweedFS pinned by digest, no console, SSE-S3 key from its own setting `OBJECT_STORE_SSE_KEY` (never the field key, SR-041 AC 5; the key belongs to the volume), joined only to the `object-store` network (SR-040 AC 1, AC 3, SR-022).
- `U-OBJ-Init` — Compose service `object-store-init` (`backend/app/core/object_store_init.py`, boto3): creates the bucket, sets AES256 default encryption, verifies it, checks no policy (SR-040 AC 4, SR-022 AC 4).

### SI-AUDIT
- `U-AUD-Writer` — append-only event writer (actor/action/target/outcome/ts/source address), no plaintext secrets (SR-023). Records the originating client address of the request when the caller passes none, and none outside a request (SR-023 AC 6). Takes typed fields only (SR-023 AC 9): `action` must be an `AuditAction`, `target_type` one of a closed set, and `target_id` the shape of its target type; anything else raises `AuditFieldError` before any row is written (shapes in section 8.4). A module key as a `target_id` is checked against the one pattern in `backend/app/core/module_key.py`, shared with module discovery. Runs under the runtime database role, which has only `SELECT` and `INSERT` on `audit_log` (section 8.4, [ADR-0017](adr/0017-database-roles-and-append-only-audit-log.md)).

### SI-MODHOST
- `U-MH-Discovery` — entry-point discovery & `ModuleManifest` validation (SR-016). A manifest is accepted only with a `module_key` of the shape in `backend/app/core/module_key.py` (`^[a-z][a-z0-9_-]{0,63}$`), a non-empty name, a complete semantic version and a list of required permissions. A rejected manifest is logged at WARNING and skipped, but the registry sync then deletes the row of every module no longer discovered; with a group enablement row that delete hits a foreign key and the backend does not start (PRB-075; section 11).
- `U-MH-PlatformServices` — `PlatformServices` facade injected into modules (SR-016.3).
- `U-MH-RouterMount` — mount module routers under `/api/v1/modules/{key}` (SR-016).

### SI-MOD-DICOM-BE
- `U-DICOMBE-Studies` — authorized DICOM byte/frame endpoint via platform services (SR-016, SR-017).

### SI-PERSIST
- `U-PER-Models` — SQLAlchemy ORM models (FHIR-aligned, SR-021).
- `U-PER-Repos` — repositories with parameterized queries (SR-031.1).
- `U-PER-Migrations` — Alembic migrations (NFR-006). Run only by the `db-migrate` service, as the owner role. Migration 0009 drops the `audit_log` rules of 0006; migration 0010 converts existing field values to the identified envelope in one transaction (SR-022 AC 7).
- `U-PER-Crypto` — field encryption (`backend/app/db/crypto.py`, `EncryptedString` in `backend/app/db/types.py`): AES-256-GCM envelope `mh1:<key-id>:<base64url(nonce || ciphertext)>` with the prefix as associated data. A keyring holds the current key (`AT_REST_ENCRYPTION_KEY` under `AT_REST_ENCRYPTION_KEY_ID`) and optional retired keys (decryption only). `decrypt` uses the key named in the prefix only: no prefix, an unknown id or a failed tag raises, with no fallback to another key. `decrypt_legacy` reads the pre-0010 format and exists for the migration. The rotation command `python -m app.db.reencrypt` (`--check`, `--apply`, `--verify-key-ids`; `backend/app/db/reencrypt.py`) runs as the owner from the `db-migrate` image and covers every `EncryptedString` column (SR-022 AC 6 to AC 8, [ADR-0018](adr/0018-field-encryption-key-identifier-and-key-separation.md)).
- `U-PER-Roles` — `backend/app/db/roles.py` (`python -m app.db.roles`): creates the unprivileged runtime role named in `DATABASE_URL` and grants it the statements the application needs on every table, withholding `UPDATE`, `DELETE` and `TRUNCATE` on `audit_log`. Idempotent: a table added by a later migration is granted by the next run. It refuses an existing runtime role that is a superuser, a member of another role or an owner of objects (SR-023 AC 8, [ADR-0017](adr/0017-database-roles-and-append-only-audit-log.md)).

### SI-WORKER
- `U-WK-Email` — render & send activation/appointment emails via SMTP (SR-033, SR-035).
- `U-WK-SessionRevoke` — propagate deactivation session-kill within 30s (SR-034.2).
- `U-WK-RetentionErase` — scheduled job that permanently erases anonymized datasets past their 5-year retention deadline (SR-024.4, ADR-0013). It runs in the `celery-beat` service on `RETENTION_SWEEP_CRON`; exactly one beat must run. Before PRB-061 was fixed nothing ran the schedule.
- Logging — the worker and beat install the same JSON formatter and redaction filter as the API through Celery's logging signals, honour `--loglevel`, and replace `argsrepr`/`kwargsrepr` in debug task headers (SR-043 AC 2, AC 4). Tasks are sent with `task_ignore_result=True`, so `.delay()` fails fast when Redis is unreachable. Both services run the secret-setting rule on start (`worker_init`, `beat_init`).

### SI-FE-SHELL
- `U-FE-Layout` — responsive layout/breakpoints (SR-020).
- `U-FE-Nav` — consistent navigation/terminology (SR-027.1).
- `U-FE-Confirm` — confirmation dialogs for destructive actions (SR-027.2).
- `U-FE-Error` — clear, actionable error surfaces (SR-027.3).
- `U-FE-RouteGuard` — `RequireRole` route wrapper: a route whose role list does not contain the signed-in user's role is not mounted and redirects to `/profile`. The role table is `frontend/src/core/nav/routeRoles.ts`; `navConfig.ts` derives its role lists from it, so the two cannot diverge, and every `<Route>` in `App.tsx` has an entry. Defence in depth only: the server stays the control (SR-005, SR-009, SR-031 AC 5).

### SI-FE-AUTH
- `U-FEA-LoginForm`, `U-FEA-Activation`, `U-FEA-PasswordForm`, `U-FEA-IdleWarning` (SR-002, SR-025, SR-030.4, SR-033).

### SI-FE-CORE
- `U-FEC-Profile`, `U-FEC-Patients`, `U-FEC-ClinicalEntries`, `U-FEC-Appointments`, `U-FEC-Consent`, `U-FEC-AdminAccounts`, `U-FEC-AdminGroupsModules`.

### SI-FE-MODREG
- `U-FEM-Registry` — module registry + lazy import (SR-016).
- `U-FEM-NavGate` — render nav only if enabled per `GET /me/modules` (SR-015).

### SI-MOD-DICOM-FE
- `U-DICOMFE-Viewport` — Cornerstone3D init, parse, LUT, slice ordering, default W/L (SR-017).
- `U-DICOMFE-Controls` — window/level, zoom, pan, slice navigation (SR-018).

### SI-FE-APICLIENT
- `U-FEAPI-Client` — hand-written typed client over `fetch` (types generated by `openapi-typescript`);
  cookie/CSRF handling (SR-031.3); RFC 7807 errors.

### SI-DEPLOY
Deployment definition shipped with the product, apart from the object store (SI-OBJSTORE). Design record ADD-026; narrative in [07 deployment view](07-deployment-view.md) and sections 8.3 and 8.11.
- `U-DEP-Compose` — `infra/docker-compose.yml`: every secret setting passed with a `:?` guard and no default (SR-041 AC 2); no `env_file`, each service lists the settings it reads; the `medhub` network with a fixed subnet and `ip_range`, the reverse proxy at a fixed address and `TRUSTED_PROXIES` set to it (SR-042 AC 3, ADR-0019); the one-shot `db-migrate` service that `backend`, `celery-worker` and `celery-beat` wait for (ADR-0017); the `celery-worker` and `celery-beat` services run their own `command:` through the image entrypoint, which ends in `exec "$@"` (PRB-061).
- `U-DEP-SecretRule` — `backend/app/core/secret_settings.py`: one rule for every secret setting (unset, empty, a known placeholder in any case, a `change-me-to-…` value, any value the template ever shipped; field and SSE keys decode to 32 bytes and differ; `SMTP_PASSWORD` required only when `SMTP_USER` is set). Called by the API at start-up, by the worker and beat on start, by `db-migrate` and by the preflight; messages name the setting, never the value (SR-041 AC 3, AC 5).
- `U-DEP-EnvTemplate` — `infra/.env.example` with no value for any secret, and `infra/DEPLOY.md` stating how to generate each one (SR-041 AC 4).
- `U-DEP-DbRoles` — the owner role used only by `db-migrate` (`DATABASE_OWNER_URL`) and the runtime role used by `backend`, `celery-worker` and `celery-beat` (`DATABASE_URL`); the grants are `U-PER-Roles` (SR-023 AC 8).
- `U-DEP-RuntimeUsers` — `backend/Dockerfile` (`USER medhub`) and `frontend/Dockerfile` (nginx master and workers as the unprivileged `nginx` user on port 8080). The pulled images (reverse proxy, PostgreSQL, Redis, SeaweedFS) are not built by MedHub and are outside SR-041 AC 1; the reverse proxy's master runs as UID 0 (section 11).
- `U-DEP-ProxyLogging` — `infra/reverse-proxy/nginx.conf` and `frontend/nginx.conf`: an allow-list JSON access log with the activation paths redacted, `crit`-only error logs on the activation locations, `Referrer-Policy: no-referrer` on the activation page, no access log in the frontend container (SR-043 AC 4).

## Development and verification infrastructure (not deployed)

`SI-DEVINFRA` — the CI pipeline (`.github/workflows/ci.yml`), the toolchain configuration and lock
files, and the OpenAPI contract export. It is part of the repository and gates every merge, but it
is not deployed and no runtime item depends on it. Units: `U-INF-CIPipeline`, `U-INF-Toolchain`,
`U-INF-ContractExport` (SR-028). Design record: ADD-024. `U-INF-CIPipeline` includes the job
`object-store-integration`, which runs the encryption checks against the real object store.

## Module boundary note

Items `SI-MOD-DICOM-BE` and `SI-MOD-DICOM-FE` are **modules** added through the plugin mechanism (SI-MODHOST / SI-FE-MODREG). They demonstrate SR-016: they are separate packages, touch PHI only via `PlatformServices`, and require no edits to other items. Future modules follow the same shape.
