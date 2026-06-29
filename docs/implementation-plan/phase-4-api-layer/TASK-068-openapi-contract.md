# TASK-068 — OpenAPI 3.1 contract finalization & typed-client generation

- **Phase:** 4 — API layer
- **Software item / unit:** SI-API / U-API-Routers, U-API-DTO (contract consolidation)
- **Implements:** NFR-006 (IEC 62304 interface definition — the OpenAPI document is the controlled,
  version-controlled interface artifact, linted in CI); SR-031 (security scheme + problem+json
  surfaced uniformly in the contract)
- **Depends on:** TASK-060, TASK-061, TASK-062, TASK-063, TASK-064, TASK-065, TASK-066, TASK-067
  (all routers must be merged so the document is complete) — must be merged first
- **Branch:** `enabler-story/openapi-contract`
- **Status:** In Progress (audit 2026-06-29)

## Objective

Finalize the FastAPI-generated **OpenAPI 3.1** document served at `/api/v1/openapi.json` as the
authoritative, machine-readable external contract (api-design.md), make it pass
`npx @redocly/cli lint` in CI, and produce the **typed-client generation artifact** the frontend
API client (TASK-080) is generated from. This is the consolidation step that turns the per-resource
routers into one approved interface specification (NFR-006). No new endpoints are added here; this
task hardens metadata, response components, the security scheme, and the generation pipeline.

## Interfaces to honor

The contract per [api-design.md](../../specifications/api-design.md) and the internal interface
definition role from [12-interfaces.md](../../design/12-interfaces.md) §12.3:

- Base path `/api/v1`; URI versioning; JSON, `camelCase` DTO fields.
- Auth scheme documented as the opaque session **cookie** (`medhub_session`, ADR-0012) — **not** a
  bearer token; CSRF via `X-CSRF-Token` header on state-changing operations (SR-031.3).
- Every error response references a **shared RFC 7807 `problem+json`** component with the documented
  `type` URIs (the error catalog in api-design.md).
- Collections documented as paginated and access-scoped.

Must **not**: introduce new endpoints or DTOs (that is each resource task); hand-edit the generated
JSON (it is generated from the FastAPI app — the source of truth is the Python route/DTO definitions);
document a bearer-token scheme (the SPA uses cookies, ADR-0012); omit the problem+json responses from
any operation (uniform error contract, §8.6).

## Implementation detail

- Files to create / modify:
  - `backend/app/main.py` — set the FastAPI app `title`, `version`, `description`, `servers`
    (`/api/v1`), `openapi_url="/api/v1/openapi.json"`, force **OpenAPI 3.1** output, and register the
    cookie security scheme + the `X-CSRF-Token` header parameter on state-changing operations.
  - `backend/app/api/openapi.py` — `customize_openapi(app)` that: attaches the shared
    `Problem` (RFC 7807) response component and references it from the documented status codes on
    every operation; tags operations by resource (auth, accounts, activation, lifecycle,
    anonymized-data, groups, modules, appointments, consents, clinical, attachments, me); and adds
    the `type`-URI enum from the error catalog.
  - `backend/scripts/export_openapi.py` — dumps `/api/v1/openapi.json` to a committed artifact at
    `backend/openapi/openapi.json` (the version-controlled interface output, NFR-006.2).
  - `frontend/scripts/generate-client.*` — generation step that produces the typed client into
    `frontend/src/api/generated/` from `backend/openapi/openapi.json` (consumed by TASK-080).
  - CI wiring (extends TASK-005): run `npx @redocly/cli lint backend/openapi/openapi.json` and fail
    the build on lint errors (api-design.md Validation, NFR-006).
- The exported `backend/openapi/openapi.json` is committed and diffed in review so contract changes
  are visible (NFR-006.2/3 traceability of the interface artifact).
- The typed-client artifact is regenerated whenever the contract changes; TASK-080 imports it.

## Tests (write first — TDD, CLAUDE.md §4)

- Contract tests (`backend/tests/api/test_openapi_contract.py`):
  - `GET /api/v1/openapi.json` returns an OpenAPI **3.1** document (assert `openapi` field starts
    `3.1`).
  - Every operation that is not explicitly public declares the cookie security requirement; the
    public routes (`/auth/login`, `/activation/{token}` GET/POST, `/anonymized-data/retrieve`, health,
    openapi) are exactly the documented unauthenticated set (SR-005, deny-by-default surfaced in the
    contract).
  - Every state-changing operation (POST/PUT/PATCH/DELETE) documents the `X-CSRF-Token` requirement
    (SR-031.3).
  - Every operation documents the shared `Problem` response for its error statuses (§8.6 uniform
    errors).
  - `camelCase` DTO field naming is consistent across components (api-design.md).
- CI lint (`backend/tests/api/test_openapi_lint.py` or a CI step): `npx @redocly/cli lint` exits 0 on
  the exported document (NFR-006).
- Generation smoke test (`frontend/tests/api/generated-client.smoke.test.ts`): the generated client
  type-checks (`tsc --noEmit`) and exposes a method per documented endpoint (consumed by TASK-080).

## Acceptance criteria

- [ ] `/api/v1/openapi.json` is a valid OpenAPI **3.1** document covering all phase-4 endpoints.
- [ ] The auth scheme is the opaque session **cookie** (ADR-0012), not a bearer token; CSRF header documented on state-changing ops (SR-031.3).
- [ ] All errors reference the shared RFC 7807 `problem+json` component with the catalog `type` URIs (§8.6).
- [ ] The exported `backend/openapi/openapi.json` passes `npx @redocly/cli lint` in CI (NFR-006).
- [ ] The committed contract artifact is version-controlled and diffable in review (NFR-006.2/3).
- [ ] The typed-client generation artifact builds and type-checks (input to TASK-080).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`; `tsc` on the generated client)
- [ ] Contract + generation tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted — this **is** the regeneration/lint task (NFR-006)
- [ ] Audit events emitted for security-relevant actions (N/A — contract artifact, no runtime behavior)
- [ ] Traceability matrix row updated (NFR-006, SR-031 → TASK-068 → contract + lint tests)
- [ ] Security review N/A (no auth/session logic; but the documented public-route set is reviewed for deny-by-default correctness)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-068a. Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
