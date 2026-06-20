# 05 - Building Block View (Software Items & Units)

This section is the **hierarchical decomposition into software items and software units** required by the software development plan (IEC 62304). The system (level 0) decomposes into software items (level 1); each item decomposes into software units (level 2) — the smallest pieces, each independently unit-testable. Where an item cannot be meaningfully decomposed further, the item *is* the unit.

Diagram: [`../specifications/diagram-building-blocks.puml`](../specifications/diagram-building-blocks.puml)

## Level 0 — System

**MedHub** = Frontend SPA + Backend (modular monolith) + supporting stores (PostgreSQL, Redis, Object storage) + Worker, deployed behind a TLS reverse proxy. Decomposed into the items below.

## Level 1 — Software items

| Item ID         | Name                           | Responsibility                                                                               | Key reqs                                       |
|-----------------|--------------------------------|----------------------------------------------------------------------------------------------|------------------------------------------------|
| SI-API          | API Layer / Routers            | HTTP endpoints, request/response DTOs, validation, error formatting, AuthZ dependency wiring | SR-001, all API SRs                            |
| SI-AUTH         | Authentication & Session       | Login, logout, password change, session lifecycle, lockout                                   | SR-002, SR-025, SR-029, SR-030                 |
| SI-AUTHZ        | Authorization & Consent        | Deny-by-default decisions; per-source consent grants; module access guard                    | SR-005–009, SR-011, SR-015, SR-036, SR-008     |
| SI-IDENTITY     | Identity & Account Lifecycle   | Account CRUD, role-constrained creation, activation, deactivate/reactivate/delete, erasure   | SR-003, SR-004, SR-024, SR-032, SR-033, SR-034 |
| SI-GROUPS       | Groups & Module Enablement     | Group CRUD, auto/manual membership, per-group module enablement                              | SR-014, SR-015                                 |
| SI-APPT         | Appointments & Notifications   | Appointment CRUD, state machine, confirmation, notification dispatch                         | SR-010, SR-011, SR-035                         |
| SI-CLINICAL     | Clinical Records               | Clinical-entry CRUD with required fields & attribution                                       | SR-012                                         |
| SI-ATTACH       | Attachment Service             | Upload/fetch attachment binaries via object storage, authorized                              | SR-013, SR-022                                 |
| SI-AUDIT        | Audit Service                  | Append-only audit log of security-relevant events                                            | SR-023                                         |
| SI-MODHOST      | Module Host / Plugin Registry  | Module discovery/registration, platform-service injection, router mounting                   | SR-016                                         |
| SI-MOD-DICOM-BE | DICOM Module (backend)         | Authorized DICOM byte/frame endpoints behind the module contract                             | SR-016, SR-017                                 |
| SI-PERSIST      | Persistence                    | SQLAlchemy models, repositories, Alembic migrations, encryption-at-rest config               | SR-021, SR-022                                 |
| SI-WORKER       | Async Worker                   | Celery tasks: send activation & appointment emails, session-revocation propagation           | SR-033, SR-035, SR-034                         |
| SI-FE-SHELL     | Frontend App Shell             | Layout, routing, responsive frame, navigation, module mounting, error/confirmation UX        | SR-019, SR-020, SR-027                         |
| SI-FE-AUTH      | Frontend Auth/Session UI       | Login, activation, password, inactivity warning/extend                                       | SR-002, SR-025, SR-030, SR-033                 |
| SI-FE-CORE      | Frontend Core Views            | Profile, patients, clinical entries, appointments, consent, admin (accounts/groups/modules)  | SR-003–016, SR-035, SR-036                     |
| SI-FE-MODREG    | Frontend Module Registry       | Dynamic module registration, gated nav, lazy chunk loading                                   | SR-015, SR-016                                 |
| SI-MOD-DICOM-FE | DICOM Viewer Module (frontend) | Cornerstone3D viewport, window/level, zoom, pan, slice nav                                   | SR-017, SR-018                                 |
| SI-FE-APICLIENT | Frontend API Client            | Typed client generated from OpenAPI; session/CSRF handling                                   | NFR-006, SR-031                                |

