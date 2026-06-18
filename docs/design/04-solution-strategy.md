# 04 - Solution Strategy

This section summarizes the fundamental decisions; each is detailed in an ADR ([adr/](adr/)).

## Fundamental decisions

| Concern                 | Strategy                                                                                                                                                       | ADR                                                      |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------|
| **Architecture style**  | Modular monolith with an in-process plugin/module mechanism — single auth choke point, single audit log, strong consistency, low operational/regulated surface | [ADR-0001](adr/0001-overall-architecture-style.md)       |
| **Backend**             | Python 3.12 + FastAPI + Pydantic + SQLAlchemy/Alembic; Celery+Redis for async email; rich DICOM/FHIR/crypto libraries; auto OpenAPI                            | [ADR-0002](adr/0002-backend-stack.md)                    |
| **Frontend**            | TypeScript + React (Vite) responsive SPA; lazy-loaded module chunks; typed client from OpenAPI                                                                 | [ADR-0003](adr/0003-frontend-stack.md)                   |
| **Primary DB**          | PostgreSQL 16 — ACID for consent/access consistency, declarative integrity, parameterized access                                                               | [ADR-0004](adr/0004-primary-database.md)                 |
| **Plugin mechanism**    | Backend modules via Python entry points + `ModuleManifest`; frontend modules via dynamic registry + lazy chunks; data only via platform services               | [ADR-0005](adr/0005-plugin-module-mechanism.md)          |
| **AuthZ & consent**     | Centralized deny-by-default RBAC + per-source `ConsentGrant` union (manual + per-appointment)                                                                  | [ADR-0006](adr/0006-authz-consent-model.md)              |
| **FHIR**                | FHIR R4-aligned internal model + documented mapping; no full FHIR server at MVP                                                                                | [ADR-0007](adr/0007-fhir-adoption-strategy.md)           |
| **DICOM**               | Objects in storage; client-side Cornerstone3D WebGL rendering; authorized byte stream                                                                          | [ADR-0008](adr/0008-dicom-storage-and-viewing.md)        |
| **File storage**        | S3-compatible (MinIO) with SSE; backend-mediated authorized access                                                                                             | [ADR-0009](adr/0009-file-object-storage.md)              |
| **Deployment**          | Containerized single-tenant Docker Compose behind a TLS-terminating reverse proxy                                                                              | [ADR-0010](adr/0010-deployment-model.md)                 |
| **Security/compliance** | Defense-in-depth: TLS+at-rest crypto, central AuthZ, hardened credentials/sessions, OWASP middleware, append-only audit, erasure, review gate                  | [ADR-0011](adr/0011-security-compliance-approach.md)     |
| **AuthN/session**       | Server-side opaque session tokens in hardened cookies, Redis-backed, enumerable & instantly revocable                                                          | [ADR-0012](adr/0012-authentication-session-mechanism.md) |

## How the top quality goals are achieved

- **Security & privacy (G1):** one deny-by-default `AuthorizationService` on every request (SR-005); per-source consent (SR-036); encryption everywhere (SR-022); hardened auth/session (SR-025/029/030); OWASP middleware (SR-031); append-only audit (SR-023). Modules cannot bypass this because they access PHI only through platform services (ADR-0005).
- **Safety / correctness (G2):** vetted Cornerstone3D rendering verified against reference images (SR-017); consent evaluated as an explicit, transactional per-source union so declining one appointment never strips other access (SR-036); clinical-entry author derived from session, not client (SR-012).
- **Compliance & traceability (G3):** Arc42 doc + ADRs + UML + traceability matrix, all version-controlled; security-review gate before merging auth/session code (SR-031.6, SR-028).
- **Extensibility (G4):** module contract + registry; new module = new package + registry entry, zero edits to existing modules (SR-016).
- **Usability & reach (G5):** responsive component library, consistent navigation, confirmation on destructive actions, clear errors (SR-020, SR-027); standards-based tech for cross-browser (SR-019).

## Top-level decomposition

The backend is decomposed into bounded **software items** (section 05): API layer, AuthN/session, Authorization/consent, Identity/account-lifecycle, Groups/module-enablement, Appointments/notifications, Clinical records, Attachments, Audit, Module host, Persistence, the DICOM module (BE+FE), Worker, plus the frontend items (Shell, Auth UI, Core views, Module registry, API client). Cross-cutting concepts (security, audit, FHIR, error handling, i18n/responsiveness) are in section 08.
