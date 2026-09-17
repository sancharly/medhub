# Gap report — 2026-09-17

Scope: whole project  ·  Records scanned: 181  ·  Errors: 8  ·  Warnings: 248

Generated with the `medical-records:traceability-check` procedure (throwaway parser, >50 records).

## Record inventory

| Type | Count |
|---|---|
| `user-need` | 15 |
| `nfr` | 9 |
| `regulatory-requirement` | 0 |
| `software-requirement` | 39 |
| `architecture-doc` | 1 |
| `task` | 117 |
| `test-specification` | 0 |
| `risk` | 0 |
| `test-plan` | 0 |
| `test-report` | 0 |
| `problem-report` | 0 |
| `change-request` | 0 |

## Errors

| Check | Element | File | Problem |
|---|---|---|---|
| E8 | TASK-003 | `docs/design-outputs/tasks/TASK-003-config-secrets-management.md` | no required link: implements → SR; links to the right relation but the wrong type: NFR-007 (implements) |
| E8 | TASK-136 | `docs/design-outputs/tasks/TASK-136-align-async-handlers-with-sync-io-stack.md` | no required link: implements → SR; links to the right relation but the wrong type: NFR-008 (implements) |
| E8 | TASK-138 | `docs/design-outputs/tasks/TASK-138-pii-scrubbing-for-worker-and-notification-logs.md` | no required link: implements → SR; links to the right relation but the wrong type: NFR-004 (implements) |
| E8 | TASK-140 | `docs/design-outputs/tasks/TASK-140-auth-config-hygiene-dead-signing-key-lockout-required.md` | no required link: implements → SR |
| E8 | TASK-141 | `docs/design-outputs/tasks/TASK-141-worker-reliability-retention-sessions-retries-silent-failures.md` | no required link: implements → SR |
| E8 | TASK-143 | `docs/design-outputs/tasks/TASK-143-unify-frontend-api-client-upload-and-problem-types.md` | no required link: implements → SR |
| E8 | TASK-146 | `docs/design-outputs/tasks/TASK-146-frontend-unit-test-gaps-session-attachment-csrf.md` | no required link: implements → SR; links to the right relation but the wrong type: NFR-006 (implements) |
| E8 | TASK-147 | `docs/design-outputs/tasks/TASK-147-iso-14971-risk-register-bootstrap.md` | no required link: implements → SR; links to the right relation but the wrong type: NFR-005 (implements), NFR-006 (implements) |

## Warnings

