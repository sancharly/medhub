# Gap report — 2026-10-21

Scope: whole project  ·  Records scanned: 315  ·  Errors: 0  ·  Warnings: 74  ·  Safety class: B

Generated with the `medical-records:traceability-check` procedure (0.3.2) as a throwaway parser. `modified_after_approval` is not computed: only the MedTrace app can compute `approved_digest`.

## Record inventory

| Type | Count |
|---|---|
| `user-need` | 15 |
| `nfr` | 9 |
| `regulatory-requirement` | 11 |
| `software-requirement` | 39 |
| `architecture-doc` | 24 |
| `task` | 118 |
| `test-specification` | 13 |
| `risk` | 11 |
| `test-plan` | 1 |
| `test-report` | 1 |
| `soup` | 35 |
| `problem-report` | 33 |
| `change-request` | 0 |
| `lifecycle-plan` | 5 |
| `release` | 0 |
| `source-ref` | 0 |

## Errors

None.

## Warnings and class-gated findings

| Check | Count |
|---|---|
| W1 | 3 |
| W2 | 10 |
| W5 | 14 |
| W7 | 9 |
| risk_control_unverified | 2 |
| soup_anomaly_review_stale | 35 |
| soup_unintegrated | 1 |

| Check | Element | File | Problem |
|---|---|---|---|
| W1 | SR-017 | `docs/design-inputs/software-requirements/SR-017-dicom-image-opening-and-rendering.md` | no TS verifies this SR |
| W1 | SR-018 | `docs/design-inputs/software-requirements/SR-018-dicom-viewer-controls.md` | no TS verifies this SR |
| W1 | SR-026 | `docs/design-inputs/software-requirements/SR-026-performance-budgets-for-routine-operations.md` | no TS verifies this SR |
| W2 | SR-003 | `docs/design-inputs/software-requirements/SR-003-unique-user-account-and-profile-view.md` | no TR verifies this SR |
| W2 | SR-004 | `docs/design-inputs/software-requirements/SR-004-user-type-assignment.md` | no TR verifies this SR |
| W2 | SR-010 | `docs/design-inputs/software-requirements/SR-010-appointment-creation.md` | no TR verifies this SR |
| W2 | SR-017 | `docs/design-inputs/software-requirements/SR-017-dicom-image-opening-and-rendering.md` | no TR verifies this SR |
| W2 | SR-018 | `docs/design-inputs/software-requirements/SR-018-dicom-viewer-controls.md` | no TR verifies this SR |
| W2 | SR-019 | `docs/design-inputs/software-requirements/SR-019-cross-browser-support.md` | no TR verifies this SR |
| W2 | SR-021 | `docs/design-inputs/software-requirements/SR-021-fhir-aligned-data-model.md` | no TR verifies this SR |
| W2 | SR-023 | `docs/design-inputs/software-requirements/SR-023-audit-logging-of-security-relevant-events.md` | no TR verifies this SR |
| W2 | SR-026 | `docs/design-inputs/software-requirements/SR-026-performance-budgets-for-routine-operations.md` | no TR verifies this SR |
| W2 | SR-031 | `docs/design-inputs/software-requirements/SR-031-web-vulnerability-mitigations.md` | no TR verifies this SR |
| W5 | ADD-005 | `docs/design-outputs/architecture/ADD-005-api-layer-routers.md` | approved but links to RISK-007 (in_review) |
| W5 | ADD-012 | `docs/design-outputs/architecture/ADD-012-attachment-service.md` | approved but links to RISK-007 (in_review) |
| W5 | ADD-015 | `docs/design-outputs/architecture/ADD-015-dicom-module-backend.md` | approved but links to RISK-007 (in_review) |
| W5 | ADD-016 | `docs/design-outputs/architecture/ADD-016-persistence.md` | approved but links to RISK-007 (in_review) |
| W5 | SR-001 | `docs/design-inputs/software-requirements/SR-001-browser-accessible-web-application-over-https.md` | approved but links to RISK-010 (in_review) |
| W5 | SR-019 | `docs/design-inputs/software-requirements/SR-019-cross-browser-support.md` | approved but links to RR-010 (in_review) |
| W5 | SR-022 | `docs/design-inputs/software-requirements/SR-022-encryption-in-transit-and-at-rest.md` | approved but links to RISK-007 (in_review) |
| W5 | SR-022 | `docs/design-inputs/software-requirements/SR-022-encryption-in-transit-and-at-rest.md` | approved but links to RISK-010 (in_review) |
| W5 | SR-025 | `docs/design-inputs/software-requirements/SR-025-password-complexity-policy.md` | approved but links to RISK-010 (in_review) |
| W5 | SR-026 | `docs/design-inputs/software-requirements/SR-026-performance-budgets-for-routine-operations.md` | approved but links to RR-010 (in_review) |
| W5 | SR-026 | `docs/design-inputs/software-requirements/SR-026-performance-budgets-for-routine-operations.md` | approved but links to RISK-007 (in_review) |
| W5 | TASK-001 | `docs/design-outputs/tasks/TASK-001-monorepo-structure-tooling.md` | approved but links to SR-028 (in_review) |
| W5 | TASK-005 | `docs/design-outputs/tasks/TASK-005-ci-pipeline.md` | approved but links to SR-028 (in_review) |
| W5 | TASK-132 | `docs/design-outputs/tasks/TASK-132-clinical-entries-view-completeness-remediation.md` | approved but links to TASK-101 (draft) |
| W7 | TASK-001 | `docs/design-outputs/tasks/TASK-001-monorepo-structure-tooling.md` | approved TASK whose SR NFR-006 has no TS |
| W7 | TASK-003 | `docs/design-outputs/tasks/TASK-003-config-secrets-management.md` | approved TASK whose SR NFR-007 has no TS |
| W7 | TASK-005 | `docs/design-outputs/tasks/TASK-005-ci-pipeline.md` | approved TASK whose SR NFR-006 has no TS |
| W7 | TASK-068 | `docs/design-outputs/tasks/TASK-068-openapi-3-1-contract-finalization-typed.md` | approved TASK whose SR NFR-006 has no TS |
| W7 | TASK-073 | `docs/design-outputs/tasks/TASK-073-dicom-module-backend-authorized-bytes.md` | approved TASK whose SR SR-017 has no TS |
| W7 | TASK-080 | `docs/design-outputs/tasks/TASK-080-typed-api-client-cookie-csrf-tanstack.md` | approved TASK whose SR NFR-006 has no TS |
| W7 | TASK-081 | `docs/design-outputs/tasks/TASK-081-responsive-layout-mui-theme.md` | approved TASK whose SR NFR-003 has no TS |
| W7 | TASK-083 | `docs/design-outputs/tasks/TASK-083-reusable-confirmation-dialog-for-destructive-actions.md` | approved TASK whose SR NFR-009 has no TS |
| W7 | TASK-127 | `docs/design-outputs/tasks/TASK-127-surface-the-security-model-in-openapi.md` | approved TASK whose SR NFR-006 has no TS |
| risk_control_unverified | TASK-113 | `docs/design-outputs/tasks/TASK-113-security-review-of-auth-session-authz.md` | mitigating element reaches no test-report |
| risk_control_unverified | TASK-137 | `docs/design-outputs/tasks/TASK-137-capture-client-ip-in-authz-and-consent-audit.md` | mitigating element reaches no test-report |
| soup_anomaly_review_stale | SOUP-001 | `docs/soup/SOUP-001-python.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-002 | `docs/soup/SOUP-002-fastapi.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-003 | `docs/soup/SOUP-003-starlette.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-004 | `docs/soup/SOUP-004-uvicorn.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-005 | `docs/soup/SOUP-005-gunicorn.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-006 | `docs/soup/SOUP-006-pydantic.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-007 | `docs/soup/SOUP-007-pydantic-settings.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-008 | `docs/soup/SOUP-008-sqlalchemy.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-009 | `docs/soup/SOUP-009-alembic.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-010 | `docs/soup/SOUP-010-psycopg2-binary.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-011 | `docs/soup/SOUP-011-cryptography.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-012 | `docs/soup/SOUP-012-argon2-cffi.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-013 | `docs/soup/SOUP-013-redis-py.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-014 | `docs/soup/SOUP-014-celery.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-015 | `docs/soup/SOUP-015-pydicom.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-016 | `docs/soup/SOUP-016-fhir-resources.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-017 | `docs/soup/SOUP-017-python-multipart.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-018 | `docs/soup/SOUP-018-fakeredis.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-019 | `docs/soup/SOUP-019-boto3.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-020 | `docs/soup/SOUP-020-postgresql.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-021 | `docs/soup/SOUP-021-redis-server.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-022 | `docs/soup/SOUP-022-minio.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-023 | `docs/soup/SOUP-023-minio-client.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-024 | `docs/soup/SOUP-024-nginx.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-025 | `docs/soup/SOUP-025-react.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-026 | `docs/soup/SOUP-026-react-dom.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-027 | `docs/soup/SOUP-027-react-router.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-028 | `docs/soup/SOUP-028-tanstack-query.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-029 | `docs/soup/SOUP-029-mui-material.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-030 | `docs/soup/SOUP-030-mui-icons.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-031 | `docs/soup/SOUP-031-emotion-react.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-032 | `docs/soup/SOUP-032-emotion-styled.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-033 | `docs/soup/SOUP-033-openapi-fetch.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-034 | `docs/soup/SOUP-034-font-inter.md` | anomaly review missing or older than 365 days |
| soup_anomaly_review_stale | SOUP-035 | `docs/soup/SOUP-035-font-manrope.md` | anomaly review missing or older than 365 days |
| soup_unintegrated | SOUP-018 | `docs/soup/SOUP-018-fakeredis.md` | no architecture element links this SOUP |

## Coverage

| SR | ADDs | TS | TR | RISKs mitigated |
|---|---|---|---|---|
| SR-001 | ADD-005, ADD-018 | TS-011 | TR-001 | RISK-005, RISK-010, RISK-011 |
| SR-002 | ADD-006, ADD-019 | TS-001 | TR-001 | — |
| SR-003 | ADD-008, ADD-016, ADD-020 | TS-003 | — | RISK-002 |
| SR-004 | ADD-007, ADD-008, ADD-016, ADD-020 | TS-003 | — | RISK-002 |
| SR-005 | ADD-007, ADD-020 | TS-002 | TR-001 | RISK-001 |
| SR-006 | ADD-007, ADD-011, ADD-020 | TS-002 | TR-001 | RISK-001 |
| SR-007 | ADD-007, ADD-011, ADD-020 | TS-002 | TR-001 | RISK-001 |
| SR-008 | ADD-005, ADD-007, ADD-020 | TS-002 | TR-001 | RISK-001, RISK-004 |
| SR-009 | ADD-007, ADD-020 | TS-002 | TR-001 | RISK-001 |
| SR-010 | ADD-010, ADD-020 | TS-006 | — | — |
| SR-011 | ADD-007, ADD-010, ADD-020 | TS-002 | TR-001 | RISK-009 |
| SR-012 | ADD-011, ADD-020 | TS-007 | TR-001 | RISK-002 |
| SR-013 | ADD-012, ADD-020 | TS-007 | TR-001 | RISK-002 |
| SR-014 | ADD-009, ADD-020 | TS-005 | TR-001 | — |
| SR-015 | ADD-007, ADD-009, ADD-020, ADD-021 | TS-005 | TR-001 | — |
| SR-016 | ADD-014, ADD-015, ADD-020, ADD-021 | TS-010 | TR-001 | — |
| SR-017 | ADD-015, ADD-022 | — | — | RISK-003 |
| SR-018 | ADD-022 | — | — | RISK-003 |
| SR-019 | ADD-018 | TS-012 | — | RISK-003 |
| SR-020 | ADD-018 | TS-012 | TR-001 | — |
| SR-021 | ADD-016 | TS-008 | — | RISK-002 |
| SR-022 | ADD-012, ADD-016 | TS-008 | TR-001 | RISK-006, RISK-007, RISK-008, RISK-010, RISK-011 |
| SR-023 | ADD-013 | TS-009 | — | RISK-001, RISK-004, RISK-005, RISK-006 |
| SR-024 | ADD-008, ADD-017 | TS-004 | TR-001 | RISK-002, RISK-008 |
| SR-025 | ADD-006, ADD-019 | TS-001 | TR-001 | RISK-005, RISK-010 |
| SR-026 | ADD-005, ADD-012, ADD-022 | — | — | RISK-007 |
| SR-027 | ADD-018 | TS-012 | TR-001 | — |
| SR-028 | ADD-024 | TS-013 | TR-001 | RISK-007, RISK-010 |
| SR-029 | ADD-006 | TS-001 | TR-001 | RISK-005 |
| SR-030 | ADD-006, ADD-019 | TS-001 | TR-001 | RISK-005 |
| SR-031 | ADD-005, ADD-016, ADD-023 | TS-008, TS-011 | — | RISK-003, RISK-005 |
| SR-032 | ADD-008 | TS-003 | TR-001 | — |
| SR-033 | ADD-008, ADD-017, ADD-019 | TS-003 | TR-001 | RISK-009 |
| SR-034 | ADD-006, ADD-008, ADD-017 | TS-003 | TR-001 | — |
| SR-035 | ADD-010, ADD-017, ADD-020 | TS-006 | TR-001 | RISK-009 |
| SR-036 | ADD-007, ADD-010, ADD-020 | TS-002 | TR-001 | RISK-001, RISK-004 |
| SR-037 | ADD-001 | TS-012 | TR-001 | — |
| SR-038 | ADD-001 | TS-012 | TR-001 | — |
| SR-039 | ADD-001 | TS-012 | TR-001 | — |
