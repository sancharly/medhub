# MedHub Implementation Plan

This folder breaks the approved MedHub architecture (`docs/design/`, `docs/specifications/`) into
small, ordered, self-contained tasks that the **Software Developer agent** can execute without
human intervention. Each task targets ~one software unit (`U-*` from
[05-building-blocks.md](../design/05-building-blocks.md)), cites the SR/NFR/ADR it satisfies, and is
intended to be one branch/PR per the [software-development-plan.md](../software-development-plan.md)
Git Flow.

- **Task template & shared conventions:** [TASK-TEMPLATE.md](TASK-TEMPLATE.md) — read this first; the
  stack, repo layout, TDD rule, deny-by-default authorization, RFC 7807 errors and audit conventions
  apply to every task and are **not** repeated in individual task files.
- **Architecture sources:** building blocks (05), runtime views (06), deployment (07), cross-cutting
  concepts (08), interfaces (12), ADRs (`adr/`), API design and FHIR mapping (`../specifications/`).

## How to execute

1. Pick the lowest-numbered task whose `Depends on` tasks are all merged.
2. Create its branch, write tests first (TDD), implement, satisfy the Definition of Done.
3. Update the row in [traceability-matrix.md](../design/traceability-matrix.md) (SR/NFR → TASK → test).
4. Submit to QA review; merge; proceed to the next unblocked task.

Phases follow the architecture's dependency tiers: build the **backend foundation → security/identity
→ domain services → API → module host + DICOM backend**, then the **frontend foundation → core views →
module system + DICOM viewer**, then **integration, system testing and compliance hardening**. Backend
phases 6–8 (frontend) can begin once the OpenAPI contract (TASK-068) is stable.

## Phase order

| Phase | Folder                                                                      | Theme                                                                   |
|-------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------|
| 0     | [phase-0-foundation](phase-0-foundation/)                                   | Repo, toolchain, app skeletons, Docker Compose, CI                      |
| 1     | [phase-1-persistence-audit](phase-1-persistence-audit/)                     | Models, migrations, repositories, crypto, audit                         |
| 2     | [phase-2-auth-identity](phase-2-auth-identity/)                             | Password, session, login/lockout, authz, consent, identity, worker base |
| 3     | [phase-3-domain-services](phase-3-domain-services/)                         | Groups, clinical entries, attachments, appointments, consent linkage    |
| 4     | [phase-4-api-layer](phase-4-api-layer/)                                     | Routers + DTOs per resource, OpenAPI, security middleware               |
| 5     | [phase-5-module-host-dicom-be](phase-5-module-host-dicom-be/)               | Plugin host, PlatformServices, router mount, DICOM backend              |
| 6     | [phase-6-frontend-foundation](phase-6-frontend-foundation/)                 | API client, layout, nav, auth UI                                        |
| 7     | [phase-7-frontend-core](phase-7-frontend-core/)                             | Profile, patients, clinical, appointments, consent, admin               |
| 8     | [phase-8-frontend-modules-dicom](phase-8-frontend-modules-dicom/)           | Frontend module registry, DICOM viewer                                  |
| 9     | [phase-9-integration-test-compliance](phase-9-integration-test-compliance/) | Integration/E2E/perf/security tests, traceability, deploy docs          |

## Full task index (Unit → Task)

### Phase 0 — Foundation & toolchain (enabler)

| Task                                                               | Title                                   | Unit(s) | Implements      | Depends on |
|--------------------------------------------------------------------|-----------------------------------------|---------|-----------------|------------|
| [TASK-001](phase-0-foundation/TASK-001-monorepo-tooling.md)        | Monorepo structure & tooling            | —       | NFR-006, SR-028 | —          |
| [TASK-002](phase-0-foundation/TASK-002-backend-app-skeleton.md)    | Backend FastAPI app skeleton            | —       | SR-001          | 001        |
| [TASK-003](phase-0-foundation/TASK-003-config-secrets.md)          | Config & secrets management             | —       | NFR-007         | 002        |
| [TASK-004](phase-0-foundation/TASK-004-docker-compose-topology.md) | Docker Compose topology + reverse proxy | —       | SR-001, SR-022  | 002        |
| [TASK-005](phase-0-foundation/TASK-005-ci-pipeline.md)             | CI pipeline                             | —       | NFR-006, SR-028 | 001        |