| Check | Element | File | Problem |
|---|---|---|---|
| W1 | SR-001 | `docs/design-inputs/software-requirements/SR-001-browser-accessible-web-application-over-https.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-002 | `docs/design-inputs/software-requirements/SR-002-email-and-password-authentication.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-003 | `docs/design-inputs/software-requirements/SR-003-unique-user-account-and-profile-view.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-004 | `docs/design-inputs/software-requirements/SR-004-user-type-assignment.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-005 | `docs/design-inputs/software-requirements/SR-005-role-based-access-control-enforcement.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-006 | `docs/design-inputs/software-requirements/SR-006-doctor-access-to-own-patients-clinical.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-007 | `docs/design-inputs/software-requirements/SR-007-patient-access-to-own-personal-and.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-008 | `docs/design-inputs/software-requirements/SR-008-patient-grant-and-revoke-of-clinical.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-009 | `docs/design-inputs/software-requirements/SR-009-administrative-personnel-non-clinical-data-scope.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-010 | `docs/design-inputs/software-requirements/SR-010-appointment-creation.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-011 | `docs/design-inputs/software-requirements/SR-011-appointment-visibility.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-012 | `docs/design-inputs/software-requirements/SR-012-clinical-entry-creation-with-required-fields.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-013 | `docs/design-inputs/software-requirements/SR-013-clinical-entry-file-attachments.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-014 | `docs/design-inputs/software-requirements/SR-014-user-group-management.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-015 | `docs/design-inputs/software-requirements/SR-015-per-group-module-enablement.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-016 | `docs/design-inputs/software-requirements/SR-016-modular-plugin-architecture.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-017 | `docs/design-inputs/software-requirements/SR-017-dicom-image-opening-and-rendering.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-018 | `docs/design-inputs/software-requirements/SR-018-dicom-viewer-controls.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-019 | `docs/design-inputs/software-requirements/SR-019-cross-browser-support.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-020 | `docs/design-inputs/software-requirements/SR-020-responsive-layout-across-devices.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-021 | `docs/design-inputs/software-requirements/SR-021-fhir-aligned-data-model.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-022 | `docs/design-inputs/software-requirements/SR-022-encryption-in-transit-and-at-rest.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-023 | `docs/design-inputs/software-requirements/SR-023-audit-logging-of-security-relevant-events.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-024 | `docs/design-inputs/software-requirements/SR-024-personal-data-erasure.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-025 | `docs/design-inputs/software-requirements/SR-025-password-complexity-policy.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-026 | `docs/design-inputs/software-requirements/SR-026-performance-budgets-for-routine-operations.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-027 | `docs/design-inputs/software-requirements/SR-027-usability-controls.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-028 | `docs/design-inputs/software-requirements/SR-028-traceable-version-controlled-development-records.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-029 | `docs/design-inputs/software-requirements/SR-029-account-lockout-after-failed-login-attempts.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-030 | `docs/design-inputs/software-requirements/SR-030-session-management.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-031 | `docs/design-inputs/software-requirements/SR-031-web-vulnerability-mitigations.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-032 | `docs/design-inputs/software-requirements/SR-032-role-constrained-user-account-creation.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-033 | `docs/design-inputs/software-requirements/SR-033-account-activation-via-email.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-034 | `docs/design-inputs/software-requirements/SR-034-account-deactivation-and-deletion-by-system.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-035 | `docs/design-inputs/software-requirements/SR-035-patient-notification-and-confirmation-of-scheduled.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-036 | `docs/design-inputs/software-requirements/SR-036-clinical-data-access-grant-on-appointment.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-037 | `docs/design-inputs/software-requirements/SR-037-design-token-based-theming-foundation.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-038 | `docs/design-inputs/software-requirements/SR-038-light-and-dark-theme-modes.md` | no TS verifies this SR (unverified by specification) |
| W1 | SR-039 | `docs/design-inputs/software-requirements/SR-039-theme-mode-toggle-default-and-persistence.md` | no TS verifies this SR (unverified by specification) |
| W2 | SR-001 | `docs/design-inputs/software-requirements/SR-001-browser-accessible-web-application-over-https.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-002 | `docs/design-inputs/software-requirements/SR-002-email-and-password-authentication.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-003 | `docs/design-inputs/software-requirements/SR-003-unique-user-account-and-profile-view.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-004 | `docs/design-inputs/software-requirements/SR-004-user-type-assignment.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-005 | `docs/design-inputs/software-requirements/SR-005-role-based-access-control-enforcement.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-006 | `docs/design-inputs/software-requirements/SR-006-doctor-access-to-own-patients-clinical.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-007 | `docs/design-inputs/software-requirements/SR-007-patient-access-to-own-personal-and.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-008 | `docs/design-inputs/software-requirements/SR-008-patient-grant-and-revoke-of-clinical.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-009 | `docs/design-inputs/software-requirements/SR-009-administrative-personnel-non-clinical-data-scope.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-010 | `docs/design-inputs/software-requirements/SR-010-appointment-creation.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-011 | `docs/design-inputs/software-requirements/SR-011-appointment-visibility.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-012 | `docs/design-inputs/software-requirements/SR-012-clinical-entry-creation-with-required-fields.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-013 | `docs/design-inputs/software-requirements/SR-013-clinical-entry-file-attachments.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-014 | `docs/design-inputs/software-requirements/SR-014-user-group-management.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-015 | `docs/design-inputs/software-requirements/SR-015-per-group-module-enablement.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-016 | `docs/design-inputs/software-requirements/SR-016-modular-plugin-architecture.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-017 | `docs/design-inputs/software-requirements/SR-017-dicom-image-opening-and-rendering.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-018 | `docs/design-inputs/software-requirements/SR-018-dicom-viewer-controls.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-019 | `docs/design-inputs/software-requirements/SR-019-cross-browser-support.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-020 | `docs/design-inputs/software-requirements/SR-020-responsive-layout-across-devices.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-021 | `docs/design-inputs/software-requirements/SR-021-fhir-aligned-data-model.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-022 | `docs/design-inputs/software-requirements/SR-022-encryption-in-transit-and-at-rest.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-023 | `docs/design-inputs/software-requirements/SR-023-audit-logging-of-security-relevant-events.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-024 | `docs/design-inputs/software-requirements/SR-024-personal-data-erasure.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-025 | `docs/design-inputs/software-requirements/SR-025-password-complexity-policy.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-026 | `docs/design-inputs/software-requirements/SR-026-performance-budgets-for-routine-operations.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-027 | `docs/design-inputs/software-requirements/SR-027-usability-controls.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-028 | `docs/design-inputs/software-requirements/SR-028-traceable-version-controlled-development-records.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-029 | `docs/design-inputs/software-requirements/SR-029-account-lockout-after-failed-login-attempts.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-030 | `docs/design-inputs/software-requirements/SR-030-session-management.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-031 | `docs/design-inputs/software-requirements/SR-031-web-vulnerability-mitigations.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-032 | `docs/design-inputs/software-requirements/SR-032-role-constrained-user-account-creation.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-033 | `docs/design-inputs/software-requirements/SR-033-account-activation-via-email.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-034 | `docs/design-inputs/software-requirements/SR-034-account-deactivation-and-deletion-by-system.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-035 | `docs/design-inputs/software-requirements/SR-035-patient-notification-and-confirmation-of-scheduled.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-036 | `docs/design-inputs/software-requirements/SR-036-clinical-data-access-grant-on-appointment.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-037 | `docs/design-inputs/software-requirements/SR-037-design-token-based-theming-foundation.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-038 | `docs/design-inputs/software-requirements/SR-038-light-and-dark-theme-modes.md` | no TR verifies this SR (unverified by evidence) |
| W2 | SR-039 | `docs/design-inputs/software-requirements/SR-039-theme-mode-toggle-default-and-persistence.md` | no TR verifies this SR (unverified by evidence) |
| W5 | TASK-132 | `docs/design-outputs/tasks/TASK-132-clinical-entries-view-completeness-remediation.md` | approved but links to TASK-101 (draft) |
| W7 | TASK-001 | `docs/design-outputs/tasks/TASK-001-monorepo-structure-tooling.md` | approved TASK whose SR NFR-006 has no TS |
| W7 | TASK-001 | `docs/design-outputs/tasks/TASK-001-monorepo-structure-tooling.md` | approved TASK whose SR SR-028 has no TS |
| W7 | TASK-002 | `docs/design-outputs/tasks/TASK-002-backend-fastapi-app-skeleton.md` | approved TASK whose SR SR-001 has no TS |
| W7 | TASK-003 | `docs/design-outputs/tasks/TASK-003-config-secrets-management.md` | approved TASK whose SR NFR-007 has no TS |
| W7 | TASK-004 | `docs/design-outputs/tasks/TASK-004-docker-compose-topology-reverse-proxy.md` | approved TASK whose SR SR-001 has no TS |
| W7 | TASK-004 | `docs/design-outputs/tasks/TASK-004-docker-compose-topology-reverse-proxy.md` | approved TASK whose SR SR-022 has no TS |
| W7 | TASK-005 | `docs/design-outputs/tasks/TASK-005-ci-pipeline.md` | approved TASK whose SR NFR-006 has no TS |
| W7 | TASK-005 | `docs/design-outputs/tasks/TASK-005-ci-pipeline.md` | approved TASK whose SR SR-028 has no TS |
| W7 | TASK-010 | `docs/design-outputs/tasks/TASK-010-sqlalchemy-domain-models-fhir-aligned.md` | approved TASK whose SR SR-021 has no TS |
| W7 | TASK-010 | `docs/design-outputs/tasks/TASK-010-sqlalchemy-domain-models-fhir-aligned.md` | approved TASK whose SR SR-003 has no TS |
| W7 | TASK-010 | `docs/design-outputs/tasks/TASK-010-sqlalchemy-domain-models-fhir-aligned.md` | approved TASK whose SR SR-004 has no TS |
| W7 | TASK-011 | `docs/design-outputs/tasks/TASK-011-alembic-initial-migration-constraints.md` | approved TASK whose SR SR-003 has no TS |
| W7 | TASK-011 | `docs/design-outputs/tasks/TASK-011-alembic-initial-migration-constraints.md` | approved TASK whose SR SR-032 has no TS |
| W7 | TASK-011 | `docs/design-outputs/tasks/TASK-011-alembic-initial-migration-constraints.md` | approved TASK whose SR SR-010 has no TS |
| W7 | TASK-012 | `docs/design-outputs/tasks/TASK-012-typed-repositories.md` | approved TASK whose SR SR-031 has no TS |
| W7 | TASK-013 | `docs/design-outputs/tasks/TASK-013-encryption-at-rest-config-key-hooks.md` | approved TASK whose SR SR-022 has no TS |
| W7 | TASK-014 | `docs/design-outputs/tasks/TASK-014-append-only-auditservice.md` | approved TASK whose SR SR-023 has no TS |
| W7 | TASK-020 | `docs/design-outputs/tasks/TASK-020-passwordservice-policy-argon2id.md` | approved TASK whose SR SR-025 has no TS |
| W7 | TASK-020 | `docs/design-outputs/tasks/TASK-020-passwordservice-policy-argon2id.md` | approved TASK whose SR SR-002 has no TS |
| W7 | TASK-021 | `docs/design-outputs/tasks/TASK-021-sessionservice-redis-opaque-tokens.md` | approved TASK whose SR SR-030 has no TS |
| W7 | TASK-022 | `docs/design-outputs/tasks/TASK-022-hardened-session-cookie-csrf-token.md` | approved TASK whose SR SR-030 has no TS |
| W7 | TASK-022 | `docs/design-outputs/tasks/TASK-022-hardened-session-cookie-csrf-token.md` | approved TASK whose SR SR-031 has no TS |
| W7 | TASK-023 | `docs/design-outputs/tasks/TASK-023-login-flow.md` | approved TASK whose SR SR-002 has no TS |
| W7 | TASK-023 | `docs/design-outputs/tasks/TASK-023-login-flow.md` | approved TASK whose SR SR-029 has no TS |
| W7 | TASK-024 | `docs/design-outputs/tasks/TASK-024-account-lockout.md` | approved TASK whose SR SR-029 has no TS |
| W7 | TASK-025 | `docs/design-outputs/tasks/TASK-025-api-auth-session-dependency-deny-by.md` | approved TASK whose SR SR-005 has no TS |
| W7 | TASK-025 | `docs/design-outputs/tasks/TASK-025-api-auth-session-dependency-deny-by.md` | approved TASK whose SR SR-031 has no TS |
| W7 | TASK-026 | `docs/design-outputs/tasks/TASK-026-rfc-7807-error-handlers.md` | approved TASK whose SR SR-027 has no TS |
| W7 | TASK-027 | `docs/design-outputs/tasks/TASK-027-authorizationservice-rbac-ownership.md` | approved TASK whose SR SR-005 has no TS |
| W7 | TASK-027 | `docs/design-outputs/tasks/TASK-027-authorizationservice-rbac-ownership.md` | approved TASK whose SR SR-006 has no TS |
| W7 | TASK-027 | `docs/design-outputs/tasks/TASK-027-authorizationservice-rbac-ownership.md` | approved TASK whose SR SR-007 has no TS |
| W7 | TASK-028 | `docs/design-outputs/tasks/TASK-028-consentservice-effective-access-union.md` | approved TASK whose SR SR-008 has no TS |
| W7 | TASK-028 | `docs/design-outputs/tasks/TASK-028-consentservice-effective-access-union.md` | approved TASK whose SR SR-036 has no TS |
| W7 | TASK-029 | `docs/design-outputs/tasks/TASK-029-admin-non-clinical-projection.md` | approved TASK whose SR SR-009 has no TS |
| W7 | TASK-030 | `docs/design-outputs/tasks/TASK-030-accountservice-create-profile.md` | approved TASK whose SR SR-003 has no TS |
| W7 | TASK-030 | `docs/design-outputs/tasks/TASK-030-accountservice-create-profile.md` | approved TASK whose SR SR-004 has no TS |
| W7 | TASK-030 | `docs/design-outputs/tasks/TASK-030-accountservice-create-profile.md` | approved TASK whose SR SR-032 has no TS |
| W7 | TASK-031 | `docs/design-outputs/tasks/TASK-031-celery-base-email-tasks.md` | approved TASK whose SR SR-033 has no TS |
| W7 | TASK-031 | `docs/design-outputs/tasks/TASK-031-celery-base-email-tasks.md` | approved TASK whose SR SR-035 has no TS |
| W7 | TASK-032 | `docs/design-outputs/tasks/TASK-032-account-activation-72h-token.md` | approved TASK whose SR SR-033 has no TS |
| W7 | TASK-033 | `docs/design-outputs/tasks/TASK-033-account-deactivate-reactivate.md` | approved TASK whose SR SR-034 has no TS |
| W7 | TASK-034 | `docs/design-outputs/tasks/TASK-034-worker-session-kill-propagation.md` | approved TASK whose SR SR-034 has no TS |
| W7 | TASK-034 | `docs/design-outputs/tasks/TASK-034-worker-session-kill-propagation.md` | approved TASK whose SR SR-030 has no TS |
| W7 | TASK-035 | `docs/design-outputs/tasks/TASK-035-erasure-anonymize-retrieval-code.md` | approved TASK whose SR SR-024 has no TS |
| W7 | TASK-035 | `docs/design-outputs/tasks/TASK-035-erasure-anonymize-retrieval-code.md` | approved TASK whose SR SR-034 has no TS |
| W7 | TASK-036 | `docs/design-outputs/tasks/TASK-036-worker-5-year-permanent-erasure.md` | approved TASK whose SR SR-024 has no TS |
| W7 | TASK-040 | `docs/design-outputs/tasks/TASK-040-group-crud.md` | approved TASK whose SR SR-014 has no TS |
| W7 | TASK-041 | `docs/design-outputs/tasks/TASK-041-group-membership-automatic-manual.md` | approved TASK whose SR SR-014 has no TS |
| W7 | TASK-041 | `docs/design-outputs/tasks/TASK-041-group-membership-automatic-manual.md` | approved TASK whose SR SR-004 has no TS |
| W7 | TASK-042 | `docs/design-outputs/tasks/TASK-042-per-group-module-enablement.md` | approved TASK whose SR SR-015 has no TS |
| W7 | TASK-043 | `docs/design-outputs/tasks/TASK-043-moduleaccessguard.md` | approved TASK whose SR SR-015 has no TS |
| W7 | TASK-044 | `docs/design-outputs/tasks/TASK-044-clinical-entry-create-list.md` | approved TASK whose SR SR-012 has no TS |
| W7 | TASK-044 | `docs/design-outputs/tasks/TASK-044-clinical-entry-create-list.md` | approved TASK whose SR SR-006 has no TS |
| W7 | TASK-044 | `docs/design-outputs/tasks/TASK-044-clinical-entry-create-list.md` | approved TASK whose SR SR-007 has no TS |
| W7 | TASK-045 | `docs/design-outputs/tasks/TASK-045-attachment-upload-minio-pydicom-validation.md` | approved TASK whose SR SR-013 has no TS |
| W7 | TASK-045 | `docs/design-outputs/tasks/TASK-045-attachment-upload-minio-pydicom-validation.md` | approved TASK whose SR SR-022 has no TS |
| W7 | TASK-046 | `docs/design-outputs/tasks/TASK-046-attachment-authorized-fetch.md` | approved TASK whose SR SR-013 has no TS |
| W7 | TASK-046 | `docs/design-outputs/tasks/TASK-046-attachment-authorized-fetch.md` | approved TASK whose SR SR-005 has no TS |
| W7 | TASK-046 | `docs/design-outputs/tasks/TASK-046-attachment-authorized-fetch.md` | approved TASK whose SR SR-022 has no TS |
| W7 | TASK-047 | `docs/design-outputs/tasks/TASK-047-appointment-create.md` | approved TASK whose SR SR-010 has no TS |
| W7 | TASK-048 | `docs/design-outputs/tasks/TASK-048-appointment-state-machine-confirm-decline.md` | approved TASK whose SR SR-035 has no TS |
| W7 | TASK-049 | `docs/design-outputs/tasks/TASK-049-confirm-grant-decline-revoke-consent.md` | approved TASK whose SR SR-036 has no TS |
| W7 | TASK-050 | `docs/design-outputs/tasks/TASK-050-appointment-notification-dispatch.md` | approved TASK whose SR SR-035 has no TS |
| W7 | TASK-051 | `docs/design-outputs/tasks/TASK-051-appointment-visibility-scoping.md` | approved TASK whose SR SR-011 has no TS |
| W7 | TASK-051 | `docs/design-outputs/tasks/TASK-051-appointment-visibility-scoping.md` | approved TASK whose SR SR-035 has no TS |
| W7 | TASK-060 | `docs/design-outputs/tasks/TASK-060-auth-session-endpoints.md` | approved TASK whose SR SR-002 has no TS |
| W7 | TASK-060 | `docs/design-outputs/tasks/TASK-060-auth-session-endpoints.md` | approved TASK whose SR SR-029 has no TS |
| W7 | TASK-060 | `docs/design-outputs/tasks/TASK-060-auth-session-endpoints.md` | approved TASK whose SR SR-030 has no TS |
| W7 | TASK-060 | `docs/design-outputs/tasks/TASK-060-auth-session-endpoints.md` | approved TASK whose SR SR-025 has no TS |
| W7 | TASK-061 | `docs/design-outputs/tasks/TASK-061-account-activation-endpoints.md` | approved TASK whose SR SR-032 has no TS |
| W7 | TASK-061 | `docs/design-outputs/tasks/TASK-061-account-activation-endpoints.md` | approved TASK whose SR SR-033 has no TS |
| W7 | TASK-062 | `docs/design-outputs/tasks/TASK-062-account-lifecycle-anonymized-data-retrieval-endpoints.md` | approved TASK whose SR SR-034 has no TS |
| W7 | TASK-062 | `docs/design-outputs/tasks/TASK-062-account-lifecycle-anonymized-data-retrieval-endpoints.md` | approved TASK whose SR SR-024 has no TS |
| W7 | TASK-063 | `docs/design-outputs/tasks/TASK-063-groups-module-enablement-endpoints.md` | approved TASK whose SR SR-014 has no TS |
| W7 | TASK-063 | `docs/design-outputs/tasks/TASK-063-groups-module-enablement-endpoints.md` | approved TASK whose SR SR-015 has no TS |
| W7 | TASK-063 | `docs/design-outputs/tasks/TASK-063-groups-module-enablement-endpoints.md` | approved TASK whose SR SR-016 has no TS |
| W7 | TASK-064 | `docs/design-outputs/tasks/TASK-064-consent-endpoints.md` | approved TASK whose SR SR-008 has no TS |
| W7 | TASK-064 | `docs/design-outputs/tasks/TASK-064-consent-endpoints.md` | approved TASK whose SR SR-036 has no TS |
| W7 | TASK-065 | `docs/design-outputs/tasks/TASK-065-appointment-endpoints.md` | approved TASK whose SR SR-010 has no TS |
| W7 | TASK-065 | `docs/design-outputs/tasks/TASK-065-appointment-endpoints.md` | approved TASK whose SR SR-011 has no TS |
| W7 | TASK-065 | `docs/design-outputs/tasks/TASK-065-appointment-endpoints.md` | approved TASK whose SR SR-035 has no TS |
| W7 | TASK-065 | `docs/design-outputs/tasks/TASK-065-appointment-endpoints.md` | approved TASK whose SR SR-036 has no TS |
| W7 | TASK-066 | `docs/design-outputs/tasks/TASK-066-clinical-entry-attachment-endpoints.md` | approved TASK whose SR SR-012 has no TS |
| W7 | TASK-066 | `docs/design-outputs/tasks/TASK-066-clinical-entry-attachment-endpoints.md` | approved TASK whose SR SR-013 has no TS |
| W7 | TASK-066 | `docs/design-outputs/tasks/TASK-066-clinical-entry-attachment-endpoints.md` | approved TASK whose SR SR-005 has no TS |
| W7 | TASK-067 | `docs/design-outputs/tasks/TASK-067-current-user-me-endpoints.md` | approved TASK whose SR SR-003 has no TS |
| W7 | TASK-067 | `docs/design-outputs/tasks/TASK-067-current-user-me-endpoints.md` | approved TASK whose SR SR-015 has no TS |
| W7 | TASK-068 | `docs/design-outputs/tasks/TASK-068-openapi-3-1-contract-finalization-typed.md` | approved TASK whose SR NFR-006 has no TS |
| W7 | TASK-068 | `docs/design-outputs/tasks/TASK-068-openapi-3-1-contract-finalization-typed.md` | approved TASK whose SR SR-031 has no TS |
| W7 | TASK-069 | `docs/design-outputs/tasks/TASK-069-security-headers-middleware-csrf-enforcement.md` | approved TASK whose SR SR-031 has no TS |
| W7 | TASK-070 | `docs/design-outputs/tasks/TASK-070-module-discovery-modulemanifest-registry.md` | approved TASK whose SR SR-016 has no TS |
| W7 | TASK-071 | `docs/design-outputs/tasks/TASK-071-platformservices-facade-sole-phi-path.md` | approved TASK whose SR SR-016 has no TS |
| W7 | TASK-071 | `docs/design-outputs/tasks/TASK-071-platformservices-facade-sole-phi-path.md` | approved TASK whose SR SR-005 has no TS |
| W7 | TASK-071 | `docs/design-outputs/tasks/TASK-071-platformservices-facade-sole-phi-path.md` | approved TASK whose SR SR-023 has no TS |
| W7 | TASK-072 | `docs/design-outputs/tasks/TASK-072-routerregistry-mount-moduleaccessguard-gating.md` | approved TASK whose SR SR-016 has no TS |
| W7 | TASK-072 | `docs/design-outputs/tasks/TASK-072-routerregistry-mount-moduleaccessguard-gating.md` | approved TASK whose SR SR-015 has no TS |
| W7 | TASK-073 | `docs/design-outputs/tasks/TASK-073-dicom-module-backend-authorized-bytes.md` | approved TASK whose SR SR-016 has no TS |
| W7 | TASK-073 | `docs/design-outputs/tasks/TASK-073-dicom-module-backend-authorized-bytes.md` | approved TASK whose SR SR-017 has no TS |
| W7 | TASK-080 | `docs/design-outputs/tasks/TASK-080-typed-api-client-cookie-csrf-tanstack.md` | approved TASK whose SR SR-031 has no TS |
| W7 | TASK-080 | `docs/design-outputs/tasks/TASK-080-typed-api-client-cookie-csrf-tanstack.md` | approved TASK whose SR NFR-006 has no TS |
| W7 | TASK-081 | `docs/design-outputs/tasks/TASK-081-responsive-layout-mui-theme.md` | approved TASK whose SR SR-020 has no TS |
| W7 | TASK-081 | `docs/design-outputs/tasks/TASK-081-responsive-layout-mui-theme.md` | approved TASK whose SR NFR-003 has no TS |
| W7 | TASK-082 | `docs/design-outputs/tasks/TASK-082-role-based-navigation.md` | approved TASK whose SR SR-027 has no TS |
| W7 | TASK-083 | `docs/design-outputs/tasks/TASK-083-reusable-confirmation-dialog-for-destructive-actions.md` | approved TASK whose SR SR-027 has no TS |
| W7 | TASK-083 | `docs/design-outputs/tasks/TASK-083-reusable-confirmation-dialog-for-destructive-actions.md` | approved TASK whose SR NFR-009 has no TS |
| W7 | TASK-084 | `docs/design-outputs/tasks/TASK-084-error-boundary-toast-rendering-rfc-7807.md` | approved TASK whose SR SR-027 has no TS |
| W7 | TASK-085 | `docs/design-outputs/tasks/TASK-085-login-ui-session-handling.md` | approved TASK whose SR SR-002 has no TS |
| W7 | TASK-086 | `docs/design-outputs/tasks/TASK-086-account-activation-set-password-ui.md` | approved TASK whose SR SR-033 has no TS |
| W7 | TASK-086 | `docs/design-outputs/tasks/TASK-086-account-activation-set-password-ui.md` | approved TASK whose SR SR-025 has no TS |
| W7 | TASK-087 | `docs/design-outputs/tasks/TASK-087-change-password-ui-with-live-policy.md` | approved TASK whose SR SR-025 has no TS |
| W7 | TASK-088 | `docs/design-outputs/tasks/TASK-088-inactivity-warning-session-extend.md` | approved TASK whose SR SR-030 has no TS |
| W7 | TASK-090 | `docs/design-outputs/tasks/TASK-090-profile-view.md` | approved TASK whose SR SR-003 has no TS |
| W7 | TASK-090 | `docs/design-outputs/tasks/TASK-090-profile-view.md` | approved TASK whose SR SR-007 has no TS |
| W7 | TASK-091 | `docs/design-outputs/tasks/TASK-091-doctor-patient-list.md` | approved TASK whose SR SR-006 has no TS |
| W7 | TASK-092 | `docs/design-outputs/tasks/TASK-092-clinical-entries-view-create-attachment-upload.md` | approved TASK whose SR SR-012 has no TS |
| W7 | TASK-092 | `docs/design-outputs/tasks/TASK-092-clinical-entries-view-create-attachment-upload.md` | approved TASK whose SR SR-013 has no TS |
| W7 | TASK-092 | `docs/design-outputs/tasks/TASK-092-clinical-entries-view-create-attachment-upload.md` | approved TASK whose SR SR-006 has no TS |
| W7 | TASK-092 | `docs/design-outputs/tasks/TASK-092-clinical-entries-view-create-attachment-upload.md` | approved TASK whose SR SR-007 has no TS |
| W7 | TASK-093 | `docs/design-outputs/tasks/TASK-093-appointments-list-create-confirm-decline.md` | approved TASK whose SR SR-010 has no TS |
| W7 | TASK-093 | `docs/design-outputs/tasks/TASK-093-appointments-list-create-confirm-decline.md` | approved TASK whose SR SR-011 has no TS |
| W7 | TASK-093 | `docs/design-outputs/tasks/TASK-093-appointments-list-create-confirm-decline.md` | approved TASK whose SR SR-035 has no TS |
| W7 | TASK-094 | `docs/design-outputs/tasks/TASK-094-consent-grant-revoke-unified-view.md` | approved TASK whose SR SR-008 has no TS |
| W7 | TASK-094 | `docs/design-outputs/tasks/TASK-094-consent-grant-revoke-unified-view.md` | approved TASK whose SR SR-036 has no TS |
| W7 | TASK-094 | `docs/design-outputs/tasks/TASK-094-consent-grant-revoke-unified-view.md` | approved TASK whose SR SR-027 has no TS |
| W7 | TASK-095 | `docs/design-outputs/tasks/TASK-095-admin-account-management.md` | approved TASK whose SR SR-009 has no TS |
| W7 | TASK-095 | `docs/design-outputs/tasks/TASK-095-admin-account-management.md` | approved TASK whose SR SR-032 has no TS |
| W7 | TASK-095 | `docs/design-outputs/tasks/TASK-095-admin-account-management.md` | approved TASK whose SR SR-034 has no TS |
| W7 | TASK-096 | `docs/design-outputs/tasks/TASK-096-admin-groups-module-enablement-ui.md` | approved TASK whose SR SR-014 has no TS |
| W7 | TASK-096 | `docs/design-outputs/tasks/TASK-096-admin-groups-module-enablement-ui.md` | approved TASK whose SR SR-015 has no TS |
| W7 | TASK-117 | `docs/design-outputs/tasks/TASK-117-database-migration-on-bring-up-remediation.md` | approved TASK whose SR SR-001 has no TS |
| W7 | TASK-117 | `docs/design-outputs/tasks/TASK-117-database-migration-on-bring-up-remediation.md` | approved TASK whose SR SR-003 has no TS |
| W7 | TASK-118 | `docs/design-outputs/tasks/TASK-118-wire-account-lockout-into-the-login.md` | approved TASK whose SR SR-029 has no TS |
| W7 | TASK-119 | `docs/design-outputs/tasks/TASK-119-password-policy-errors-as-400-activation.md` | approved TASK whose SR SR-025 has no TS |
| W7 | TASK-119 | `docs/design-outputs/tasks/TASK-119-password-policy-errors-as-400-activation.md` | approved TASK whose SR SR-027 has no TS |
| W7 | TASK-119 | `docs/design-outputs/tasks/TASK-119-password-policy-errors-as-400-activation.md` | approved TASK whose SR SR-033 has no TS |
| W7 | TASK-120 | `docs/design-outputs/tasks/TASK-120-wire-admin-non-clinical-projection-into.md` | approved TASK whose SR SR-009 has no TS |
| W7 | TASK-121 | `docs/design-outputs/tasks/TASK-121-erasure-retrieval-code-delivery-deadline-re.md` | approved TASK whose SR SR-024 has no TS |
| W7 | TASK-121 | `docs/design-outputs/tasks/TASK-121-erasure-retrieval-code-delivery-deadline-re.md` | approved TASK whose SR SR-034 has no TS |
| W7 | TASK-122 | `docs/design-outputs/tasks/TASK-122-group-name-uniqueness-db-constraint-remediation.md` | approved TASK whose SR SR-014 has no TS |
| W7 | TASK-123 | `docs/design-outputs/tasks/TASK-123-doctor-patient-roster-endpoint-remediation.md` | approved TASK whose SR SR-006 has no TS |
| W7 | TASK-124 | `docs/design-outputs/tasks/TASK-124-appointment-notification-resilience-remediation.md` | approved TASK whose SR SR-035 has no TS |
| W7 | TASK-125 | `docs/design-outputs/tasks/TASK-125-attachment-upload-via-multipart-streaming-remediation.md` | approved TASK whose SR SR-013 has no TS |
| W7 | TASK-126 | `docs/design-outputs/tasks/TASK-126-attachment-listing-endpoint-clinical-entry-author.md` | approved TASK whose SR SR-012 has no TS |
| W7 | TASK-126 | `docs/design-outputs/tasks/TASK-126-attachment-listing-endpoint-clinical-entry-author.md` | approved TASK whose SR SR-013 has no TS |
| W7 | TASK-127 | `docs/design-outputs/tasks/TASK-127-surface-the-security-model-in-openapi.md` | approved TASK whose SR SR-031 has no TS |
| W7 | TASK-127 | `docs/design-outputs/tasks/TASK-127-surface-the-security-model-in-openapi.md` | approved TASK whose SR NFR-006 has no TS |
| W7 | TASK-128 | `docs/design-outputs/tasks/TASK-128-app-wide-csrf-enforcement-remediation.md` | approved TASK whose SR SR-031 has no TS |
| W7 | TASK-129 | `docs/design-outputs/tasks/TASK-129-wire-module-registry-sync-into-startup.md` | approved TASK whose SR SR-016 has no TS |
| W7 | TASK-129 | `docs/design-outputs/tasks/TASK-129-wire-module-registry-sync-into-startup.md` | approved TASK whose SR SR-023 has no TS |
| W7 | TASK-130 | `docs/design-outputs/tasks/TASK-130-fix-activation-ui-to-match-the.md` | approved TASK whose SR SR-033 has no TS |
| W7 | TASK-131 | `docs/design-outputs/tasks/TASK-131-fix-forced-password-change-gate-remediation.md` | approved TASK whose SR SR-025 has no TS |
| W7 | TASK-132 | `docs/design-outputs/tasks/TASK-132-clinical-entries-view-completeness-remediation.md` | approved TASK whose SR SR-012 has no TS |
| W7 | TASK-132 | `docs/design-outputs/tasks/TASK-132-clinical-entries-view-completeness-remediation.md` | approved TASK whose SR SR-013 has no TS |
| W7 | TASK-132 | `docs/design-outputs/tasks/TASK-132-clinical-entries-view-completeness-remediation.md` | approved TASK whose SR SR-015 has no TS |
| W7 | TASK-132 | `docs/design-outputs/tasks/TASK-132-clinical-entries-view-completeness-remediation.md` | approved TASK whose SR SR-016 has no TS |
| W7 | TASK-133 | `docs/design-outputs/tasks/TASK-133-admin-accounts-view-completeness-remediation.md` | approved TASK whose SR SR-032 has no TS |
| W7 | TASK-133 | `docs/design-outputs/tasks/TASK-133-admin-accounts-view-completeness-remediation.md` | approved TASK whose SR SR-034 has no TS |
| W7 | TASK-134 | `docs/design-outputs/tasks/TASK-134-manual-add-member-ui-for-groups.md` | approved TASK whose SR SR-014 has no TS |
| W7 | TASK-149 | `docs/design-outputs/tasks/TASK-149-design-token-theme-foundation.md` | approved TASK whose SR SR-037 has no TS |
| W7 | TASK-149 | `docs/design-outputs/tasks/TASK-149-design-token-theme-foundation.md` | approved TASK whose SR SR-038 has no TS |
| W7 | TASK-150 | `docs/design-outputs/tasks/TASK-150-medhub-component-identity-overrides.md` | approved TASK whose SR SR-037 has no TS |
| W7 | TASK-150 | `docs/design-outputs/tasks/TASK-150-medhub-component-identity-overrides.md` | approved TASK whose SR SR-038 has no TS |
| W7 | TASK-151 | `docs/design-outputs/tasks/TASK-151-theme-mode-toggle-and-persistence.md` | approved TASK whose SR SR-039 has no TS |
| W7 | TASK-151 | `docs/design-outputs/tasks/TASK-151-theme-mode-toggle-and-persistence.md` | approved TASK whose SR SR-038 has no TS |
| W7 | TASK-152 | `docs/design-outputs/tasks/TASK-152-screen-sweep-tokenization-both-modes.md` | approved TASK whose SR SR-037 has no TS |
| W7 | TASK-152 | `docs/design-outputs/tasks/TASK-152-screen-sweep-tokenization-both-modes.md` | approved TASK whose SR SR-038 has no TS |
| W7 | TASK-153 | `docs/design-outputs/tasks/TASK-153-theming-test-coverage-and-contrast.md` | approved TASK whose SR SR-037 has no TS |
| W7 | TASK-153 | `docs/design-outputs/tasks/TASK-153-theming-test-coverage-and-contrast.md` | approved TASK whose SR SR-038 has no TS |
| W7 | TASK-153 | `docs/design-outputs/tasks/TASK-153-theming-test-coverage-and-contrast.md` | approved TASK whose SR SR-039 has no TS |

