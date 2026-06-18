# ADR-0002: Python + FastAPI for the backend

## Status

Accepted

## Context

We need a backend framework for the modular monolith (ADR-0001) that:

- Serves a documented HTTP API over HTTPS (SR-001) consumed by an SPA.
- Has first-class libraries for the regulated domain: DICOM parsing (SR-013, SR-017), FHIR resources (SR-021), cryptography (SR-022), and security middleware (SR-031).
- Supports a clean in-process plugin mechanism (SR-016).
- Is productive for a small team and explicitly preferred by the stakeholder (Python over Java/JavaScript).
- Produces an auditable, testable codebase suitable for IEC 62304 (NFR-006).

## Decision

Use **Python 3.12** with **FastAPI** as the backend web framework, **Pydantic v2** for request/response validation and schema, **SQLAlchemy 2.x** + **Alembic** for persistence and migrations, and **uvicorn/gunicorn** as the ASGI server. Long-running/async work (sending activation and appointment emails, SR-033/SR-035; session-invalidation propagation, SR-034) runs on **Celery** with **Redis** as broker/result backend.

## Consequences

### Positive

- Strong domain library ecosystem: `pydicom` (DICOM parsing/validation, SR-013/SR-017), `fhir.resources` (typed FHIR R4 models, SR-021), `cryptography`/`argon2-cffi` (SR-022/SR-025), `authlib`/framework middleware (SR-031).
- FastAPI auto-generates an OpenAPI 3.1 contract from Pydantic models, directly producing the interface documentation IEC 62304 wants (NFR-006) and feeding the api-designer deliverable.
- Pydantic gives declarative, server-side input validation — the enforceable backbone of password policy (SR-025), required-field checks (SR-010, SR-012, SR-032), and injection resistance (SR-031).
- Dependency-injection system (`Depends`) is a natural insertion point for the centralized authorization check (SR-005) on every endpoint.
- Matches the stakeholder's stated Python preference; high team productivity at prototype scale.

### Negative

- Python is slower than the JVM/Go for CPU-bound work; heavy DICOM pixel processing must be done client-side (ADR-0008) or with native libs (`numpy`/`pydicom`) to meet SR-026 AC-3.
- GIL limits in-process CPU parallelism; mitigated by running multiple worker processes and offloading to Celery.
- Async correctness (mixing sync SQLAlchemy and async endpoints) requires discipline; mitigated by a coding standard (one style per layer).

### Neutral

- Requires a separate frontend toolchain (ADR-0003); backend is API-only.

## Alternatives Considered

**Java + Spring Boot.** Strong regulated-industry pedigree, excellent FHIR support (HAPI FHIR). Rejected as the default because the stakeholder prefers Python, the team is small, and the HAPI/Spring footprint is heavier than needed for an MVP. No DICOM/FHIR capability gap justifies overriding the preference here.

**Node.js + NestJS (TypeScript).** Would unify language with the frontend. Rejected: DICOM and FHIR server-side tooling is weaker than Python's `pydicom`/`fhir.resources`, and the stakeholder prefers Python; medical-imaging parsing is better served in Python.

**Django.** Viable (batteries-included, ORM, admin). Rejected in favor of FastAPI for its native OpenAPI generation, Pydantic validation, and lighter, API-first shape that fits an SPA + plugin backend better.

## References

- Requirements: SR-001, SR-005, SR-010, SR-012, SR-013, SR-016, SR-017, SR-021, SR-022, SR-025, SR-031, SR-032; NFR-006, NFR-008
- Stakeholder constraint: Python preferred over Java/JavaScript
