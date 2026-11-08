# 08 - Cross-cutting Concepts

Concepts that span multiple building blocks. They are implemented once (as central services or middleware) and inherited by all items, including plugin modules.

## 8.1 Domain model (FHIR-aligned)

The core entities and their FHIR R4 alignment are defined in [`../specifications/diagram-domain-model.puml`](../specifications/diagram-domain-model.puml) and [`../specifications/fhir-mapping.md`](../specifications/fhir-mapping.md) (SR-021, NFR-002). Persistence is relational PostgreSQL (ADR-0004) with JSONB for FHIR extension fields.

## 8.2 Authorization & consent

Single deny-by-default `AuthorizationService` (SI-AUTHZ) invoked on every request via DI (SR-005). Consent is modeled as **per-source `ConsentGrant`** rows; effective access = union of active grants (SR-008, SR-036). Doctor access to clinical data is governed **solely** by these grants — manual (SR-008) plus confirmed-appointment-derived (SR-036); there is **no explicit care-team/care-relationship entity** (resolved, see [ADR-0006](adr/0006-authz-consent-model.md)). Admin personnel get a non-clinical field projection (SR-009). Module access additionally passes `ModuleAccessGuard` (SR-015).

**One decision point, every decision audited (SR-005, SR-023 AC 7; CR-004).** `AuthorizationService.decide()` (`U-AUTHZ-Policy`) is the only place an access decision is taken. It covers clinical and appointment access, module access, the account lifecycle (create, deactivate, reactivate, delete, activation resend, unlock), and the consent and patient-roster routes. Each decision returns an allow flag and a basis, and is audited with actor, action, target, outcome and source address, allowed or denied; a refusal that the contract answers with 404 is still audited as `AUTHZ_DENIED`. Services and routers ask; they do not compare a role. A static test fails when a role comparison that decides access appears outside `backend/app/authz/`. Its stated limits are `getattr` dispatch on a role and `self.<attr>` aliases (PRB-027). The frontend route guard (`routeRoles.ts`, `RequireRole`) is defence in depth only; the server stays the control (SR-031 AC 5). Known gap: an allowed decision's audit row is rolled back when the request later fails (PRB-060, open; the independent-transaction rule of section 8.4 covers refusals and failures only).

## 8.3 Security (defense-in-depth)

See [ADR-0011](adr/0011-security-compliance-approach.md). Layers:

