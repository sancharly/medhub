# 08 - Cross-cutting Concepts

Concepts that span multiple building blocks. They are implemented once (as central services or middleware) and inherited by all items, including plugin modules.

## 8.1 Domain model (FHIR-aligned)

The core entities and their FHIR R4 alignment are defined in [`../specifications/diagram-domain-model.puml`](../specifications/diagram-domain-model.puml) and [`../specifications/fhir-mapping.md`](../specifications/fhir-mapping.md) (SR-021, NFR-002). Persistence is relational PostgreSQL (ADR-0004) with JSONB for FHIR extension fields.

## 8.2 Authorization & consent

Single deny-by-default `AuthorizationService` (SI-AUTHZ) invoked on every request via DI (SR-005). Consent is modeled as **per-source `ConsentGrant`** rows; effective access = union of active grants (SR-008, SR-036). Doctor access to clinical data is governed **solely** by these grants — manual (SR-008) plus confirmed-appointment-derived (SR-036); there is **no explicit care-team/care-relationship entity** (resolved, see [ADR-0006](adr/0006-authz-consent-model.md)). Admin personnel get a non-clinical field projection (SR-009). Module access additionally passes `ModuleAccessGuard` (SR-015).

## 8.3 Security (defense-in-depth)

See [ADR-0011](adr/0011-security-compliance-approach.md). Layers:

- **Transport:** TLS at the proxy, HSTS, HTTP→HTTPS redirect (SR-001, SR-022).
- **At rest:** object-store SSE + encrypted DB volume (SR-022; SR-013.4).
- **Credentials:** Argon2id hashing (SR-002.4); server-side password policy with history/age (SR-025); lockout (SR-029).
- **Sessions:** server-side opaque tokens, role timeouts, absolute lifetime, concurrency cap, hardened cookies (SR-030, [ADR-0012](adr/0012-authentication-session-mechanism.md)).
- **Web vulnerabilities:** one security middleware sets CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`; CSRF via SameSite + tokens; ORM-only parameterized queries; SPA output encoding (SR-031). Access control enforced server-side always (SR-031.5, CV-04).
- **Review gate:** auth/session code requires a documented security review before merge (SR-031.6).

## 8.4 Audit logging

Central append-only `AuditService` (SI-AUDIT) records authentication, clinical-data access, consent changes, and administrative actions with actor/action/target/outcome/timestamp; no plaintext credentials; not modifiable by ordinary users (SR-023). Audit calls are side effects of operations, not a public endpoint.

## 8.5 Data-subject rights & retention

Erasure/anonymization (SI-IDENTITY `U-ID-Erasure`) implements the now-decided retention policy; clinical records are anonymized rather than silently deleted (SR-024, SR-034.5). Patient self-access and consent control realize GDPR rights (SR-007, SR-008). See [ADR-0013](adr/0013-account-deletion-anonymized-retention.md).

**Deletion → 5-year anonymized retention with a user-held code (ADR-0013):** on account deletion (SR-034.5 / SR-024), credentials and PII are severed from the record data and the user's data is retained in **anonymized** form for **5 years**, after which a scheduled `SI-WORKER` job **permanently erases** it. At deletion time a high-entropy **anonymization code** is generated and sent to the user (email); with it the user can retrieve their own anonymized dataset at any time within the 5 years. The code is **never stored** in any recoverable form — only a salted KDF hash (Argon2id, consistent with credential handling, ADR-0011) is kept to *locate-and-authorize* retrieval; the code never appears in the DB, logs, or audit records. **Trade-off (by design):** losing the code makes the dataset unrecoverable — there is no recovery path, which is the intended privacy property (the operator cannot re-identify or surrender the data subject's dataset without the data subject's code).

## 8.6 Validation & error handling

- Server-side validation via Pydantic at the API boundary is authoritative (password policy, required fields, references). Client validation is convenience only (SR-025, SR-031.5).
- Errors are RFC 7807 `application/problem+json` with stable `type` URIs and field-level `errors[]`; the SPA surfaces clear, actionable messages (SR-027.3, api-design.md).

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

Twelve-factor style configuration via environment; secrets injected at deploy time, never committed; per-deployment signing keys and crypto keys managed by the operator (ADR-0010, ADR-0011). **Hosting region / data residency is a deployment-time configuration choice** — no region is hard-coded and no non-EU-only managed service is required, so the operator can host EU-only to meet GDPR data-residency obligations; the architecture imposes no obstacle to this (NFR-004, ADR-0010).

## 8.12 Notification delivery (best-effort MVP, extensible)

Notifications (appointment in-app + email, activation email) are dispatched **best-effort** for the MVP: the system sends and relies on Celery retries (section 11), but performs **no delivery- or read-tracking / acknowledgement** (SR-035 requires sending, not delivery proof). To avoid later rework, notification dispatch is funneled through a single `Notification` abstraction (created by `U-APPT-Notify` / `U-WK-Email`) that carries a **`status` field and a post-send hook**; the MVP only sets `status` to `QUEUED`/`SENT`/`FAILED`, but the same field and hook are the clean extension point where delivery receipts, read tracking, or acknowledgement can later be recorded **without changing callers** (SR-035). This is a documented, deliberate MVP scope (resolved open question, section 11).
