# Requirements Traceability Matrix

Verifies that the architecture implements **all** requirements (NFR-006, SR-028). Columns: requirement → satisfying software item(s) (section 05) → governing ADR(s) → design artifact(s). This is the architecture-side trace; requirement→test traceability is established in the Testing phase per the development plan.

## Software requirements (SR) → architecture

| SR     | Title (short)                           | Software item(s)                                                                                                                | ADR(s)           | Artifact(s)                            |
|--------|-----------------------------------------|---------------------------------------------------------------------------------------------------------------------------------|------------------|----------------------------------------|
| SR-001 | HTTPS web app                           | SI-API, SI-FE-SHELL, Reverse proxy                                                                                              | 0003, 0010, 0011 | 03, 07, diagram-context/deployment, TASK-004, TASK-004a |
| SR-002 | Email/password auth                     | SI-AUTH (`U-AUTH-Login`), SI-FE-AUTH                                                                                            | 0011, 0012       | 06.1, seq-login                        |
| SR-003 | Unique account + profile                | SI-IDENTITY (`U-ID-AccountCrud`), SI-PERSIST                                                                                    | 0004             | domain-model, 05, TASK-004a            |
| SR-004 | User type assignment                    | SI-IDENTITY, SI-AUTHZ, SI-PERSIST                                                                                               | 0006             | domain-model                           |
| SR-005 | RBAC deny-by-default                    | SI-AUTHZ (`U-AUTHZ-Policy`)                                                                                                     | 0006, 0011       | 08.2, 12, seq-doctor-access            |
| SR-006 | Doctor sees own patients                | SI-AUTHZ (`U-AUTHZ-Consent`), SI-CLINICAL                                                                                       | 0006             | 06.2, seq-doctor-access                |
| SR-007 | Patient sees own data                   | SI-AUTHZ, SI-CLINICAL, SI-FE-CORE                                                                                               | 0006             | 06, 05                                 |
| SR-008 | Grant/revoke consent (immediate)        | SI-AUTHZ (`U-AUTHZ-Consent`), SI-API                                                                                            | 0006             | 06.6, domain-model                     |
| SR-009 | Admin non-clinical scope                | SI-AUTHZ (`U-AUTHZ-AdminProjection`)                                                                                            | 0006             | 08.2                                   |
| SR-010 | Appointment creation                    | SI-APPT (`U-APPT-Crud`)                                                                                                         | 0006             | seq-appointment-consent                |
| SR-011 | Appointment visibility                  | SI-AUTHZ (`U-AUTHZ-ApptVisibility`), SI-APPT                                                                                    | 0006             | 05                                     |
| SR-012 | Clinical entry creation                 | SI-CLINICAL (`U-CLIN-EntryCrud`)                                                                                                | 0004, 0007       | domain-model, fhir-mapping             |
| SR-013 | Clinical entry attachments              | SI-ATTACH                                                                                                                       | 0008, 0009       | seq-dicom-view, domain-model           |
| SR-014 | Group management                        | SI-GROUPS (`U-GRP-Crud`, `U-GRP-Membership`)                                                                                    | 0006             | domain-model                           |
| SR-015 | Per-group module enablement             | SI-GROUPS (`U-GRP-ModuleEnable`), SI-AUTHZ (`U-AUTHZ-ModuleGuard`)                                                              | 0005, 0006       | seq-dicom-view                         |
| SR-016 | Modular plugin architecture             | SI-MODHOST, SI-FE-MODREG, SI-MOD-DICOM-BE/FE                                                                                    | 0001, 0005       | 08.7, 12, building-blocks              |
| SR-017 | DICOM open & render                     | SI-MOD-DICOM-FE (`U-DICOMFE-Viewport`), SI-MOD-DICOM-BE                                                                         | 0008             | seq-dicom-view                         |
| SR-018 | DICOM viewer controls                   | SI-MOD-DICOM-FE (`U-DICOMFE-Controls`)                                                                                          | 0008             | seq-dicom-view                         |
| SR-019 | Cross-browser                           | SI-FE-SHELL, all FE items                                                                                                       | 0003             | 08.8, 11                               |
| SR-020 | Responsive layout                       | SI-FE-SHELL (`U-FE-Layout`)                                                                                                     | 0003             | 08.8                                   |
| SR-021 | FHIR-aligned model                      | SI-PERSIST (`U-PER-Models`)                                                                                                     | 0004, 0007       | fhir-mapping, domain-model             |
| SR-022 | Encryption in transit & at rest         | Reverse proxy, SI-PERSIST (`U-PER-Crypto`), SI-ATTACH                                                                           | 0009, 0010, 0011 | 08.3, deployment                       |
| SR-023 | Audit logging                           | SI-AUDIT (`U-AUD-Writer`)                                                                                                       | 0011             | 08.4, all sequences                    |
| SR-024 | Personal data erasure                   | SI-IDENTITY (`U-ID-Erasure`), SI-WORKER (`U-WK-RetentionErase`)                                                                 | 0009, 0011, 0013 | 06.7, 08.5, activity-account-lifecycle |
| SR-025 | Password complexity policy              | SI-AUTH (`U-AUTH-PasswordPolicy`)                                                                                               | 0011, 0012       | 08.3                                   |
| SR-026 | Performance budgets                     | SI-API, SI-ATTACH, SI-MOD-DICOM-FE                                                                                              | 0008, 0009       | 08.9, 10 (normal-load assumption)      |
| SR-027 | Usability controls                      | SI-FE-SHELL (`U-FE-Confirm`, `U-FE-Error`, `U-FE-Nav`)                                                                          | 0003             | 08.8, 08.6                             |
| SR-028 | Traceable dev records                   | (process) — this matrix, ADRs, version control                                                                                  | 0011             | this matrix, adr/, 09, TASK-005        |
| SR-029 | Account lockout                         | SI-AUTH (`U-AUTH-Lockout`)                                                                                                      | 0011, 0012       | 06.1, seq-login                        |
| SR-030 | Session management                      | SI-AUTH (`U-AUTH-Session`, `U-AUTH-Cookie`), SI-FE-AUTH (`U-FEA-IdleWarning`)                                                   | 0012             | 08.3, seq-login                        |
| SR-031 | Web vulnerability mitigations           | SI-API (`U-API-*`), security middleware, SI-PERSIST (`U-PER-Repos`)                                                             | 0011             | 08.3, 08.6                             |
| SR-032 | Role-constrained account creation       | SI-IDENTITY (`U-ID-AccountCrud`)                                                                                                | 0006             | activity-account-lifecycle             |
| SR-033 | Account activation via email            | SI-IDENTITY (`U-ID-Activation`), SI-WORKER (`U-WK-Email`)                                                                       | 0002, 0011       | activity-account-lifecycle             |
| SR-034 | Deactivation/deletion                   | SI-IDENTITY (`U-ID-Lifecycle`, `U-ID-Erasure`), SI-AUTH (session kill), SI-WORKER (`U-WK-SessionRevoke`, `U-WK-RetentionErase`) | 0011, 0012, 0013 | 06.7, activity-account-lifecycle       |
| SR-035 | Appointment notification & confirmation | SI-APPT (`U-APPT-State`, `U-APPT-Notify`), SI-WORKER                                                                            | 0006             | seq-appointment-consent                |
| SR-036 | Consent grant on confirmation           | SI-AUTHZ (`U-AUTHZ-Consent`), SI-APPT (`U-APPT-ConsentLink`)                                                                    | 0006             | 06.3, seq-appointment-consent          |