## Coverage

| SR | Title | TASKs | ADDs | TS | TR | RISKs mitigated |
|---|---|---|---|---|---|---|
| SR-001 | Browser-accessible web application over  | 3 | — | — | — | — |
| SR-002 | Email and password authentication | 5 | — | — | — | — |
| SR-003 | Unique user account and profile view | 6 | — | — | — | — |
| SR-004 | User type assignment | 3 | — | — | — | — |
| SR-005 | Role-based access control enforcement | 7 | — | — | — | — |
| SR-006 | Doctor access to own patients' clinical  | 6 | — | — | — | — |
| SR-007 | Patient access to own personal and clini | 4 | — | — | — | — |
| SR-008 | Patient grant and revoke of clinical-dat | 4 | — | — | — | — |
| SR-009 | Administrative personnel non-clinical da | 3 | — | — | — | — |
| SR-010 | Appointment creation | 4 | — | — | — | — |
| SR-011 | Appointment visibility | 3 | — | — | — | — |
| SR-012 | Clinical entry creation with required fi | 5 | — | — | — | — |
| SR-013 | Clinical entry file attachments | 8 | — | — | — | — |
| SR-014 | User group management | 6 | — | — | — | — |
| SR-015 | Per-group module enablement | 9 | — | — | — | — |
| SR-016 | Modular plugin architecture | 10 | — | — | — | — |
| SR-017 | DICOM image opening and rendering | 3 | — | — | — | — |
| SR-018 | DICOM viewer controls | 1 | — | — | — | — |
| SR-019 | Cross-browser support | 1 | — | — | — | — |
| SR-020 | Responsive layout across devices | 1 | — | — | — | — |
| SR-021 | FHIR-aligned data model | 1 | — | — | — | — |
| SR-022 | Encryption in transit and at rest | 4 | — | — | — | — |
| SR-023 | Audit logging of security-relevant event | 5 | — | — | — | — |
| SR-024 | Personal data erasure | 6 | — | — | — | — |
| SR-025 | Password complexity policy | 6 | — | — | — | — |
| SR-026 | Performance budgets for routine operatio | 3 | — | — | — | — |
| SR-027 | Usability controls | 6 | — | — | — | — |
| SR-028 | Traceable, version-controlled developmen | 5 | — | — | — | — |
| SR-029 | Account lockout after failed login attem | 5 | — | — | — | — |
| SR-030 | Session management | 7 | — | — | — | — |
| SR-031 | Web vulnerability mitigations | 10 | — | — | — | — |
| SR-032 | Role-constrained user account creation | 6 | — | — | — | — |
| SR-033 | Account activation via email | 7 | — | — | — | — |
| SR-034 | Account deactivation and deletion by sys | 8 | — | — | — | — |
| SR-035 | Patient notification and confirmation of | 8 | — | — | — | — |
| SR-036 | Clinical data access grant on appointmen | 6 | — | — | — | — |
| SR-037 | Design-token-based theming foundation | 4 | ADD-001 | — | — | — |
| SR-038 | Light and dark theme modes with accessib | 5 | ADD-001 | — | — | — |
| SR-039 | Theme mode toggle, system default, and p | 2 | ADD-001 | — | — | — |