- **Transport:** TLS at the proxy, HSTS, HTTP→HTTPS redirect (SR-001, SR-022).
- **At rest:** object-store SSE + encrypted DB volume + field-level AES-256-GCM on `clinical_entry.description` (SR-022; SR-013.4). Two separate keys: `AT_REST_ENCRYPTION_KEY` for field values and `OBJECT_STORE_SSE_KEY` for the object store, refused when equal (SR-041 AC 5, [ADR-0018](adr/0018-field-encryption-key-identifier-and-key-separation.md)). Each field value names its key (`mh1:<key id>:...`), which makes a rehearsed rotation possible (section 11 for what a lost key means).
- **Secrets at start-up:** one rule (`U-DEP-SecretRule`) refuses an unset, empty or placeholder secret, a field or SSE key that is not 32 bytes, and equal keys, in the API, the worker, beat, `db-migrate` and the object-store preflight; Compose also has no default for a secret (SR-041). The Celery services refuse on `worker_init`/`beat_init`.
- **Least privilege:** the application connects as a runtime database role that cannot `UPDATE`, `DELETE` or `TRUNCATE` `audit_log`; the owner credential exists only in `db-migrate` ([ADR-0017](adr/0017-database-roles-and-append-only-audit-log.md)). Application images run as an unprivileged user (`medhub`, `nginx` on 8080). The official reverse-proxy image runs its master as UID 0 (section 11).
- **Credentials:** Argon2id hashing (SR-002.4); server-side password policy with history/age (SR-025); lockout (SR-029).
- **Sessions:** server-side opaque tokens, role timeouts, absolute lifetime, concurrency cap, hardened cookies (SR-030, [ADR-0012](adr/0012-authentication-session-mechanism.md)).
- **Web vulnerabilities:** one security middleware sets CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`; CSRF via SameSite + tokens, with exemptions limited to an exact set of no-session paths (login, anonymized retrieval, health and contract probes, and the activation `POST` matched as one path segment) reviewed by a route-inventory test (SR-031 AC 3); ORM-only parameterized queries; SPA output encoding (SR-031). Access control enforced server-side always (SR-031.5, CV-04).
- **Review gate:** auth/session code requires a documented security review before merge (SR-031.6).

## 8.4 Audit logging

Central append-only `AuditService` (SI-AUDIT) records authentication, clinical-data access, consent changes, and administrative actions with actor/action/target/outcome/timestamp and source address; no plaintext credentials; not modifiable by ordinary users (SR-023).

- **Source address (SR-023 AC 6, [ADR-0019](adr/0019-originating-client-address-trusted-proxy-rule.md)):** `U-API-ClientAddress` computes the originating client address once per request (the TCP peer, or the right-most untrusted `X-Forwarded-For` entry when the peer is in `TRUSTED_PROXIES`) and the writer records it when the caller passes none. Outside a request (a Celery task) there is no address. The writer does not validate the address; the rule that derives it is the control.
- **Append-only by privilege (SR-023 AC 8, [ADR-0017](adr/0017-database-roles-and-append-only-audit-log.md)):** the runtime role has `SELECT` and `INSERT` on `audit_log`; `UPDATE`, `DELETE` and `TRUNCATE` fail with a permission error. Database rules are not used (migration 0009 drops those of 0006). Direct SQL by the owner is not audited.
- **Typed fields (SR-023 AC 9):** the writer refuses, with `AuditFieldError` before any row is written, a value outside these shapes, so no secret can be stored under any field: `action` is a member of `AuditAction`; `target_type` is one of a closed set; `target_id` must have the shape of its `target_type`: none; one UUID (account, appointment, attachment, clinical entry, consent, consent grant, group, patient roster, anonymized dataset); `<uuid>:<uuid>` (group membership); `<uuid>:<module key>` (group module); a bare module key (module); `user_type:<UserType>` (account creation); an empty string (a decision with no resource id); no id (module registry). A module key has the shape `^[a-z][a-z0-9_-]{0,63}$` and nothing more (shape only, no registry lookup), defined once in `backend/app/core/module_key.py` and shared with module discovery, which rejects a non-matching manifest. `ip` is derived by the ADR-0019 rule and not validated by the writer. The pattern scrub of credential-like `key=value` text stays as a second line. The failed-login counter is incremented before the audit write, so a refused write cannot skip the count. Audit calls are side effects of operations, not a public endpoint. Events that record a failure or a refusal (outcome FAILURE, and `ACCOUNT_LOCKOUT`) are committed on their own short-lived transaction so they survive a request that ends in an error, while other events stay in the request transaction ([ADR-0016](adr/0016-failure-audit-events-on-own-transaction.md)).

## 8.5 Data-subject rights & retention

Erasure/anonymization (SI-IDENTITY `U-ID-Erasure`) implements the now-decided retention policy; clinical records are anonymized rather than silently deleted (SR-024, SR-034.5). Patient self-access and consent control realize GDPR rights (SR-007, SR-008). See [ADR-0013](adr/0013-account-deletion-anonymized-retention.md).

**Deletion → 5-year anonymized retention with a user-held code (ADR-0013):** on account deletion (SR-034.5 / SR-024), credentials and PII are severed from the record data and the user's data is retained in **anonymized** form for **5 years**, after which a scheduled `SI-WORKER` job **permanently erases** it. At deletion time a high-entropy **anonymization code** is generated and sent to the user (email); with it the user can retrieve their own anonymized dataset at any time within the 5 years. The code is **never stored** in any recoverable form — only a salted KDF hash (Argon2id, consistent with credential handling, ADR-0011) is kept to *locate-and-authorize* retrieval; the code never appears in the DB, logs, or audit records. **Trade-off (by design):** losing the code makes the dataset unrecoverable — there is no recovery path, which is the intended privacy property (the operator cannot re-identify or surrender the data subject's dataset without the data subject's code).

## 8.6 Validation & error handling

- Server-side validation via Pydantic at the API boundary is authoritative (password policy, required fields, references). Client validation is convenience only (SR-025, SR-031.5).
- Errors are RFC 7807 `application/problem+json` with stable `type` URIs and field-level `errors[]`; the SPA surfaces clear, actionable messages (SR-027.3, api-design.md). Two problems were added by CR-004: `503` `session-cap-contention` with `Retry-After: 1`, and `400` `validation-error` with the rule `filename_max_bytes` for an attachment name over 255 UTF-8 bytes (section 12). The 500 handler logs the matched route template, never the raw path.

## 8.7 Module/plugin concept

Two-sided Module Contract (backend entry points + `ModuleManifest`; frontend registry + lazy chunks). Modules access PHI only via `PlatformServices`, preserving the AuthZ choke point and audit (SR-016). See [ADR-0005](adr/0005-plugin-module-mechanism.md).

## 8.8 Responsiveness, cross-browser & usability

- Responsive layout with phone/tablet/desktop breakpoints, adequate touch targets, no horizontal scroll of primary content (SR-020, NFR-003).
- Standards-based web tech (ES2020, fetch, WebGL); no browser-proprietary APIs without fallback → works on Safari/Firefox/Chrome/Edge (SR-019); documented cross-browser test pass per release.
- Consistent navigation/terminology, confirmation on destructive actions, clear errors → minimal-training usability (SR-027, NFR-009).

## 8.9 Performance

Performance budgets (routine ops <3 s, DICOM initial render <10 s) met by: object storage off the DB path, client-side DICOM rendering, lazy module chunks, indexed consent/authorization queries, and deferring heavy work (uploads, full volumetric load) so initial interaction stays responsive (SR-026, NFR-008).

## 8.10 Internationalization & accessibility (baseline)

English MVP with i18n-ready string handling in the SPA; accessible component library for adequate contrast/target size supporting usability and responsive goals (NFR-003, NFR-009). Full i18n and formal accessibility audit are post-MVP.

## 8.11 Configuration & secrets

Twelve-factor style configuration via environment; secrets injected at deploy time, never committed; per-deployment crypto keys managed by the operator (ADR-0010, ADR-0011). There is no session signing key (PRB-018): sessions are opaque random tokens held in Redis, and a leftover `SESSION_SIGNING_KEY` in an existing `.env` is ignored.

**Secret settings (SR-041; `backend/app/core/secret_settings.py`, `infra/DEPLOY.md` "Secret settings").** `POSTGRES_PASSWORD`, `DATABASE_OWNER_URL` (`db-migrate` only), `DATABASE_URL` (runtime role, a different password), `OBJECT_STORE_ACCESS_KEY`, `OBJECT_STORE_SECRET_KEY`, `OBJECT_STORE_SSE_KEY` (object store and preflight only), `AT_REST_ENCRYPTION_KEY`, `AT_REST_ENCRYPTION_RETIRED_KEYS` (optional, decryption only) and `SMTP_PASSWORD` (only when `SMTP_USER` is set). `AT_REST_ENCRYPTION_KEY_ID` is required but not secret. `TRUSTED_PROXIES` is not secret and is fixed in the Compose file. The template holds no secret value, Compose has no default, and the application refuses placeholders (section 8.3). Each service receives only the settings it reads.

**Field-key rotation and key separation (SR-022 AC 6 to AC 8, [ADR-0018](adr/0018-field-encryption-key-identifier-and-key-separation.md)).** The field key rotates without making a stored value unreadable: new key current, old key retired, `python -m app.db.reencrypt --apply`, then the old key is dropped when `--check` shows no value under its id (section 6.10). The SSE key does not rotate in place; it changes by a checked copy to a new volume (section 6.11). A lost key is unrecoverable and there is still no backup and restore procedure (PRB-057, section 11). **Hosting region / data residency is a deployment-time configuration choice** — no region is hard-coded and no non-EU-only managed service is required, so the operator can host EU-only to meet GDPR data-residency obligations; the architecture imposes no obstacle to this (NFR-004, ADR-0010).

## 8.12 Notification delivery (best-effort MVP, extensible)

Notifications (appointment in-app + email, activation email) are dispatched **best-effort** for the MVP: the system sends and relies on Celery retries (section 11), but performs **no delivery- or read-tracking / acknowledgement** (SR-035 requires sending, not delivery proof). To avoid later rework, notification dispatch is funneled through a single `Notification` abstraction (created by `U-APPT-Notify` / `U-WK-Email`) that carries a **`status` field and a post-send hook**; the MVP only sets `status` to `QUEUED`/`SENT`/`FAILED`, but the same field and hook are the clean extension point where delivery receipts, read tracking, or acknowledgement can later be recorded **without changing callers** (SR-035). This is a documented, deliberate MVP scope (resolved open question, section 11).

## 8.13 Visual design tokens & theming

The frontend's entire visual appearance (color, typography, spacing, radii, elevation) is defined by a **single design-token foundation** in `frontend/src/core/theme/` and applied globally through MUI theme component overrides; screens never hard-code visual values (SR-037). **Light and dark modes** are two value sets over the same token structure via MUI CSS-variables `colorSchemes`, both verified against WCAG 2.1 AA contrast (SR-038). A chrome-visible toggle defaults to the OS color-scheme preference and persists the explicit choice client-side in `localStorage` — presentational only, no PHI, no backend involvement (SR-039). Mechanism: ADR-0014; token values and contrast evidence: design record ADD-001 (`docs/design-outputs/architecture/`).

## 8.14 Logging and redaction (SR-043)

One JSON formatter and one redaction filter (`backend/app/core/logging.py`) are installed by the API process (lifespan) and by the Celery worker and beat (through Celery's logging signals, on every handler, honouring `--loglevel`). The filter replaces email-shaped values in the message and in every structured field before a record is emitted, so debug records are redacted too. Log calls name accounts and patients by identifier only. Further rules, by where a credential could appear:

- **API 500 record:** names the matched route template (for example `/api/v1/activation/{token}`), never the raw request path (SR-043 AC 4).
- **Celery:** `argsrepr`/`kwargsrepr` in debug task headers, which hold the activation token, are replaced. The task arguments themselves still pass the Redis broker in plaintext (PRB-074, open).
- **Reverse proxy:** an allow-list JSON access log with the normalised path, no request line, query string or header; `[redacted]` replaces the token in the two activation paths, matched without case (`~*`) because the application is case-insensitive. The activation locations log errors at `crit` only and the activation page sends `Referrer-Policy: no-referrer`. The frontend container logs no access.
- **Backend access log:** no option enables one in the image or in Compose.
- **Residual (human decision CR-004 D-19):** a hand-crafted `Referer` that carries a token, or a token in the query string of another path, sent to a non-activation location during an upstream failure or a 413, is written to the proxy error log (SR-043 AC 4). No MedHub URL or browser flow produces it. It is listed in section 11 for the release evaluation.
- **Module discovery:** a rejected manifest is logged at WARNING with the first 80 characters of the offending value, never the whole manifest.
- **Verification by hand:** `infra/log-secrets-check.sh` exercises activation, an erasure and a retrieval against a started stack and searches the logs for the secrets of `infra/.env`.