**Result: all 36 SRs are mapped to at least one software item.**

## Non-functional requirements (NFR) → architecture

| NFR     | Title                 | How addressed                                                        | Items / ADRs                                                                   |
|---------|-----------------------|----------------------------------------------------------------------|--------------------------------------------------------------------------------|
| NFR-001 | Browser compatibility | Standards-based SPA; cross-browser test pass                         | SI-FE-*; ADR-0003; SR-019                                                      |
| NFR-002 | FHIR data governance  | FHIR R4-aligned model + documented mapping                           | SI-PERSIST; ADR-0007; fhir-mapping.md; SR-021                                  |
| NFR-003 | Device/responsive     | Responsive layout, breakpoints, touch targets                        | SI-FE-SHELL; ADR-0003; SR-020                                                  |
| NFR-004 | GDPR                  | Consent, minimization, erasure, audit, encryption                    | SI-AUTHZ, SI-IDENTITY, SI-AUDIT; ADR-0006/0011; SR-005/008/022/023/024         |
| NFR-005 | MDR/FDA               | Traceable docs, verified clinical features (DICOM)                   | This matrix, ADRs; SI-MOD-DICOM-*; SR-017/028                                  |
| NFR-006 | IEC 62304             | Lifecycle outputs, item/unit decomposition, interfaces, traceability | Arc42 doc, 05, 12, this matrix; SR-028; TASK-005 (CI gate)                     |
| NFR-007 | Cybersecurity         | TLS, at-rest crypto, auth/session/lockout, OWASP, audit              | SI-AUTH, SI-AUTHZ, SI-API, SI-AUDIT; ADR-0011/0012; SR-022/023/025/029/030/031 |
| NFR-008 | Performance           | Budgets, object-store offload, client DICOM, lazy chunks             | SI-API, SI-ATTACH, SI-MOD-DICOM-FE; ADR-0008/0009; SR-026                      |
| NFR-009 | Usability             | Consistent nav, confirmations, clear errors                          | SI-FE-SHELL; ADR-0003; SR-027                                                  |