### Phase 1 — Persistence & audit

| Task                                                             | Title                                     | Unit(s)          | Implements             | Depends on |
|------------------------------------------------------------------|-------------------------------------------|------------------|------------------------|------------|
| [TASK-010](phase-1-persistence-audit/TASK-010-domain-models.md)  | SQLAlchemy domain models (FHIR-aligned)   | U-PER-Models     | SR-021, SR-003, SR-004 | 002        |
| [TASK-011](phase-1-persistence-audit/TASK-011-migrations.md)     | Alembic + initial migration + constraints | U-PER-Migrations | SR-003, SR-032, SR-010 | 010        |
| [TASK-012](phase-1-persistence-audit/TASK-012-repositories.md)   | Typed repositories                        | U-PER-Repos      | SR-031                 | 011        |
| [TASK-013](phase-1-persistence-audit/TASK-013-crypto-at-rest.md) | Encryption-at-rest config + key hooks     | U-PER-Crypto     | SR-022                 | 011        |
| [TASK-014](phase-1-persistence-audit/TASK-014-audit-writer.md)   | Append-only AuditService                  | U-AUD-Writer     | SR-023                 | 012        |

### Phase 2 — Auth, session, authorization, identity, worker base

| Task                                                                 | Title                                         | Unit(s)                 | Implements                   | Depends on  |
|----------------------------------------------------------------------|-----------------------------------------------|-------------------------|------------------------------|-------------|
| [TASK-020](phase-2-auth-identity/TASK-020-password-service.md)       | PasswordService (policy + Argon2id)           | U-AUTH-PasswordPolicy   | SR-025, SR-002               | 012         |
| [TASK-021](phase-2-auth-identity/TASK-021-session-service.md)        | SessionService (Redis opaque tokens)          | U-AUTH-Session          | SR-030, ADR-0012             | 012         |
| [TASK-022](phase-2-auth-identity/TASK-022-cookie-csrf.md)            | Hardened cookie + CSRF token                  | U-AUTH-Cookie           | SR-030.6, SR-031             | 021         |
| [TASK-023](phase-2-auth-identity/TASK-023-login.md)                  | Login flow                                    | U-AUTH-Login            | SR-002, SR-029               | 020,021,014 |
| [TASK-024](phase-2-auth-identity/TASK-024-lockout.md)                | Account lockout                               | U-AUTH-Lockout          | SR-029                       | 023         |
| [TASK-025](phase-2-auth-identity/TASK-025-api-deps.md)               | API auth/session dependency (deny-by-default) | U-API-Deps              | SR-005, SR-031.5             | 021         |
| [TASK-026](phase-2-auth-identity/TASK-026-error-handler.md)          | RFC 7807 error handlers                       | U-API-ErrorHandler      | SR-027.3                     | 002         |
| [TASK-027](phase-2-auth-identity/TASK-027-authorization-service.md)  | AuthorizationService (RBAC + ownership)       | U-AUTHZ-Policy          | SR-005, SR-006, SR-007       | 014,025     |
| [TASK-028](phase-2-auth-identity/TASK-028-consent-service.md)        | ConsentService + effective_access union       | U-AUTHZ-Consent         | SR-008, SR-036               | 027         |
| [TASK-029](phase-2-auth-identity/TASK-029-admin-projection.md)       | Admin non-clinical projection                 | U-AUTHZ-AdminProjection | SR-009                       | 027         |
| [TASK-030](phase-2-auth-identity/TASK-030-account-crud.md)           | AccountService create + profile               | U-ID-AccountCrud        | SR-003, SR-004, SR-032       | 027         |
| [TASK-031](phase-2-auth-identity/TASK-031-worker-email.md)           | Celery base + email tasks                     | U-WK-Email              | SR-033, SR-035               | 003,012     |
| [TASK-032](phase-2-auth-identity/TASK-032-activation.md)             | Account activation (72h token)                | U-ID-Activation         | SR-033                       | 030,031,020 |
| [TASK-033](phase-2-auth-identity/TASK-033-account-lifecycle.md)      | Deactivate/reactivate (kill sessions ≤30s)    | U-ID-Lifecycle          | SR-034.1–4                   | 030,021     |
| [TASK-034](phase-2-auth-identity/TASK-034-worker-session-revoke.md)  | Worker: session-kill propagation              | U-WK-SessionRevoke      | SR-034.2, SR-030.5           | 033,031     |
| [TASK-035](phase-2-auth-identity/TASK-035-erasure-anonymize.md)      | Erasure → anonymize + retrieval code          | U-ID-Erasure            | SR-024, SR-034.5–7, ADR-0013 | 030,014,031 |
| [TASK-036](phase-2-auth-identity/TASK-036-worker-retention-erase.md) | Worker: 5-year permanent erasure              | U-WK-RetentionErase     | SR-024, ADR-0013             | 035         |

