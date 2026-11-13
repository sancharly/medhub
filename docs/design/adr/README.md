# Architecture Decision Records (ADRs)

This folder records the significant architecture decisions for MedHub. One decision per file, following the template in the `architecture-designer` skill. ADRs are version-controlled design records that satisfy SR-028 (traceable, version-controlled development records) and NFR-005 / NFR-006 (MDR/FDA and IEC 62304 documentation).

| ADR                                                       | Decision                                                                                         | Status   |
|-----------------------------------------------------------|--------------------------------------------------------------------------------------------------|----------|
| [ADR-0001](0001-overall-architecture-style.md)            | Modular monolith with a runtime plugin/module mechanism                                          | Accepted |
| [ADR-0002](0002-backend-stack.md)                         | Python + FastAPI for the backend                                                                 | Accepted |
| [ADR-0003](0003-frontend-stack.md)                        | TypeScript + React (Vite) SPA, responsive                                                        | Accepted |
| [ADR-0004](0004-primary-database.md)                      | PostgreSQL as the primary relational database                                                    | Accepted |
| [ADR-0005](0005-plugin-module-mechanism.md)               | Backend plugins via Python entry points; frontend modules via dynamic registration + lazy chunks | Accepted |
| [ADR-0006](0006-authz-consent-model.md)                   | Centralized deny-by-default RBAC plus per-source consent grants                                  | Accepted |
| [ADR-0007](0007-fhir-adoption-strategy.md)                | FHIR-aligned internal data model (FHIR R4), no full FHIR server in MVP                           | Accepted |
| [ADR-0008](0008-dicom-storage-and-viewing.md)             | DICOM stored as objects; viewing via Cornerstone3D in the browser                                | Accepted |
| [ADR-0009](0009-file-object-storage.md)                   | S3-compatible object storage (MinIO) with server-side encryption                                 | Accepted |
| [ADR-0010](0010-deployment-model.md)                      | Containerized single-tenant deployment via Docker Compose (MVP)                                  | Accepted |
| [ADR-0011](0011-security-compliance-approach.md)          | Defense-in-depth: TLS, encryption at rest, OWASP controls, append-only audit log                 | Accepted |
| [ADR-0012](0012-authentication-session-mechanism.md)      | Server-side opaque session tokens in hardened cookies                                            | Accepted |
| [ADR-0013](0013-account-deletion-anonymized-retention.md) | Account deletion via 5-year anonymized retention with a user-held retrieval code                 | Accepted |
| [ADR-0014](0014-mui-css-variables-theming.md)             | Design-token theming via MUI CSS variables + native light/dark colorSchemes                      | Accepted |
| [ADR-0015](0015-object-store-component-after-minio.md)    | Replace MinIO with SeaweedFS; boto3 bucket initialiser; credential preflight; isolated network (amends ADR-0009) | Accepted |
| [ADR-0016](0016-failure-audit-events-on-own-transaction.md) | Failure audit events are committed on their own transaction (refines ADR-0011; replaces TASK-173's `durable` flag) | Accepted |
| [ADR-0017](0017-database-roles-and-append-only-audit-log.md) | Separate migration and runtime database roles; audit log append-only by privilege (refines ADR-0011, amends ADR-0010) | Accepted |
| [ADR-0018](0018-field-encryption-key-identifier-and-key-separation.md) | Field-encryption envelope with a key identifier, rehearsed rotation, separate object-store SSE key (refines ADR-0011, ADR-0015 D2) | Accepted |
| [ADR-0019](0019-originating-client-address-trusted-proxy-rule.md) | Originating client address from one trusted-proxy rule in the application | Accepted |
| [ADR-0020](0020-tool-and-test-image-pins-in-the-pin-check.md) | Build and CI tool pins and test-container images enforced by the existing pin check, against the shipped references (extends CR-001's check) | Accepted |

ADR-0010 and ADR-0019 carry dated notes (2026-11-08, TASK-201) recording what CR-004 changed in the text they describe; their decisions are unchanged.

ADR-0020 carries dated amendment notes (2026-11-12, TASK-212 QA): the test definition is `backend/postgres_image.py`, and the pin check reads its one-line or parenthesised assignment. The human acknowledged the amendment on 2026-11-12. A further dated note (2026-11-12, TASK-213 QA round 2) adds the `PostgresContainer` call rule and limits the guarantee to `PostgresContainer` call sites (the `DockerContainer` Redis call is not checked); the human acknowledged it on 2026-11-13.

## Trade-off summary

The dominant forces are: regulatory rigor (IEC 62304 / MDR / FDA / GDPR), a small prototype-stage team, a central plugin mechanism, and safety-critical DICOM rendering. These bias the architecture toward **simplicity, auditability, and strong access control over horizontal scalability**. A modular monolith (ADR-0001) is chosen over microservices precisely because it keeps the regulated surface small and the audit trail coherent, while still delivering the extensibility the product needs through an in-process module mechanism (ADR-0005).
