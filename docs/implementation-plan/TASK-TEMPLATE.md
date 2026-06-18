# TASK-NNN — <title>

- **Phase:** <n> — <name>
- **Software item / unit:** SI-XXX / U-XXX[, U-YYY]
- **Implements:** SR-### …, NFR-### …; ADR-#### …
- **Depends on:** TASK-### … (must be merged first)
- **Branch:** `feature/<slug>` (or `enabler-story/<slug>`)
- **Status:** Not started

## Objective

One paragraph: what this unit does and why, traced to its requirement(s).

## Interfaces to honor

Exact in-process / HTTP contracts this unit provides or consumes (from
[12-interfaces.md](../../design/12-interfaces.md)), with Python / TS signatures.
State explicitly what it must **not** do (e.g. modules touch PHI only via `PlatformServices`).

## Implementation detail

- Files to create / modify (explicit paths in the repo layout below).
- Key classes / functions / endpoints; libraries to use (exact names from the stack list).
- Data-model / migration changes, config keys, error cases (RFC 7807 `type` URIs).
- Edge cases and the relevant acceptance-criteria rules quoted from the SR(s).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit tests: cases to cover (happy path, deny-by-default, validation, edge).
- Integration tests where the unit crosses an interface.
- Each test references the SR acceptance criterion it verifies.

## Acceptance criteria

Checklist distilled from the SR(s) — objectively verifiable.

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy` or `eslint`/`tsc`)
- [ ] Unit (and required integration) tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (API tasks only)
- [ ] Audit events emitted for security-relevant actions (SR-023)
- [ ] Traceability matrix row updated (SR/NFR → TASK → test)
- [ ] Security review completed (auth / session / authz tasks only — SR-031.6)

---

## Repo layout (reference for all tasks)

```
backend/app/{main.py, core/(config,security,logging), db/(models,repositories,alembic/),
  auth/, authz/, identity/, groups/, clinical/, attachments/, appointments/, audit/,
  modules/(host), api/(routers,deps,errors,schemas), workers/(celery)}
backend/modules/dicom_viewer/        # installable module package (entry point: medhub.modules)
backend/tests/
frontend/src/{app/(shell,routing), api/(generated client), auth/, core/,
  modules/(registry), modules/dicom-viewer/}
frontend/tests/
infra/{docker-compose.yml, reverse-proxy/, .env.example}
```

## Conventions inherited by every task (do not repeat per task)

- **TDD**: failing tests first, then implement, then verify (CLAUDE.md §4). Surgical changes only (§3).
- **Backend**: every protected endpoint passes the `AuthorizationService` FastAPI dependency —
  **deny-by-default** (SR-005). Server-side Pydantic validation is authoritative (SR-031.5).
  Errors are RFC 7807 `application/problem+json` ([api-design.md](../../specifications/api-design.md)).
  Security-relevant actions call `AuditService` (SR-023). ORM-only parameterized queries (SR-031).
- **Secrets / config**: 12-factor, env-injected, never committed (NFR-007).
- **Frontend**: TypeScript only; typed client generated from OpenAPI; cookie + CSRF auth;
  MUI for accessible/responsive UI; module code lazy-loaded.
- **Stack (exact):** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, Celery, Redis,
  pydicom, fhir.resources, argon2-cffi, PostgreSQL 16, MinIO (S3 / SSE-AES256); TypeScript,
  React 18, Vite, React Router, TanStack Query, MUI, Cornerstone3D
  (`@cornerstonejs/core|tools|dicom-image-loader`); Docker Compose, Traefik/nginx reverse proxy
  (TLS / HSTS / security headers).
- **Git Flow** (per [software-development-plan.md](../../software-development-plan.md)): one branch/PR per task.
