# Gap report — 2026-09-17

Scope: whole project  ·  Records scanned: 272  ·  Errors: 0  ·  Warnings: 95

Generated with the `medical-records:traceability-check` procedure (throwaway parser, >50 records).

## Record inventory

| Type | Count |
|---|---|
| `user-need` | 15 |
| `nfr` | 9 |
| `regulatory-requirement` | 10 |
| `software-requirement` | 39 |
| `architecture-doc` | 23 |
| `task` | 118 |
| `test-specification` | 13 |
| `risk` | 11 |
| `test-plan` | 1 |
| `test-report` | 1 |
| `problem-report` | 32 |
| `change-request` | 0 |

## Errors

None.

## Warnings

| Check | Element | File | Problem |
|---|---|---|---|
| W1 | SR-017 | `docs/design-inputs/software-requirements/SR-017-dicom-image-opening-and-rendering.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-018 | `docs/design-inputs/software-requirements/SR-018-dicom-viewer-controls.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-026 | `docs/design-inputs/software-requirements/SR-026-performance-budgets-for-routine-operations.md` | no TS verifies this SR (unverified by specification) |
| W2 | SR-003 | `docs/design-inputs/software-requirements/SR-003-unique-user-account-and-profile-view.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-004 | `docs/design-inputs/software-requirements/SR-004-user-type-assignment.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-010 | `docs/design-inputs/software-requirements/SR-010-appointment-creation.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-017 | `docs/design-inputs/software-requirements/SR-017-dicom-image-opening-and-rendering.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-018 | `docs/design-inputs/software-requirements/SR-018-dicom-viewer-controls.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-019 | `docs/design-inputs/software-requirements/SR-019-cross-browser-support.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-021 | `docs/design-inputs/software-requirements/SR-021-fhir-aligned-data-model.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-023 | `docs/design-inputs/software-requirements/SR-023-audit-logging-of-security-relevant-events.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-026 | `docs/design-inputs/software-requirements/SR-026-performance-budgets-for-routine-operations.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-031 | `docs/design-inputs/software-requirements/SR-031-web-vulnerability-mitigations.md` | no TR verifies this SR (unverified by evidence) |
| W5 | SR-001 | `docs/design-inputs/software-requirements/SR-001-browser-accessible-web-application-over-https.md` | approved but links to RR-003 (in_review) |
| W5 | SR-001 | `docs/design-inputs/software-requirements/SR-001-browser-accessible-web-application-over-https.md` | approved but links to RISK-005 (in_review) |
| W5 | SR-001 | `docs/design-inputs/software-requirements/SR-001-browser-accessible-web-application-over-https.md` | approved but links to RISK-010 (in_review) |
| W5 | SR-001 | `docs/design-inputs/software-requirements/SR-001-browser-accessible-web-application-over-https.md` | approved but links to RISK-011 (in_review) |
| W5 | SR-002 | `docs/design-inputs/software-requirements/SR-002-email-and-password-authentication.md` | approved but links to RR-003 (in_review) |
| W5 | SR-003 | `docs/design-inputs/software-requirements/SR-003-unique-user-account-and-profile-view.md` | approved but links to RISK-002 (in_review) |
| W5 | SR-004 | `docs/design-inputs/software-requirements/SR-004-user-type-assignment.md` | approved but links to RISK-002 (in_review) |
| W5 | SR-005 | `docs/design-inputs/software-requirements/SR-005-role-based-access-control-enforcement.md` | approved but links to RR-001 (in_review) |
| W5 | SR-005 | `docs/design-inputs/software-requirements/SR-005-role-based-access-control-enforcement.md` | approved but links to RISK-001 (in_review) |
| W5 | SR-006 | `docs/design-inputs/software-requirements/SR-006-doctor-access-to-own-patients-clinical.md` | approved but links to RR-001 (in_review) |
| W5 | SR-006 | `docs/design-inputs/software-requirements/SR-006-doctor-access-to-own-patients-clinical.md` | approved but links to RISK-001 (in_review) |
| W5 | SR-007 | `docs/design-inputs/software-requirements/SR-007-patient-access-to-own-personal-and.md` | approved but links to RR-001 (in_review) |
| W5 | SR-007 | `docs/design-inputs/software-requirements/SR-007-patient-access-to-own-personal-and.md` | approved but links to RISK-001 (in_review) |
| W5 | SR-008 | `docs/design-inputs/software-requirements/SR-008-patient-grant-and-revoke-of-clinical.md` | approved but links to RR-001 (in_review) |
| W5 | SR-008 | `docs/design-inputs/software-requirements/SR-008-patient-grant-and-revoke-of-clinical.md` | approved but links to RISK-001 (in_review) |
| W5 | SR-008 | `docs/design-inputs/software-requirements/SR-008-patient-grant-and-revoke-of-clinical.md` | approved but links to RISK-004 (in_review) |
| W5 | SR-009 | `docs/design-inputs/software-requirements/SR-009-administrative-personnel-non-clinical-data-scope.md` | approved but links to RR-001 (in_review) |
| W5 | SR-009 | `docs/design-inputs/software-requirements/SR-009-administrative-personnel-non-clinical-data-scope.md` | approved but links to RISK-001 (in_review) |
| W5 | SR-011 | `docs/design-inputs/software-requirements/SR-011-appointment-visibility.md` | approved but links to RISK-009 (in_review) |
| W5 | SR-012 | `docs/design-inputs/software-requirements/SR-012-clinical-entry-creation-with-required-fields.md` | approved but links to RISK-002 (in_review) |
| W5 | SR-013 | `docs/design-inputs/software-requirements/SR-013-clinical-entry-file-attachments.md` | approved but links to RISK-002 (in_review) |
| W5 | SR-017 | `docs/design-inputs/software-requirements/SR-017-dicom-image-opening-and-rendering.md` | approved but links to RR-009 (in_review) |
| W5 | SR-017 | `docs/design-inputs/software-requirements/SR-017-dicom-image-opening-and-rendering.md` | approved but links to RISK-003 (in_review) |
| W5 | SR-018 | `docs/design-inputs/software-requirements/SR-018-dicom-viewer-controls.md` | approved but links to RISK-003 (in_review) |
| W5 | SR-019 | `docs/design-inputs/software-requirements/SR-019-cross-browser-support.md` | approved but links to RR-010 (in_review) |
| W5 | SR-019 | `docs/design-inputs/software-requirements/SR-019-cross-browser-support.md` | approved but links to RISK-003 (in_review) |
| W5 | SR-020 | `docs/design-inputs/software-requirements/SR-020-responsive-layout-across-devices.md` | approved but links to RR-009 (in_review) |
| W5 | SR-021 | `docs/design-inputs/software-requirements/SR-021-fhir-aligned-data-model.md` | approved but links to RISK-002 (in_review) |
| W5 | SR-022 | `docs/design-inputs/software-requirements/SR-022-encryption-in-transit-and-at-rest.md` | approved but links to RR-003 (in_review) |
| W5 | SR-022 | `docs/design-inputs/software-requirements/SR-022-encryption-in-transit-and-at-rest.md` | approved but links to RISK-006 (in_review) |
| W5 | SR-022 | `docs/design-inputs/software-requirements/SR-022-encryption-in-transit-and-at-rest.md` | approved but links to RISK-007 (in_review) |
| W5 | SR-022 | `docs/design-inputs/software-requirements/SR-022-encryption-in-transit-and-at-rest.md` | approved but links to RISK-008 (in_review) |
| W5 | SR-022 | `docs/design-inputs/software-requirements/SR-022-encryption-in-transit-and-at-rest.md` | approved but links to RISK-010 (in_review) |
| W5 | SR-022 | `docs/design-inputs/software-requirements/SR-022-encryption-in-transit-and-at-rest.md` | approved but links to RISK-011 (in_review) |
| W5 | SR-023 | `docs/design-inputs/software-requirements/SR-023-audit-logging-of-security-relevant-events.md` | approved but links to RR-004 (in_review) |
| W5 | SR-023 | `docs/design-inputs/software-requirements/SR-023-audit-logging-of-security-relevant-events.md` | approved but links to RISK-001 (in_review) |
| W5 | SR-023 | `docs/design-inputs/software-requirements/SR-023-audit-logging-of-security-relevant-events.md` | approved but links to RISK-004 (in_review) |
| W5 | SR-023 | `docs/design-inputs/software-requirements/SR-023-audit-logging-of-security-relevant-events.md` | approved but links to RISK-005 (in_review) |
| W5 | SR-023 | `docs/design-inputs/software-requirements/SR-023-audit-logging-of-security-relevant-events.md` | approved but links to RISK-006 (in_review) |
| W5 | SR-024 | `docs/design-inputs/software-requirements/SR-024-personal-data-erasure.md` | approved but links to RR-002 (in_review) |
| W5 | SR-024 | `docs/design-inputs/software-requirements/SR-024-personal-data-erasure.md` | approved but links to RR-005 (in_review) |
| W5 | SR-024 | `docs/design-inputs/software-requirements/SR-024-personal-data-erasure.md` | approved but links to RISK-002 (in_review) |
| W5 | SR-024 | `docs/design-inputs/software-requirements/SR-024-personal-data-erasure.md` | approved but links to RISK-008 (in_review) |
| W5 | SR-025 | `docs/design-inputs/software-requirements/SR-025-password-complexity-policy.md` | approved but links to RR-003 (in_review) |
| W5 | SR-025 | `docs/design-inputs/software-requirements/SR-025-password-complexity-policy.md` | approved but links to RISK-005 (in_review) |
| W5 | SR-025 | `docs/design-inputs/software-requirements/SR-025-password-complexity-policy.md` | approved but links to RISK-010 (in_review) |
| W5 | SR-026 | `docs/design-inputs/software-requirements/SR-026-performance-budgets-for-routine-operations.md` | approved but links to RR-010 (in_review) |
| W5 | SR-026 | `docs/design-inputs/software-requirements/SR-026-performance-budgets-for-routine-operations.md` | approved but links to RISK-007 (in_review) |
| W5 | SR-027 | `docs/design-inputs/software-requirements/SR-027-usability-controls.md` | approved but links to RR-009 (in_review) |
| W5 | SR-028 | `docs/design-inputs/software-requirements/SR-028-traceable-version-controlled-development-records.md` | approved but links to RR-006 (in_review) |
| W5 | SR-028 | `docs/design-inputs/software-requirements/SR-028-traceable-version-controlled-development-records.md` | approved but links to RR-007 (in_review) |
| W5 | SR-028 | `docs/design-inputs/software-requirements/SR-028-traceable-version-controlled-development-records.md` | approved but links to RR-008 (in_review) |
| W5 | SR-028 | `docs/design-inputs/software-requirements/SR-028-traceable-version-controlled-development-records.md` | approved but links to RR-010 (in_review) |
| W5 | SR-028 | `docs/design-inputs/software-requirements/SR-028-traceable-version-controlled-development-records.md` | approved but links to RISK-007 (in_review) |
| W5 | SR-028 | `docs/design-inputs/software-requirements/SR-028-traceable-version-controlled-development-records.md` | approved but links to RISK-010 (in_review) |
| W5 | SR-029 | `docs/design-inputs/software-requirements/SR-029-account-lockout-after-failed-login-attempts.md` | approved but links to RR-003 (in_review) |
| W5 | SR-029 | `docs/design-inputs/software-requirements/SR-029-account-lockout-after-failed-login-attempts.md` | approved but links to RISK-005 (in_review) |
| W5 | SR-030 | `docs/design-inputs/software-requirements/SR-030-session-management.md` | approved but links to RR-003 (in_review) |
| W5 | SR-030 | `docs/design-inputs/software-requirements/SR-030-session-management.md` | approved but links to RISK-005 (in_review) |
| W5 | SR-031 | `docs/design-inputs/software-requirements/SR-031-web-vulnerability-mitigations.md` | approved but links to RR-003 (in_review) |
| W5 | SR-031 | `docs/design-inputs/software-requirements/SR-031-web-vulnerability-mitigations.md` | approved but links to RISK-003 (in_review) |
| W5 | SR-031 | `docs/design-inputs/software-requirements/SR-031-web-vulnerability-mitigations.md` | approved but links to RISK-005 (in_review) |
| W5 | SR-033 | `docs/design-inputs/software-requirements/SR-033-account-activation-via-email.md` | approved but links to RISK-009 (in_review) |
| W5 | SR-034 | `docs/design-inputs/software-requirements/SR-034-account-deactivation-and-deletion-by-system.md` | approved but links to RR-002 (in_review) |
| W5 | SR-035 | `docs/design-inputs/software-requirements/SR-035-patient-notification-and-confirmation-of-scheduled.md` | approved but links to RISK-009 (in_review) |
| W5 | SR-036 | `docs/design-inputs/software-requirements/SR-036-clinical-data-access-grant-on-appointment.md` | approved but links to RR-001 (in_review) |
| W5 | SR-036 | `docs/design-inputs/software-requirements/SR-036-clinical-data-access-grant-on-appointment.md` | approved but links to RISK-001 (in_review) |
| W5 | SR-036 | `docs/design-inputs/software-requirements/SR-036-clinical-data-access-grant-on-appointment.md` | approved but links to RISK-004 (in_review) |
| W5 | TASK-036 | `docs/design-outputs/tasks/TASK-036-worker-5-year-permanent-erasure.md` | approved but links to RISK-008 (in_review) |
| W5 | TASK-066 | `docs/design-outputs/tasks/TASK-066-clinical-entry-attachment-endpoints.md` | approved but links to RISK-002 (in_review) |
| W5 | TASK-118 | `docs/design-outputs/tasks/TASK-118-wire-account-lockout-into-the-login.md` | approved but links to RISK-005 (in_review) |
| W5 | TASK-132 | `docs/design-outputs/tasks/TASK-132-clinical-entries-view-completeness-remediation.md` | approved but links to TASK-101 (draft) |
| W6 | TASK-148 | `docs/design-outputs/tasks/TASK-148-fix-dangling-remediation-ids-in-traceability-matrix.md` | links to obsolete element TASK-114 |
| W7 | TASK-001 | `docs/design-outputs/tasks/TASK-001-monorepo-structure-tooling.md` | approved TASK whose SR NFR-006 has no TS |
| W7 | TASK-003 | `docs/design-outputs/tasks/TASK-003-config-secrets-management.md` | approved TASK whose SR NFR-007 has no TS |
| W7 | TASK-005 | `docs/design-outputs/tasks/TASK-005-ci-pipeline.md` | approved TASK whose SR NFR-006 has no TS |
| W7 | TASK-068 | `docs/design-outputs/tasks/TASK-068-openapi-3-1-contract-finalization-typed.md` | approved TASK whose SR NFR-006 has no TS |
| W7 | TASK-073 | `docs/design-outputs/tasks/TASK-073-dicom-module-backend-authorized-bytes.md` | approved TASK whose SR SR-017 has no TS |
| W7 | TASK-080 | `docs/design-outputs/tasks/TASK-080-typed-api-client-cookie-csrf-tanstack.md` | approved TASK whose SR NFR-006 has no TS |
| W7 | TASK-081 | `docs/design-outputs/tasks/TASK-081-responsive-layout-mui-theme.md` | approved TASK whose SR NFR-003 has no TS |
| W7 | TASK-083 | `docs/design-outputs/tasks/TASK-083-reusable-confirmation-dialog-for-destructive-actions.md` | approved TASK whose SR NFR-009 has no TS |
| W7 | TASK-127 | `docs/design-outputs/tasks/TASK-127-surface-the-security-model-in-openapi.md` | approved TASK whose SR NFR-006 has no TS |

## Coverage

| SR | Title | TASKs | ADDs | TS | TR | RISKs mitigated |
|---|---|---|---|---|---|---|
| SR-001 | Browser-accessible web application over  | 3 | ADD-004, ADD-005, ADD-018 | TS-011 | TR-001 | RISK-005, RISK-010, RISK-011 |
| SR-002 | Email and password authentication | 5 | ADD-006, ADD-019 | TS-001 | TR-001 | — |
| SR-003 | Unique user account and profile view | 6 | ADD-008, ADD-016, ADD-020 | TS-003 | — | RISK-002 |
| SR-004 | User type assignment | 3 | ADD-007, ADD-008, ADD-016, ADD-020 | TS-003 | — | RISK-002 |
| SR-005 | Role-based access control enforcement | 7 | ADD-007, ADD-020 | TS-002 | TR-001 | RISK-001 |
| SR-006 | Doctor access to own patients' clinical  | 6 | ADD-007, ADD-011, ADD-020 | TS-002 | TR-001 | RISK-001 |
| SR-007 | Patient access to own personal and clini | 4 | ADD-007, ADD-011, ADD-020 | TS-002 | TR-001 | RISK-001 |
| SR-008 | Patient grant and revoke of clinical-dat | 4 | ADD-005, ADD-007, ADD-020 | TS-002 | TR-001 | RISK-001, RISK-004 |
| SR-009 | Administrative personnel non-clinical da | 3 | ADD-007, ADD-020 | TS-002 | TR-001 | RISK-001 |
| SR-010 | Appointment creation | 4 | ADD-010, ADD-020 | TS-006 | — | — |
| SR-011 | Appointment visibility | 3 | ADD-007, ADD-010, ADD-020 | TS-002 | TR-001 | RISK-009 |
| SR-012 | Clinical entry creation with required fi | 5 | ADD-004, ADD-011, ADD-020 | TS-007 | TR-001 | RISK-002 |
| SR-013 | Clinical entry file attachments | 8 | ADD-012, ADD-020 | TS-007 | TR-001 | RISK-002 |
| SR-014 | User group management | 6 | ADD-009, ADD-020 | TS-005 | TR-001 | — |
| SR-015 | Per-group module enablement | 9 | ADD-007, ADD-009, ADD-020, ADD-021 | TS-005 | TR-001 | — |
| SR-016 | Modular plugin architecture | 10 | ADD-014, ADD-015, ADD-020, ADD-021 | TS-010 | TR-001 | — |
| SR-017 | DICOM image opening and rendering | 3 | ADD-004, ADD-015, ADD-022 | — | — | RISK-003 |
| SR-018 | DICOM viewer controls | 1 | ADD-022 | — | — | RISK-003 |
| SR-019 | Cross-browser support | 1 | ADD-018 | TS-012 | — | RISK-003 |
| SR-020 | Responsive layout across devices | 1 | ADD-018 | TS-012 | TR-001 | — |
| SR-021 | FHIR-aligned data model | 1 | ADD-004, ADD-016 | TS-008 | — | RISK-002 |
| SR-022 | Encryption in transit and at rest | 4 | ADD-004, ADD-012, ADD-016 | TS-008 | TR-001 | RISK-006, RISK-007, RISK-008, RISK-010, RISK-011 |
| SR-023 | Audit logging of security-relevant event | 6 | ADD-004, ADD-013 | TS-009 | — | RISK-001, RISK-004, RISK-005, RISK-006 |
| SR-024 | Personal data erasure | 8 | ADD-008, ADD-017 | TS-004 | TR-001 | RISK-002, RISK-008 |
| SR-025 | Password complexity policy | 6 | ADD-006, ADD-019 | TS-001 | TR-001 | RISK-005, RISK-010 |
| SR-026 | Performance budgets for routine operatio | 4 | ADD-005, ADD-012, ADD-022 | — | — | RISK-007 |
| SR-027 | Usability controls | 6 | ADD-018 | TS-012 | TR-001 | — |
| SR-028 | Traceable, version-controlled developmen | 7 | ADD-002, ADD-003 | TS-013 | TR-001 | RISK-007, RISK-010 |
| SR-029 | Account lockout after failed login attem | 6 | ADD-006 | TS-001 | TR-001 | RISK-005 |
| SR-030 | Session management | 9 | ADD-004, ADD-006, ADD-019 | TS-001 | TR-001 | RISK-005 |
| SR-031 | Web vulnerability mitigations | 12 | ADD-005, ADD-016, ADD-023 | TS-008, TS-011 | — | RISK-003, RISK-005 |
| SR-032 | Role-constrained user account creation | 6 | ADD-008 | TS-003 | TR-001 | — |
| SR-033 | Account activation via email | 7 | ADD-008, ADD-017, ADD-019 | TS-003 | TR-001 | RISK-009 |
| SR-034 | Account deactivation and deletion by sys | 8 | ADD-006, ADD-008, ADD-017 | TS-003 | TR-001 | — |
| SR-035 | Patient notification and confirmation of | 9 | ADD-010, ADD-017, ADD-020 | TS-006 | TR-001 | RISK-009 |
| SR-036 | Clinical data access grant on appointmen | 6 | ADD-007, ADD-010, ADD-020 | TS-002 | TR-001 | RISK-001, RISK-004 |
| SR-037 | Design-token-based theming foundation | 4 | ADD-001 | TS-012 | TR-001 | — |
| SR-038 | Light and dark theme modes with accessib | 5 | ADD-001 | TS-012 | TR-001 | — |
| SR-039 | Theme mode toggle, system default, and p | 2 | ADD-001 | TS-012 | TR-001 | — |