### Phase 3 — Domain services

| Task                                                                     | Title                                  | Unit(s)                | Implements               | Depends on |
|--------------------------------------------------------------------------|----------------------------------------|------------------------|--------------------------|------------|
| [TASK-040](phase-3-domain-services/TASK-040-group-crud.md)               | Group CRUD                             | U-GRP-Crud             | SR-014                   | 027        |
| [TASK-041](phase-3-domain-services/TASK-041-group-membership.md)         | Group membership (auto + manual)       | U-GRP-Membership       | SR-014.3, SR-004         | 040        |
| [TASK-042](phase-3-domain-services/TASK-042-module-enablement.md)        | Per-group module enablement            | U-GRP-ModuleEnable     | SR-015                   | 040        |
| [TASK-043](phase-3-domain-services/TASK-043-module-access-guard.md)      | ModuleAccessGuard                      | U-AUTHZ-ModuleGuard    | SR-015                   | 042        |
| [TASK-044](phase-3-domain-services/TASK-044-clinical-entry.md)           | Clinical entry create/list             | U-CLIN-EntryCrud       | SR-012, SR-006, SR-007   | 027,014    |
| [TASK-045](phase-3-domain-services/TASK-045-attachment-upload.md)        | Attachment upload → MinIO + pydicom    | U-ATT-Upload           | SR-013, SR-022           | 044,013    |
| [TASK-046](phase-3-domain-services/TASK-046-attachment-fetch.md)         | Attachment authorized fetch            | U-ATT-Fetch            | SR-013.3, SR-005, SR-022 | 045,027    |
| [TASK-047](phase-3-domain-services/TASK-047-appointment-crud.md)         | Appointment create                     | U-APPT-Crud            | SR-010                   | 027        |
| [TASK-048](phase-3-domain-services/TASK-048-appointment-state.md)        | Appointment state machine              | U-APPT-State           | SR-035.5–7               | 047        |
| [TASK-049](phase-3-domain-services/TASK-049-appointment-consent-link.md) | Confirm→grant / decline→revoke consent | U-APPT-ConsentLink     | SR-036                   | 048,028    |
| [TASK-050](phase-3-domain-services/TASK-050-appointment-notify.md)       | Appointment notification dispatch      | U-APPT-Notify          | SR-035.1–2               | 047,031    |
| [TASK-051](phase-3-domain-services/TASK-051-appointment-visibility.md)   | Appointment visibility scoping         | U-AUTHZ-ApptVisibility | SR-011                   | 047,027    |

### Phase 4 — API layer (routers + DTOs: U-API-Routers, U-API-DTO)

| Task                                                                    | Title                                        | Implements                     | Depends on      |
|-------------------------------------------------------------------------|----------------------------------------------|--------------------------------|-----------------|
| [TASK-060](phase-4-api-layer/TASK-060-auth-endpoints.md)                | Auth/session endpoints                       | SR-002, SR-029, SR-030, SR-025 | 023,024,022,020 |
| [TASK-061](phase-4-api-layer/TASK-061-account-activation-endpoints.md)  | Account + activation endpoints               | SR-032, SR-033                 | 030,032         |
| [TASK-062](phase-4-api-layer/TASK-062-lifecycle-retrieval-endpoints.md) | Lifecycle + anonymized-data retrieval        | SR-034, SR-024, ADR-0013       | 033,035         |
| [TASK-063](phase-4-api-layer/TASK-063-groups-modules-endpoints.md)      | Groups + module-enablement endpoints         | SR-014, SR-015, SR-016         | 040,041,042     |
| [TASK-064](phase-4-api-layer/TASK-064-consent-endpoints.md)             | Consent endpoints                            | SR-008, SR-036.7               | 028             |
| [TASK-065](phase-4-api-layer/TASK-065-appointment-endpoints.md)         | Appointment endpoints                        | SR-010, SR-011, SR-035         | 047,048,049,051 |
| [TASK-066](phase-4-api-layer/TASK-066-clinical-attachment-endpoints.md) | Clinical-entry + attachment endpoints        | SR-012, SR-013, SR-005         | 044,045,046     |
| [TASK-067](phase-4-api-layer/TASK-067-me-endpoints.md)                  | `/me`, `/me/modules` endpoints               | SR-003, SR-015                 | 030,043         |
| [TASK-068](phase-4-api-layer/TASK-068-openapi-contract.md)              | OpenAPI 3.1 + redocly lint + client artifact | NFR-006, SR-031                | 060–067         |
| [TASK-069](phase-4-api-layer/TASK-069-security-middleware.md)           | Security middleware + CSRF enforcement       | SR-031                         | 025,026         |

