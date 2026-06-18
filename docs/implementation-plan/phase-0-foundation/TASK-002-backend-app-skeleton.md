# TASK-002 — Backend FastAPI app skeleton

- **Phase:** 0 — Foundation & toolchain
- **Software item / unit:** SI-API / — (app bootstrap; routers land later)
- **Implements:** SR-001
- **Depends on:** TASK-001 (must be merged first)
- **Branch:** `enabler-story/backend-app-skeleton`
- **Status:** Not started

## Objective

Stand up the FastAPI application factory that all backend items mount into: a single `create_app()` entry point exposing an unauthenticated liveness probe `/healthz`, a versioned `/api/v1` router mount point, and structured JSON logging. This realizes the "reachable web application" baseline of SR-001 at the server tier; TLS, redirects, and HTTPS delivery are completed by the reverse proxy in TASK-004.

## Interfaces to honor

- Provides the **app composition root** that later items extend; the external HTTP contract is the FastAPI-generated **OpenAPI 3.1** document at `/api/v1/openapi.json` ([api-design.md](../../specifications/api-design.md)). Base path is `/api/v1` (URI versioning).
- Must expose a single mount point so SI-API routers (TASK-040+) attach without editing the factory beyond a registration call.
- Must **not** implement any business endpoint, authentication, authorization, or DB access here. `/healthz` is deliberately unauthenticated and returns no PHI or environment detail. RFC 7807 error handlers and the `AuthorizationService` dependency are wired by later tasks — this task only leaves the seam.

## Implementation detail

- Files to create:
  - `backend/app/main.py` — `create_app() -> FastAPI`: instantiates the app, sets `title`, `version`, `openapi_url="/api/v1/openapi.json"`, includes the v1 router, registers logging on startup. Export a module-level `app = create_app()` for the ASGI server.
  - `backend/app/api/router.py` — `api_router = APIRouter(prefix="/api/v1")` (empty include surface; later tasks `api_router.include_router(...)`).
  - `backend/app/api/health.py` — `GET /healthz` → `{"status": "ok"}` (200), defined on the root app, **outside** `/api/v1` so liveness checks bypass versioned routing.
  - `backend/app/core/logging.py` — `configure_logging()`: structured JSON logs to stdout (12-factor; container-friendly for TASK-004) with a request-id field; no PHI, no credentials in log output.
- Libraries (exact stack): FastAPI, Pydantic v2. ASGI server (`gunicorn` + `uvicorn` worker) is containerized in TASK-004; this task targets `uvicorn` for local dev.
- Config keys: none here (read via `Settings` once TASK-003 lands; until then use literals/defaults). Do not read raw `os.environ` in app code — leave that to TASK-003.
- Error cases: none beyond FastAPI defaults; the RFC 7807 handler is a later task and must not be stubbed with a non-compliant format here.

## Tests (write first — TDD, CLAUDE.md §4)

- `backend/tests/test_health.py`:
  - `GET /healthz` → 200, body `{"status": "ok"}` (SR-001.1 reachable/loads; SR-001.3 reachable landing seam).
  - `/healthz` requires no authentication (no cookie/session present).
- `backend/tests/test_app_factory.py`:
  - `create_app()` returns a `FastAPI` instance and serves `/api/v1/openapi.json` with `openapi: 3.1.x`.
  - The `/api/v1` mount point exists (router prefix asserted) so later items can attach.
- `backend/tests/test_logging.py`: `configure_logging()` emits parseable JSON and never includes a known credential/PHI token placed in a log call.
- Use `httpx.ASGITransport` + `pytest` (no network); reference [fastapi-patterns] for app-factory/test-client structure.

## Acceptance criteria

Distilled from SR-001:

- [ ] The app is reachable and serves a 200 liveness response without installation (SR-001.1).
- [ ] A versioned `/api/v1` mount point and `/api/v1/openapi.json` exist (interface baseline for SR-001.3).
- [ ] Logging is structured JSON to stdout and contains no credentials or PHI.
- [ ] `/healthz` is unauthenticated and exposes no environment or PHI detail.
- [ ] No business endpoint, auth, authz, or DB access is present.

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted — `/api/v1/openapi.json` renders and passes `npx @redocly/cli lint`
- [ ] Audit events emitted for security-relevant actions (N/A — no security-relevant action yet)
- [ ] Traceability matrix row updated (SR-001 → TASK-002 → health/app-factory tests)
- [ ] Security review completed (N/A — no auth/session code)
