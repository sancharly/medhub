# Architecture Decision Records (ADRs)

This folder records the significant architecture decisions for MedHub. One decision per file, following the template in the `architecture-designer` skill. ADRs are version-controlled design records that satisfy SR-028 (traceable, version-controlled development records) and NFR-005 / NFR-006 (MDR/FDA and IEC 62304 documentation).

| ADR                                                  | Decision                                                                                         | Status   |
|------------------------------------------------------|--------------------------------------------------------------------------------------------------|----------|
| [ADR-0001](0001-overall-architecture-style.md)       | Modular monolith with a runtime plugin/module mechanism                                          | Accepted |
| [ADR-0002](0002-backend-stack.md)                    | Python + FastAPI for the backend                                                                 | Accepted |
| [ADR-0003](0003-frontend-stack.md)                   | TypeScript + React (Vite) SPA, responsive                                                        | Accepted |
| [ADR-0004](0004-primary-database.md)                 | PostgreSQL as the primary relational database                                                    | Accepted |
| [ADR-0005](0005-plugin-module-mechanism.md)          | Backend plugins via Python entry points; frontend modules via dynamic registration + lazy chunks | Accepted |
| [ADR-0006](0006-authz-consent-model.md)              | Centralized deny-by-default RBAC plus per-source consent grants                                  | Accepted |
| [ADR-0007](0007-fhir-adoption-strategy.md)           | FHIR-aligned internal data model (FHIR R4), no full FHIR server in MVP                           | Accepted |
| [ADR-0008](0008-dicom-storage-and-viewing.md)        | DICOM stored as objects; viewing via Cornerstone3D in the browser                                | Accepted |
| [ADR-0009](0009-file-object-storage.md)              | S3-compatible object storage (MinIO) with server-side encryption                                 | Accepted |
| [ADR-0010](0010-deployment-model.md)                 | Containerized single-tenant deployment via Docker Compose (MVP)                                  | Accepted |
| [ADR-0011](0011-security-compliance-approach.md)     | Defense-in-depth: TLS, encryption at rest, OWASP controls, append-only audit log                 | Accepted |
| [ADR-0012](0012-authentication-session-mechanism.md) | Server-side opaque session tokens in hardened cookies                                            | Accepted |

## Trade-off summary

The dominant forces are: regulatory rigor (IEC 62304 / MDR / FDA / GDPR), a small prototype-stage team, a central plugin mechanism, and safety-critical DICOM rendering. These bias the architecture toward **simplicity, auditability, and strong access control over horizontal scalability**. A modular monolith (ADR-0001) is chosen over microservices precisely because it keeps the regulated surface small and the audit trail coherent, while still delivering the extensibility the product needs through an in-process module mechanism (ADR-0005).