**Result: all 9 NFRs are addressed.**

## User needs (UN) → coverage (via SRs)

| UN                                       | Covered by SR(s)       | Items                           |
|------------------------------------------|------------------------|---------------------------------|
| UN-001 Web access                        | SR-001, SR-019, SR-020 | SI-API, SI-FE-SHELL             |
| UN-002 Authenticated profile             | SR-002, SR-003         | SI-AUTH, SI-IDENTITY            |
| UN-003 Differentiated access             | SR-004, SR-005         | SI-AUTHZ, SI-IDENTITY           |
| UN-004 Doctor own-patient access         | SR-006                 | SI-AUTHZ, SI-CLINICAL           |
| UN-005 Patient ownership & consent       | SR-007, SR-008         | SI-AUTHZ, SI-CLINICAL           |
| UN-006 Admin limited access & scheduling | SR-009, SR-010         | SI-AUTHZ, SI-APPT               |
| UN-007 Appointment scheduling            | SR-010, SR-011         | SI-APPT, SI-AUTHZ               |
| UN-008 Clinical entries                  | SR-012, SR-013         | SI-CLINICAL, SI-ATTACH          |
| UN-009 Groups & module enablement        | SR-014, SR-015         | SI-GROUPS, SI-AUTHZ             |
| UN-010 Extensible plugins                | SR-016                 | SI-MODHOST, SI-FE-MODREG        |
| UN-011 DICOM viewing                     | SR-017, SR-018         | SI-MOD-DICOM-FE/BE              |
| UN-012 Account lifecycle                 | SR-032, SR-033, SR-034 | SI-IDENTITY, SI-WORKER, SI-AUTH |
| UN-013 Appointment notify & confirm      | SR-035, SR-036         | SI-APPT, SI-AUTHZ, SI-WORKER    |

**Result: all 13 user needs are covered.**

## Coverage summary

- 36/36 software requirements → mapped to software items.
- 9/9 non-functional requirements → addressed.
- 13/13 user needs → covered.
- **No requirement is left unaddressed by the architecture.**

## Audit remediation note (2026-06-29)

The architecture covers every requirement, but a phase 0–7 implementation audit
([../implementation-plan/AUDIT-LEDGER.md](../implementation-plan/AUDIT-LEDGER.md)) found requirements
whose **implementation** was incomplete despite the owning task being marked Completed. The
requirement→test column (TASK-114) must reflect these remediation tasks:

| Requirement       | Gap found                                                     | Remediation task                |
|-------------------|---------------------------------------------------------------|---------------------------------|
| SR-006            | Doctor patient-roster endpoint missing (404)                  | TASK-044a                       |
| SR-009            | Admin non-clinical projection never applied to endpoints      | TASK-029a                       |
| SR-029            | Account lockout never wired into login                        | TASK-024a                       |
| SR-031.3          | CSRF not enforced app-wide (most mutating routes unprotected) | TASK-069a, TASK-068a            |
| SR-024 / ADR-0013 | Erasure retrieval code never delivered; deadline/re-key gaps  | TASK-035a                       |
| SR-016            | Module registry never synced at startup (`/modules` empty)    | TASK-070a                       |
| SR-013            | Attachment upload not multipart; DICOM metadata discarded     | TASK-066a                       |
| SR-001.1 / SR-003 | No DB migration on bring-up (fresh deploy = empty schema)     | TASK-004a (**completed** 2026-06-30) |
| SR-025 / SR-033   | Forced-password gate inert; activation contract + policy-400  | TASK-087a, TASK-086a, TASK-026a |
| SR-014            | Group-name uniqueness not DB-enforced                         | TASK-040a → `tests/groups/test_membership.py` |
| SR-035            | Email failure suppresses in-app notification                  | TASK-050a → `tests/appointments/test_notify.py` |
| SR-022            | No column used EncryptedString (PHI readable from DB dump)    | TASK-013 (**remediated** 2026-06-30) |
| SR-023            | record() signature diverged from 12-interfaces contract; audit_log mutable at DB level | TASK-014 (**remediated** 2026-06-30) |
| SR-031            | AppointmentRepository.list_for_actor() embedded role-based authorization logic | TASK-012 (**remediated** 2026-06-30) |
| SR-029            | Lockout wired into login endpoint + admin unlock endpoint     | TASK-024a → `tests/api/test_lockout_integration.py` |
| SR-025 / SR-033   | PasswordPolicyError→400; activation confirm_password check    | TASK-026a → `tests/api/test_activation_router.py` |
| SR-009            | Admin non-clinical projection wired into account endpoints    | TASK-029a → `tests/api/test_accounts_router.py` |
| SR-024 / SR-034   | Erasure code emailed; deadline enforced; ANONYMIZED_RETRIEVAL | TASK-035a → `tests/identity/test_erasure.py` |

## Phase-4 API layer task → test traceability (2026-06-30)

| Requirement  | Task      | Key test file(s)                                                         |
|--------------|-----------|--------------------------------------------------------------------------|
| SR-002, SR-025, SR-029, SR-030 | TASK-060 | `tests/api/test_auth_router.py`, `tests/api/test_lockout_integration.py` |
| SR-032, SR-033 | TASK-061 | `tests/api/test_accounts_router.py`, `tests/api/test_activation_router.py` |
| SR-034, SR-024, ADR-0013 | TASK-062 | `tests/api/test_lifecycle_router.py`, `tests/api/test_anonymized_retrieve.py` |
| SR-014, SR-015, SR-016 | TASK-063 | `tests/api/test_groups_router.py` |
| SR-008, SR-036.7 | TASK-064 | `tests/api/test_consents_router.py` |
| SR-010, SR-011, SR-035 | TASK-065 | `tests/api/test_appointments_router.py` |
| SR-012, SR-013, SR-005 | TASK-066 | `tests/api/test_clinical_router.py`, `tests/api/test_attachments_router.py` |
| SR-013 | TASK-066a | `tests/api/test_attachments_router.py`, `tests/attachments/test_attachment_upload.py` |
| SR-003, SR-015 | TASK-067 | `tests/api/test_me_router.py` |
| NFR-006, SR-031 | TASK-068 | `tests/api/test_openapi_contract.py` |
| SR-031 | TASK-068a | `tests/api/test_openapi_contract.py` (TestOpenAPISecurityRequirements) |
| SR-031 | TASK-069 | `tests/api/test_security_headers.py`, `tests/api/test_csrf_enforcement.py` |
| SR-031.3 | TASK-069a | `tests/api/test_csrf_enforcement.py` |

## Phase-6 frontend foundation task → test traceability (2026-06-30)

| Requirement | Task | Key test file(s) |
|-------------|------|------------------|
| SR-027 | TASK-083 | `frontend/src/core/confirm/ConfirmDialog.test.tsx` |
| SR-030.7 | TASK-085 | `frontend/src/auth/LoginPage.test.tsx` |
| SR-033 | TASK-086a | `frontend/src/auth/ActivationPage.test.tsx` |
| SR-025 | TASK-087a | `frontend/src/auth/ForcedPasswordGate.test.tsx` |

## Phase-7 frontend core task → test traceability (2026-06-30)

| Requirement | Task | Key test file(s) |
|-------------|------|------------------|
| SR-006 | TASK-091 | `frontend/src/core/patients/PatientListPage.test.tsx` |
| SR-012, SR-013, SR-015, SR-016 | TASK-092, TASK-092a | `frontend/src/core/clinical/ClinicalEntriesPage.test.tsx` |
| SR-009, SR-032, SR-034, ADR-0013 | TASK-095, TASK-095a | `frontend/src/core/admin/accounts/AccountsPage.test.tsx` |
| SR-014, SR-015 | TASK-096, TASK-096a | `frontend/src/core/admin/groups/GroupsPage.test.tsx` |
