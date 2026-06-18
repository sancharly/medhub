# 03 - Context and Scope

## Business Context

MedHub is the single point of access for four user types to centralized PHI and clinical activity. External partners are the user's web browser, an email service (for activation and appointment notifications), and object storage (for clinical file binaries).

See diagram: [`../specifications/diagram-context.puml`](../specifications/diagram-context.puml)

### Business Interfaces

| Entity                       | Direction | Description                                                                                    |
|------------------------------|-----------|------------------------------------------------------------------------------------------------|
| **Doctor**                   | Inbound   | Records clinical entries, views own patients' data, uses DICOM viewer (UN-004, UN-008, UN-011) |
| **Patient**                  | Inbound   | Views own data, grants/revokes consent, confirms/declines appointments (UN-005, UN-013)        |
| **Administrative personnel** | Inbound   | Schedules appointments, views limited non-clinical data (UN-006, UN-007)                       |
| **System administrator**     | Inbound   | Manages accounts, groups, module enablement, account lifecycle (UN-009, UN-012)                |
| **Email service (SMTP)**     | Outbound  | Activation emails (SR-033) and appointment notifications (SR-035)                              |
| **Object storage**           | Outbound  | Stores/retrieves encrypted DICOM and report files (SR-013, SR-022)                             |

## Technical Context

The browser runs the React SPA (and the Cornerstone3D DICOM viewer in WebGL). It communicates with the FastAPI backend exclusively over HTTPS/REST-JSON with an opaque session cookie. The backend persists structured data in PostgreSQL, stores binaries in S3-compatible object storage, keeps sessions and task queues in Redis, and dispatches emails through a Celery worker to an SMTP server.

See diagrams: [`../specifications/diagram-context.puml`](../specifications/diagram-context.puml), [`../specifications/diagram-building-blocks.puml`](../specifications/diagram-building-blocks.puml), [`../specifications/diagram-deployment.puml`](../specifications/diagram-deployment.puml)

### Technical Interfaces

| Component                              | Data/Protocol/Interface                   | Direction     | Description                                                      |
|----------------------------------------|-------------------------------------------|---------------|------------------------------------------------------------------|
| **Browser ↔ Reverse proxy**            | HTTPS/TLS 1.2+, REST/JSON, session cookie | Inbound       | All client traffic; HTTP→HTTPS redirect, HSTS (SR-001, SR-022)   |
| **SPA ↔ Backend API**                  | `/api/v1` JSON, RFC 7807 errors           | Bidirectional | Typed client generated from OpenAPI (api-design.md)              |
| **DICOM viewer ↔ Attachment endpoint** | HTTPS, DICOM Part-10 bytes/frames         | Inbound       | Authorized byte stream; rendering client-side (SR-017, ADR-0008) |
| **Backend ↔ PostgreSQL**               | SQL over local/TLS                        | Outbound      | Domain + audit data (ADR-0004)                                   |
| **Backend ↔ Redis**                    | RESP                                      | Outbound      | Sessions (SR-030) + Celery broker                                |
| **Backend ↔ Object storage**           | S3 API (HTTPS), SSE                       | Outbound      | Encrypted attachment objects (ADR-0009)                          |
| **Worker ↔ SMTP**                      | SMTP(S)                                   | Outbound      | Activation & appointment emails (SR-033, SR-035)                 |

## Scope

**In scope (MVP):** authentication/session/lockout; account lifecycle; RBAC + consent; appointments + confirmation; clinical entries + attachments; groups + per-group module enablement; the plugin mechanism; the DICOM viewer module; FHIR-aligned model; encryption, audit, erasure; responsive cross-browser SPA.

**Out of scope (MVP, see ADRs/risks):** full FHIR REST server and external interoperability (ADR-0007); full PACS/DICOMweb (ADR-0008); multi-tenancy and HA orchestration (ADR-0010); untrusted/hot-loaded plugins (ADR-0005); external IdP (ADR-0011/0012); formal IEC 62366 usability engineering and penetration testing (NFR-009 notes).
