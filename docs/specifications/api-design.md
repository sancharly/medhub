# MedHub API & Interface Design

Produced with the **api-designer** skill. Defines the external HTTP interface (SPA ↔ backend) and the internal module-contract interface. The authoritative machine-readable contract is the FastAPI-generated **OpenAPI 3.1** document at `/api/v1/openapi.json`; this document specifies the design that contract must satisfy.

## Conventions

- Base path: `/api/v1` (URI versioning; breaking changes → `/v2`).
- JSON, `camelCase` field names in DTOs (FHIR-traceable per `fhir-mapping.md`).
- Resource-oriented URIs, correct HTTP verbs, no verbs in paths.
- AuthN: opaque session cookie (`Secure; HttpOnly; SameSite=Strict`) — ADR-0012. No bearer tokens for the SPA.
- AuthZ: every endpoint passes the central `AuthorizationService` dependency (SR-005); deny-by-default.
- Errors: **RFC 7807** `application/problem+json` with stable `type` URIs and field-level `errors[]`.
- Collections paginated (cursor or page/limit) and access-scoped.
- All state-changing requests CSRF-protected (SameSite + token, SR-031).

## Error catalog (RFC 7807 `type` URIs)

| Status | type URI suffix            | Used for                                                                  |
|--------|----------------------------|---------------------------------------------------------------------------|
| 400    | `/errors/validation-error` | malformed/missing fields (SR-010, SR-012, SR-025, SR-032)                 |
| 401    | `/errors/unauthenticated`  | no/invalid session (SR-002, SR-005) — generic, no field disclosure        |
| 403    | `/errors/forbidden`        | authorization denied (SR-005, SR-006, SR-009, SR-015) — no protected data |
| 404    | `/errors/not-found`        | resource absent or not visible to caller                                  |
| 409    | `/errors/conflict`         | duplicate email (SR-032.3), invalid state transition                      |
| 423    | `/errors/account-locked`   | surfaced generically as 401 during login (SR-029.6)                       |
| 429    | `/errors/rate-limited`     | throttling                                                                |

## Core endpoints

### Authentication & session (SI-AUTH)

| Method & path               | Purpose                                    | Key reqs               |
|-----------------------------|--------------------------------------------|------------------------|
| `POST /auth/login`          | email+password → session cookie            | SR-002, SR-029, SR-030 |
| `POST /auth/logout`         | invalidate server-side session immediately | SR-030.5               |
| `POST /auth/session/extend` | reset inactivity timer                     | SR-030.4               |
| `GET /me`                   | current user profile                       | SR-003                 |
| `GET /me/modules`           | modules enabled for the user's groups      | SR-015, SR-016.2       |
| `POST /auth/password`       | change password (policy + history)         | SR-025                 |

### Account activation (SI-IDENTITY)

| Method & path              | Purpose                     | Key reqs     |
|----------------------------|-----------------------------|--------------|
| `GET /activation/{token}`  | validate activation token   | SR-033.2     |
| `POST /activation/{token}` | set password (x2), activate | SR-033.3/4/5 |

### Identity & account lifecycle (SI-IDENTITY) — admin/sysadmin only

| Method & path                           | Purpose                                                                                      | Key reqs                     |
|-----------------------------------------|----------------------------------------------------------------------------------------------|------------------------------|
| `POST /accounts`                        | create account (role-constrained), triggers activation email                                 | SR-032, SR-033.1             |
| `GET /accounts`                         | list (non-clinical projection for admin)                                                     | SR-009                       |
| `GET /accounts/{id}`                    | view account                                                                                 | SR-003, SR-009               |
| `POST /accounts/{id}/deactivate`        | deactivate (sysadmin), kills sessions ≤30s                                                   | SR-034.1/2                   |
| `POST /accounts/{id}/reactivate`        | reactivate                                                                                   | SR-034.4                     |
| `DELETE /accounts/{id}`                 | delete → anonymize into 5-year retained dataset; emails user a retrieval code (confirm step) | SR-034.5/6, SR-024, ADR-0013 |
| `POST /accounts/{id}/resend-activation` | new single-use link                                                                          | SR-033.7                     |

### Anonymized-dataset retrieval (SI-IDENTITY) — code-authorized, no account/session

| Method & path                    | Purpose                                                                                                                                                                           | Key reqs         |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|
| `POST /anonymized-data/retrieve` | retrieve a deleted user's retained anonymized dataset; body carries the user-held anonymization code (matched against a stored salted hash, never the code); valid within 5 years | SR-024, ADR-0013 |

> The anonymization code is held only by the user and is **never stored** in recoverable form; a lost code makes the dataset unrecoverable by design. Retrieval is audited; expired (>5y) datasets are erased by a scheduled worker job (SR-024.4).

### Groups & module enablement (SI-GROUPS) — sysadmin only

