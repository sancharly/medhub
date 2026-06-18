# 02 - Architecture Constraints

## Technical Constraints

| Constraint                         | Description                                                              | Rationale                              |
|------------------------------------|--------------------------------------------------------------------------|----------------------------------------|
| **TC-01: Web delivery over HTTPS** | Browser-accessible web app, no client install, TLS-only                  | UN-001, SR-001, SR-022                 |
| **TC-02: Cross-browser**           | Current stable Safari, Firefox, Chrome, Edge                             | NFR-001, SR-019                        |
| **TC-03: Responsive**              | Usable on phone, tablet, desktop                                         | NFR-003, SR-020                        |
| **TC-04: FHIR R4 alignment**       | Core entities aligned to FHIR R4 with documented mapping                 | NFR-002, SR-021                        |
| **TC-05: DICOM support**           | Open/render CT/MRI/X-ray incl. volumetric, with standard viewer controls | UN-011, SR-017, SR-018                 |
| **TC-06: Plugin extensibility**    | Add modules without modifying existing modules; enable per group         | SR-015, SR-016                         |
| **TC-07: Encryption**              | TLS in transit; AES-256-class at rest for PHI & attachments              | SR-022                                 |
| **TC-08: Backend in Python**       | Stakeholder preference; backend uses Python (ADR-0002)                   | Stakeholder constraint                 |
| **TC-09: Frontend in JS/TS**       | SPA in TypeScript/React (ADR-0003)                                       | Necessitated by rich UI + DICOM viewer |

## Organizational Constraints

| Constraint                          | Description                                                                 | Impact                                                                                                  |
|-------------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **OC-01: IEC 62304**                | Lifecycle activities & controlled records per the software development plan | Architecture activity must output Arc42 doc, specs, UML, item/unit decomposition, interface definitions |
| **OC-02: MDR (EU) & FDA (US)**      | Medical-device regulation incl. cybersecurity case file                     | Documentation, traceability, risk analysis, verification rigor (NFR-005, SR-031)                        |
| **OC-03: GDPR**                     | Lawful consent, minimization, data-subject rights, audit                    | Consent model, erasure, audit log, encryption (NFR-004)                                                 |
| **OC-04: IEC 62443-3-3 SL 2**       | Credential, lockout, session controls cite this standard                    | SR-025, SR-029, SR-030 define exact behaviors                                                           |
| **OC-05: Folder & version control** | Design in `docs/design/`, specs in `docs/specifications/`, all under git    | Per dev-plan; SR-028                                                                                    |
| **OC-06: Traceability**             | Bidirectional UN/NFR → SR → architecture → test                             | SR-028, NFR-006; traceability matrix maintained                                                         |
| **OC-07: Documentation language**   | English; Markdown + PlantUML                                                | Consistency with existing repo artifacts                                                                |

## Conventions

| Convention                         | Description                                                                                            |
|------------------------------------|--------------------------------------------------------------------------------------------------------|
| **CV-01: Software item IDs**       | Items use `SI-<NAME>`; units enumerated under each item (section 05)                                   |
| **CV-02: API**                     | `/api/v1`, JSON camelCase, RFC 7807 errors, resource-oriented (api-design.md)                          |
| **CV-03: Diagrams**                | PlantUML in `docs/specifications/*.puml`; in-house components `#lightblue`, external/SOUP `#lightgray` |
| **CV-04: Server-side enforcement** | Access control is always enforced server-side; client never the sole gate (SR-031.5)                   |
| **CV-05: Deny-by-default**         | All authorization decisions deny unless explicitly permitted (SR-005)                                  |

## Dependencies

### Internal Dependencies

| Item                              | Purpose                                  | Type                                     |
|-----------------------------------|------------------------------------------|------------------------------------------|
| `SI-AUTHZ` (AuthorizationService) | Central deny-by-default access + consent | Direct (used by all data items)          |
| `SI-AUDIT` (AuditService)         | Append-only audit logging                | Direct (used by security-relevant items) |
| `SI-PERSIST` (Persistence)        | SQLAlchemy data access                   | Direct                                   |
| `SI-MODHOST` (Module Host)        | Plugin registration & platform services  | Direct (used by modules)                 |

### External Dependencies (SOUP)

| Library / Component        | Version        | Purpose                                      |
|----------------------------|----------------|----------------------------------------------|
| Python                     | 3.12           | Backend runtime (ADR-0002)                   |
| FastAPI / Pydantic v2      | latest stable  | API, validation, OpenAPI                     |
| SQLAlchemy / Alembic       | 2.x            | ORM, migrations                              |
| pydicom                    | latest stable  | Server-side DICOM parsing/validation         |
| fhir.resources             | R4             | FHIR-aligned DTO models (SR-021)             |
| argon2-cffi / cryptography | latest stable  | Password hashing, crypto (SR-022, SR-025)    |
| Celery + Redis             | latest stable  | Async email tasks; Redis also session store  |
| PostgreSQL                 | 16             | Primary DB (ADR-0004)                        |
| MinIO (S3-compatible)      | latest stable  | Object storage for attachments (ADR-0009)    |
| React / TypeScript / Vite  | React 18, TS 5 | SPA (ADR-0003)                               |
| Cornerstone3D              | latest stable  | In-browser DICOM viewer (ADR-0008)           |
| MUI (or equivalent)        | latest stable  | Responsive, accessible UI components         |
| Traefik / nginx            | latest stable  | TLS termination, security headers (ADR-0010) |

> All SOUP must be inventoried and risk-assessed per IEC 62304 (versions pinned at implementation time).