### Phase 5 — Module host + DICOM backend

| Task                                                                   | Title                                        | Unit(s)               | Implements             | Depends on          |
|------------------------------------------------------------------------|----------------------------------------------|-----------------------|------------------------|---------------------|
| [TASK-070](phase-5-module-host-dicom-be/TASK-070-module-discovery.md)  | Module discovery + ModuleManifest + registry | U-MH-Discovery        | SR-016                 | 042                 |
| [TASK-071](phase-5-module-host-dicom-be/TASK-071-platform-services.md) | PlatformServices facade (sole PHI path)      | U-MH-PlatformServices | SR-016, SR-005, SR-023 | 070,027,044,046,014 |
| [TASK-072](phase-5-module-host-dicom-be/TASK-072-router-mount.md)      | RouterRegistry.mount + ModuleAccessGuard     | U-MH-RouterMount      | SR-016, SR-015         | 071,043             |
| [TASK-073](phase-5-module-host-dicom-be/TASK-073-dicom-backend.md)     | DICOM module backend (authorized bytes)      | U-DICOMBE-Studies     | SR-016, SR-017         | 072,046             |

### Phase 6 — Frontend foundation

| Task                                                               | Title                                  | Unit(s)            | Implements      | Depends on |
|--------------------------------------------------------------------|----------------------------------------|--------------------|-----------------|------------|
| [TASK-080](phase-6-frontend-foundation/TASK-080-api-client.md)     | Typed API client + cookie/CSRF + Query | U-FEAPI-Client     | SR-031, NFR-006 | 068        |
| [TASK-081](phase-6-frontend-foundation/TASK-081-layout-theme.md)   | Responsive layout + MUI theme          | U-FE-Layout        | SR-020, NFR-003 | 001        |
| [TASK-082](phase-6-frontend-foundation/TASK-082-navigation.md)     | Role-based navigation                  | U-FE-Nav           | SR-027          | 081        |
| [TASK-083](phase-6-frontend-foundation/TASK-083-confirm-dialog.md) | Confirmation dialog                    | U-FE-Confirm       | SR-027, NFR-009 | 081        |
| [TASK-084](phase-6-frontend-foundation/TASK-084-error-boundary.md) | Error boundary/toast (RFC 7807)        | U-FE-Error         | SR-027.3        | 081        |
| [TASK-085](phase-6-frontend-foundation/TASK-085-login-ui.md)       | Login UI                               | U-FEA-LoginForm    | SR-002          | 080,082    |
| [TASK-086](phase-6-frontend-foundation/TASK-086-activation-ui.md)  | Activation / set-password UI           | U-FEA-Activation   | SR-033          | 080        |
| [TASK-087](phase-6-frontend-foundation/TASK-087-password-ui.md)    | Change-password UI                     | U-FEA-PasswordForm | SR-025          | 080        |
| [TASK-088](phase-6-frontend-foundation/TASK-088-idle-warning.md)   | Inactivity warning + extend            | U-FEA-IdleWarning  | SR-030.4        | 080        |

### Phase 7 — Frontend core views