| Method & path                                                  | Purpose                         | Key reqs |
|----------------------------------------------------------------|---------------------------------|----------|
| `POST /groups`, `GET /groups`                                  | create/list groups              | SR-014   |
| `POST /groups/{id}/members` / `DELETE .../members/{accountId}` | manual membership               | SR-014.3 |
| `PUT /groups/{id}/modules/{moduleKey}`                         | enable/disable module for group | SR-015   |
| `GET /modules`                                                 | installed module registry       | SR-016   |

### Appointments & confirmation (SI-APPT)

| Method & path                     | Purpose                                               | Key reqs             |
|-----------------------------------|-------------------------------------------------------|----------------------|
| `POST /appointments`              | create (doctor, patient, datetime) → PENDING + notify | SR-010, SR-035.1/2   |
| `GET /appointments`               | list, scoped to caller (own/admin)                    | SR-011               |
| `POST /appointments/{id}/confirm` | patient only → CONFIRMED + grant consent              | SR-035.5/9, SR-036.1 |
| `POST /appointments/{id}/decline` | patient only → DECLINED + revoke that grant           | SR-035.6/7, SR-036.4 |

### Clinical records & attachments (SI-CLINICAL, SI-ATTACH)

| Method & path                             | Purpose                                    | Key reqs                 |
|-------------------------------------------|--------------------------------------------|--------------------------|
| `GET /patients/{id}/clinical-entries`     | list patient history (authz)               | SR-006, SR-007           |
| `POST /patients/{id}/clinical-entries`    | doctor creates entry (author from session) | SR-012                   |
| `POST /clinical-entries/{id}/attachments` | upload file (DICOM/report)                 | SR-013                   |
| `GET /attachments/{id}`                   | authorized download/stream                 | SR-005, SR-013.3, SR-022 |

### Consent (SI-AUTHZ)

| Method & path           | Purpose                                           | Key reqs   |
|-------------------------|---------------------------------------------------|------------|
| `POST /consents`        | patient grants a doctor (MANUAL)                  | SR-008.1   |
| `DELETE /consents/{id}` | patient revokes (immediate)                       | SR-008.3/4 |
| `GET /me/consents`      | unified view of all grants (manual + appointment) | SR-036.7   |

### Module endpoints (mounted by SI-MODHOST)

| Method & path                                      | Purpose                       | Key reqs                                         |
|----------------------------------------------------|-------------------------------|--------------------------------------------------|
| `GET /modules/dicom-viewer/studies/{attachmentId}` | authorized DICOM bytes/frames | SR-016, SR-017 (data via platform services only) |

> Audit (SR-023) and erasure (SR-024) are produced as side effects of the above endpoints and by admin operations; there is no separate "write audit" public endpoint (append-only, server-internal).

## Authentication & authorization flow

1. `POST /auth/login` → Argon2id verify → create Redis session → `Set-Cookie` (ADR-0012).
2. Every subsequent request: cookie → session lookup → `AuthorizationService.authorize(actor, action, resource)` (SR-005) → allow/deny.
3. Module endpoints additionally pass `ModuleAccessGuard` (group enablement, SR-015) before authorization.

## Internal interface — Module Contract (SI-MODHOST)

Backend module (Python package, `medhub.modules` entry point) provides a `ModuleManifest`:

```python
class ModuleManifest:
    module_key: str            # stable id, e.g. "dicom-viewer"
    name: str
    version: str
    required_permissions: list[str]
    def register(self, registry: RouterRegistry,
                 services: PlatformServices) -> None: ...
```

`PlatformServices` is the **only** way a module touches PHI, preserving the SR-005 choke point and SR-023 audit (SR-016.3):

```python
class PlatformServices:
    authorization: AuthorizationService   # authorize(actor, action, resource)
    clinical: ClinicalDataService         # read entries (authorized)
    attachments: AttachmentService        # fetch object bytes (authorized)
    audit: AuditService                   # append audit event
```

Frontend module registry entry (TypeScript):

```ts
interface FrontendModule {
  moduleKey: string;
  navItem: NavItem;
  lazyComponent: () => Promise<{ default: React.ComponentType }>; // code-split
}
```

The shell renders `navItem` only if `moduleKey` ∈ `GET /me/modules` (SR-015, SR-016.2).

## Versioning & evolution

- URI version `/v1`; additive changes are non-breaking; breaking changes → `/v2` with a documented deprecation window.
- `ModuleManifest.version` lets the host check module/platform compatibility.
- FHIR export/import (future) is an additive adapter (`/v1/fhir/...`) over the aligned model (`fhir-mapping.md`).

## Validation

The generated OpenAPI document is expected to pass `npx @redocly/cli lint` as part of CI before the contract is considered an approved interface specification (NFR-006 interface definition).