## Level 2 — Software units (per item)

### SI-API
- `U-API-Routers` — endpoint definitions per resource (auth, accounts, groups, appointments, clinical, attachments, consents, modules).
- `U-API-DTO` — Pydantic request/response schemas (camelCase, FHIR-traceable).
- `U-API-ErrorHandler` — RFC 7807 problem+json mapping (SR-027.3, api-design.md).
- `U-API-Deps` — DI providers: current session, current user, `authorize(...)` guard.

### SI-AUTH
- `U-AUTH-Login` — credential verification (Argon2id), generic failure (SR-002).
- `U-AUTH-Lockout` — failed-attempt counter, 5/30-min lock, admin unlock (SR-029).
- `U-AUTH-Session` — Redis session create/refresh/invalidate, role timeouts, absolute lifetime, concurrency cap (SR-030).
- `U-AUTH-PasswordPolicy` — server-side complexity, history(12), max-age(180d), reuse/username checks (SR-025).
- `U-AUTH-Cookie` — Secure/HttpOnly/SameSite=Strict cookie issuing (SR-030.6).

### SI-AUTHZ
- `U-AUTHZ-Policy` — deny-by-default decision engine (user type + relationship + consent + module) (SR-005).
- `U-AUTHZ-Consent` — `ConsentGrant` create/revoke, per-source union evaluation (SR-008, SR-036).
- `U-AUTHZ-AdminProjection` — non-clinical field projection for admin personnel (SR-009).
- `U-AUTHZ-ModuleGuard` — module-enabled-for-group check (SR-015).
- `U-AUTHZ-ApptVisibility` — appointment visibility scoping (SR-011).

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
- `U-ATT-Fetch` — authorized stream / scoped pre-signed URL (SR-005, SR-013.3).

### SI-AUDIT
- `U-AUD-Writer` — append-only event writer (actor/action/target/outcome/ts), no plaintext secrets (SR-023).

### SI-MODHOST
- `U-MH-Discovery` — entry-point discovery & `ModuleManifest` validation (SR-016).
- `U-MH-PlatformServices` — `PlatformServices` facade injected into modules (SR-016.3).
- `U-MH-RouterMount` — mount module routers under `/api/v1/modules/{key}` (SR-016).

### SI-MOD-DICOM-BE
- `U-DICOMBE-Studies` — authorized DICOM byte/frame endpoint via platform services (SR-016, SR-017).

### SI-PERSIST
- `U-PER-Models` — SQLAlchemy ORM models (FHIR-aligned, SR-021).
- `U-PER-Repos` — repositories with parameterized queries (SR-031.1).
- `U-PER-Migrations` — Alembic migrations (NFR-006).
- `U-PER-Crypto` — at-rest encryption config / pgcrypto where needed (SR-022).

### SI-WORKER
- `U-WK-Email` — render & send activation/appointment emails via SMTP (SR-033, SR-035).
- `U-WK-SessionRevoke` — propagate deactivation session-kill within 30s (SR-034.2).
- `U-WK-RetentionErase` — scheduled job that permanently erases anonymized datasets past their 5-year retention deadline (SR-024.4, ADR-0013).

### SI-FE-SHELL
- `U-FE-Layout` — responsive layout/breakpoints (SR-020).
- `U-FE-Nav` — consistent navigation/terminology (SR-027.1).
- `U-FE-Confirm` — confirmation dialogs for destructive actions (SR-027.2).
- `U-FE-Error` — clear, actionable error surfaces (SR-027.3).

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
- `U-FEAPI-Client` — generated typed client; cookie/CSRF handling (SR-031.3).

## Module boundary note

Items `SI-MOD-DICOM-BE` and `SI-MOD-DICOM-FE` are **modules** added through the plugin mechanism (SI-MODHOST / SI-FE-MODREG). They demonstrate SR-016: they are separate packages, touch PHI only via `PlatformServices`, and require no edits to other items. Future modules follow the same shape.