| Task                                                               | Title                                    | Unit(s)                  | Implements             | Depends on  |
|--------------------------------------------------------------------|------------------------------------------|--------------------------|------------------------|-------------|
| [TASK-090](phase-7-frontend-core/TASK-090-profile.md)              | Profile view                             | U-FEC-Profile            | SR-003, SR-007         | 080,081,082 |
| [TASK-091](phase-7-frontend-core/TASK-091-patients.md)             | Doctor patient list                      | U-FEC-Patients           | SR-006                 | 080,081,082 |
| [TASK-092](phase-7-frontend-core/TASK-092-clinical-entries.md)     | Clinical entries view/create + upload    | U-FEC-ClinicalEntries    | SR-012, SR-013         | 091,066     |
| [TASK-093](phase-7-frontend-core/TASK-093-appointments.md)         | Appointments list/create/confirm/decline | U-FEC-Appointments       | SR-010, SR-011, SR-035 | 065,083     |
| [TASK-094](phase-7-frontend-core/TASK-094-consent.md)              | Consent grant/revoke + unified view      | U-FEC-Consent            | SR-008, SR-036.7       | 064,083     |
| [TASK-095](phase-7-frontend-core/TASK-095-admin-accounts.md)       | Admin account management                 | U-FEC-AdminAccounts      | SR-009, SR-032, SR-034 | 061,062,083 |
| [TASK-096](phase-7-frontend-core/TASK-096-admin-groups-modules.md) | Admin groups & module enablement UI      | U-FEC-AdminGroupsModules | SR-014, SR-015         | 063         |

### Phase 8 — Frontend module system + DICOM viewer

| Task                                                                            | Title                                   | Unit(s)            | Implements       | Depends on  |
|---------------------------------------------------------------------------------|-----------------------------------------|--------------------|------------------|-------------|
| [TASK-100](phase-8-frontend-modules-dicom/TASK-100-frontend-module-registry.md) | Frontend ModuleRegistry + lazy chunks   | U-FEM-Registry     | SR-016           | 080,081,082 |
| [TASK-101](phase-8-frontend-modules-dicom/TASK-101-nav-gating.md)               | Nav gating by `GET /me/modules`         | U-FEM-NavGate      | SR-015, SR-016.2 | 100,067     |
| [TASK-102](phase-8-frontend-modules-dicom/TASK-102-dicom-viewport.md)           | Cornerstone3D viewport                  | U-DICOMFE-Viewport | SR-017, SR-026.3 | 100,073     |
| [TASK-103](phase-8-frontend-modules-dicom/TASK-103-dicom-controls.md)           | Viewer controls (W/L, zoom, pan, slice) | U-DICOMFE-Controls | SR-018           | 102         |

### Phase 9 — Integration, system testing, compliance hardening

| Task                                                                               | Title                                     | Implements        | Depends on      |
|------------------------------------------------------------------------------------|-------------------------------------------|-------------------|-----------------|
| [TASK-110](phase-9-integration-test-compliance/TASK-110-integration-tests.md)      | Integration tests for the 7 runtime flows | §06 flows         | per-flow        |
| [TASK-111](phase-9-integration-test-compliance/TASK-111-system-e2e-tests.md)       | System/E2E + cross-browser                | SR-019, SR-028    | 102,103,090–096 |
| [TASK-112](phase-9-integration-test-compliance/TASK-112-performance-validation.md) | Performance validation vs budgets         | SR-026, NFR-008   | 111             |
| [TASK-113](phase-9-integration-test-compliance/TASK-113-security-review.md)        | Security review + dependency scan         | SR-031.6, NFR-007 | 060,069,028     |
| [TASK-114](phase-9-integration-test-compliance/TASK-114-traceability-update.md)    | Traceability matrix completion            | SR-028, NFR-006   | all             |
| [TASK-115](phase-9-integration-test-compliance/TASK-115-deploy-docs.md)            | Deploy/run docs + sysadmin bootstrap      | dev-plan outputs  | 004             |
| [TASK-116](phase-9-integration-test-compliance/TASK-116-clinical-data-rekeying.md) | Clinical data re-keying (erasure remediation) | ADR-0013, SR-024 | 035a,036,045    |

## Coverage

All 56 software units map to a task (Phases 1–8); all 36 SRs and 9 NFRs are covered (see the
per-SR/NFR mapping in the approved plan and [traceability-matrix.md](../design/traceability-matrix.md),
which TASK-114 completes with the TASK → test column).

## Audit remediation tasks (2026-06-29)

