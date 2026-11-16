# 04 - Solution Strategy

This section summarizes the fundamental decisions; each is detailed in an ADR ([adr/](adr/)).

## Fundamental decisions

| Concern                 | Strategy                                                                                                                                                       | ADR                                                      |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------|
| **Architecture style**  | Modular monolith with an in-process plugin/module mechanism — single auth choke point, single audit log, strong consistency, low operational/regulated surface | [ADR-0001](adr/0001-overall-architecture-style.md)       |
| **Backend**             | Python 3.12 + FastAPI + Pydantic + SQLAlchemy/Alembic; Celery+Redis for async email; rich DICOM/FHIR/crypto libraries; auto OpenAPI                            | [ADR-0002](adr/0002-backend-stack.md)                    |
| **Frontend**            | TypeScript + React (Vite) responsive SPA; lazy-loaded module chunks; hand-written typed `ApiClient` with types generated from OpenAPI                                 | [ADR-0003](adr/0003-frontend-stack.md)                   |
| **Primary DB**          | PostgreSQL 16 — ACID for consent/access consistency, declarative integrity, parameterized access                                                               | [ADR-0004](adr/0004-primary-database.md)                 |
| **Plugin mechanism**    | Backend modules via Python entry points + `ModuleManifest`; frontend modules via dynamic registry + lazy chunks; data only via platform services               | [ADR-0005](adr/0005-plugin-module-mechanism.md)          |
| **AuthZ & consent**     | Centralized deny-by-default RBAC + per-source `ConsentGrant` union (manual + per-appointment)                                                                  | [ADR-0006](adr/0006-authz-consent-model.md)              |
| **FHIR**                | FHIR R4-aligned internal model + documented mapping; no full FHIR server at MVP                                                                                | [ADR-0007](adr/0007-fhir-adoption-strategy.md)           |
| **DICOM**               | Objects in storage; client-side Cornerstone3D WebGL rendering; authorized byte stream                                                                          | [ADR-0008](adr/0008-dicom-storage-and-viewing.md)        |
| **File storage**        | S3-compatible (SeaweedFS, ADR-0015) with SSE; backend-mediated authorized access                                                                                             | [ADR-0009](adr/0009-file-object-storage.md), [ADR-0015](adr/0015-object-store-component-after-minio.md)              |
| **Deployment**          | Containerized single-tenant Docker Compose behind a TLS-terminating reverse proxy                                                                              | [ADR-0010](adr/0010-deployment-model.md)                 |
| **Security/compliance** | Defense-in-depth: TLS+at-rest crypto, central AuthZ, hardened credentials/sessions, OWASP middleware, append-only audit, erasure, review gate                  | [ADR-0011](adr/0011-security-compliance-approach.md)     |
| **AuthN/session**       | Server-side opaque session tokens in hardened cookies, Redis-backed, enumerable & instantly revocable                                                          | [ADR-0012](adr/0012-authentication-session-mechanism.md) |
| **Concurrency**         | Every dependency and handler that calls a blocking client is a plain `def` and runs in AnyIO's thread pool; the thread limit and the database pool are sized together | [ADR-0022](adr/0022-blocking-io-off-the-event-loop-with-matched-pools.md) |
| **Transaction boundary** | The request transaction commits (or rolls back) before the response is sent, through one `DbSession` alias with `scope="function"` | [ADR-0023](adr/0023-request-transaction-commits-before-the-response.md) |
| **Attachment IO**       | Upload and download in 64 KiB chunks; the download is two reads, the second bound to the first by the ETag (`If-Match`) | [ADR-0021](adr/0021-bounded-attachment-io-and-bound-two-pass-download.md) |

## How the top quality goals are achieved

- **Security & privacy (G1):** one deny-by-default `AuthorizationService` on every request (SR-005); per-source consent (SR-036); encryption everywhere (SR-022); hardened auth/session (SR-025/029/030); OWASP middleware (SR-031); append-only audit (SR-023). Modules cannot bypass this because they access PHI only through platform services (ADR-0005).
- **Safety / correctness (G2):** vetted Cornerstone3D rendering verified against reference images (SR-017); consent evaluated as an explicit, transactional per-source union so declining one appointment never strips other access (SR-036); clinical-entry author derived from session, not client (SR-012).
- **Compliance & traceability (G3):** Arc42 doc + ADRs + UML + design records with frontmatter links, all version-controlled; security-review gate before merging auth/session code (SR-031.6, SR-028).
- **Extensibility (G4):** module contract + registry; new module = new package + registry entry, zero edits to existing modules (SR-016).
- **Usability & reach (G5):** responsive component library, consistent navigation, confirmation on destructive actions, clear errors (SR-020, SR-027); standards-based tech for cross-browser (SR-019).

## Concurrency model and request consistency (CR-006)

- **Blocking IO off the event loop.** The stack is synchronous (SQLAlchemy with psycopg2, redis-py, boto3), so a blocking call in an `async def` stalls every request of the worker (PRB-009, PRB-072). `get_session`, `get_current_user`, the module gate, `logout`, `extend_session` and the other blocking dependencies and handlers are plain `def` and run in AnyIO's worker threads. The upload handler stays `async` because it awaits `UploadFile`; it calls the blocking service through `run_in_threadpool`. A static test fails if an `async def` in `app/api` calls a known blocking client (TASK-136).
- **Pools sized together.** `API_THREADPOOL_SIZE` sets AnyIO's default limiter in the lifespan and the Redis pool size; `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` and `DB_POOL_TIMEOUT` set the SQLAlchemy engine pool (`backend/app/core/config.py`). Start-up is refused when threads exceed `DB_POOL_SIZE + DB_MAX_OVERFLOW`. The invariant bounds threads, not requests: a connection belongs to the request, so one worker serves about threads + connections concurrent requests and answers 500 beyond that (PRB-081, open). Values are in [07 deployment view](07-deployment-view.md).
- **Acknowledged means committed.** `get_db` keeps its body (commit on return, rollback on exception, close), but every route reaches it through the `DbSession` alias (`backend/app/db/repositories/session.py`), declared with `scope="function"`, so FastAPI tears it down before the response is sent. A failing commit is a 5xx, never the prepared success status; a streamed download commits its audit rows before the first byte (ADR-0023, refining [ADR-0016](adr/0016-failure-audit-events-on-own-transaction.md)).
- **Bounded attachment IO.** The attachment maximum is 150 MiB (`attachment_max_bytes`); memory per upload and per download is bounded by the chunk size and Starlette's 1 MiB spool threshold (ADR-0021).

## Top-level decomposition

The backend is decomposed into bounded **software items** (section 05): API layer, AuthN/session, Authorization/consent, Identity/account-lifecycle, Groups/module-enablement, Appointments/notifications, Clinical records, Attachments, Audit, Module host, Persistence, the DICOM module (BE+FE), Worker, plus the frontend items (Shell, Auth UI, Core views, Module registry, API client). Cross-cutting concepts (security, audit, FHIR, error handling, i18n/responsiveness) are in section 08.