A full audit of phases 0–7 (see [AUDIT-LEDGER.md](AUDIT-LEDGER.md), [SMOKE-RESULTS.md](SMOKE-RESULTS.md),
[AUDIT-FINDINGS.md](AUDIT-FINDINGS.md)) found gaps where tasks were marked Completed without their
acceptance criteria actually met — several units are implemented but never wired into the request path.
The contract showstoppers (CSRF cookie name, login field name) were fixed in-branch; the rest are tracked
as remediation tasks (suffix `-a`, in their owning phase):

| Task                                                                          | Phase | Remediates                   | Gap                                                                                         |
|-------------------------------------------------------------------------------|-------|------------------------------|---------------------------------------------------------------------------------------------|
| [TASK-004a](phase-0-foundation/TASK-004a-migrate-on-bringup.md)               | 0     | 004, 005                     | No DB migration on bring-up (fresh deploy = empty DB)                                       |
| [TASK-024a](phase-2-auth-identity/TASK-024a-lockout-wiring.md)                | 2     | 024, 023                     | Lockout service never wired into login                                                      |
| [TASK-026a](phase-2-auth-identity/TASK-026a-password-policy-problem.md)       | 2     | 026, 032                     | Password-policy error → 500 not 400; activation confirm-match                               |
| [TASK-029a](phase-2-auth-identity/TASK-029a-admin-projection-wiring.md)       | 2     | 029                          | Admin PII projection never applied to account endpoints                                     |
| [TASK-035a](phase-2-auth-identity/TASK-035a-erasure-retrieval-delivery.md)    | 2     | 035                          | Erasure retrieval code never emailed; deadline/re-key gaps                                  |
| [TASK-040a](phase-3-domain-services/TASK-040a-group-name-unique.md)           | 3     | 040, 041                     | Group name unique constraint; auto-membership tests                                         |
| [TASK-044a](phase-3-domain-services/TASK-044a-doctor-patient-roster.md)       | 3     | 044, 066, 091                | Missing doctor patient-roster endpoint (404)                                                |
| [TASK-050a](phase-3-domain-services/TASK-050a-notification-resilience.md)     | 3     | 050                          | Email failure suppresses the in-app notification                                            |
| [TASK-066a](phase-4-api-layer/TASK-066a-multipart-upload.md)                  | 4     | 066, 045                     | Attachment upload not multipart; DICOM metadata discarded                                   |
| [TASK-068a](phase-4-api-layer/TASK-068a-openapi-security.md)                  | 4     | 068                          | OpenAPI cookieAuth/CSRF defined but never applied                                           |
| [TASK-069a](phase-4-api-layer/TASK-069a-csrf-enforcement.md)                  | 4     | 022, 061, 063, 065, 066, 069 | CSRF not enforced app-wide; 401-not-403                                                     |
| [TASK-070a](phase-5-module-host-dicom-be/TASK-070a-module-registry-sync.md)   | 5     | 070, 073                     | Module registry never synced at startup (`/modules` empty)                                  |
| [TASK-086a](phase-6-frontend-foundation/TASK-086a-activation-contract.md)     | 6     | 086                          | Activation UI omits `accountId`; treats invalid token as valid                              |
| [TASK-087a](phase-6-frontend-foundation/TASK-087a-forced-password-gate.md)    | 6     | 087                          | Forced-password gate keys on a field `/me` never returns                                    |
| [TASK-092a](phase-7-frontend-core/TASK-092a-clinical-entries-completeness.md) | 7     | 092                          | Single-file upload; attachments not listed; viewer link not module-gated; create drops time |
| [TASK-095a](phase-7-frontend-core/TASK-095a-admin-accounts-completeness.md)   | 7     | 095                          | Delete dialog lacks ADR-0013 lost-code warning; no resend-activation control                |
| [TASK-096a](phase-7-frontend-core/TASK-096a-group-add-member.md)              | 7     | 096                          | Manual add-member UI missing (SR-014.3)                                                     |

## Out of scope (deferred)

Full FHIR REST API / bulk export; terminology bindings (LOINC/SNOMED/ICD); notification
delivery-tracking (best-effort only for MVP, extension point retained — §8.12); multi-tenancy and
managed-cloud/Kubernetes scaling; full i18n and a formal accessibility audit.
