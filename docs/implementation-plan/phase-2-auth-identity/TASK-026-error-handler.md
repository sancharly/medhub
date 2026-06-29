# TASK-026 — RFC 7807 error handlers

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-API / U-API-ErrorHandler
- **Implements:** SR-027.3 (clear, actionable error messaging); api-design.md error catalog
- **Depends on:** TASK-002 (backend FastAPI app skeleton)
- **Branch:** `feature/rfc7807-error-handlers`
- **Status:** In Progress (audit 2026-06-29)

## Objective

Register the application-wide exception handlers that render every error as RFC 7807
`application/problem+json` with stable `type` URIs and field-level `errors[]`, so the SPA can
surface clear, actionable messages (SR-027.3, §8.6) and so all later auth/authz/identity tasks map
their domain exceptions to a uniform, non-disclosing contract. This is the single place the error
catalog from api-design.md is implemented.

## Interfaces to honor

No service interface; this unit registers FastAPI exception handlers and defines the domain
exception base classes other units raise:

```python
class ProblemError(Exception):              # base: type, status, title, detail, errors[]
    ...
class ValidationProblem(ProblemError): ...   # 400
class UnauthenticatedError(ProblemError): ...# 401
class AuthorizationError(ProblemError): ...  # 403
class NotFoundError(ProblemError): ...       # 404
class ConflictError(ProblemError): ...       # 409
class RateLimitedError(ProblemError): ...    # 429
```

The response body shape (problem+json): `{ "type", "title", "status", "detail", "instance",
"errors": [ { "field", "rule", "message" } ] }`.

Must **not**: leak protected data, internal stack traces, SQL, or which credential field failed in
401/403 bodies (SR-002.2, SR-005 AC-4); use status-code-only error responses (every error is
problem+json).

## Implementation detail

- Files to create:
  - `backend/app/api/errors.py` — exception classes, the `type` URI registry, handler functions,
    and `register_error_handlers(app)`.
  - Wire `register_error_handlers` into the app factory (`backend/app/main.py`, from TASK-002).
- Stable `type` URIs (api-design.md error catalog; base `https://medhub.example/errors/`):
  - 400 `/errors/validation-error` — malformed/missing fields, password-policy violations
    (SR-010/012/025/032).
  - 401 `/errors/unauthenticated` — no/invalid session; **generic**, no field disclosure.
  - 403 `/errors/forbidden` — authorization denied; no protected data (SR-005/006/009/015).
  - 404 `/errors/not-found` — absent or not visible to caller.
  - 409 `/errors/conflict` — duplicate email (SR-032.3), invalid state transition.
  - 423 `/errors/account-locked` — defined but **surfaced as 401 during login** (SR-029.6).
  - 429 `/errors/rate-limited`.
- Override FastAPI's default `RequestValidationError` handler so Pydantic v2 validation errors are
  re-rendered as `/errors/validation-error` with one `errors[]` entry per field (server-side
  validation is authoritative, SR-031.5, §8.6) — preserving the field path and a human message.
- `Content-Type: application/problem+json` on all error responses; include `instance` (request path).
- Map the domain exceptions raised across phase 2: `PasswordPolicyError` (TASK-020) → 400 with one
  `errors[]` entry per violated rule; `CsrfError` (TASK-022) → 403; `UnauthenticatedError`/
  `AuthorizationError` (TASK-025/027) → 401/403; duplicate-email (TASK-030) → 409.
- Error cases: an unhandled exception falls through to a generic 500 problem+json with **no**
  internal detail (defensive; logged server-side only).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/api/test_error_handlers.py`):
  - Each `ProblemError` subclass renders the correct status, `type` URI, and
    `Content-Type: application/problem+json` (api-design.md catalog).
  - Pydantic validation failure → 400 `/errors/validation-error` with field-level `errors[]`
    (SR-027.3).
  - 401 and 403 bodies contain no field-level disclosure of credentials or protected data
    (SR-002.2, SR-005 AC-4).
  - Unhandled exception → 500 problem+json with no stack trace / internal detail.
- Integration (`backend/tests/api/test_problem_json_contract.py`): hit a route that raises each
  error type and assert the on-the-wire body matches the documented schema.

## Acceptance criteria

Distilled from SR-027.3 and the api-design.md error catalog:

- [ ] All errors are `application/problem+json` with stable `type` URIs (catalog).
- [ ] Validation errors carry field-level `errors[]` identifying each problem (SR-027.3, §8.6).
- [ ] 401/403 disclose no protected data or credential-field detail (SR-002.2, SR-005 AC-4).
- [ ] Duplicate-email maps to 409 conflict; locked-account maps to 401 during login (SR-032.3, SR-029.6).
- [ ] Pydantic v2 validation is rendered through the same contract (server-side authoritative).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit (and required integration) tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (problem+json response components registered for reuse)
- [ ] Audit events emitted for security-relevant actions (N/A — handlers are presentation; callers audit)
- [ ] Traceability matrix row updated (SR-027.3, api-design.md → TASK-026 → tests)
- [ ] Security review completed (N/A — not auth/session/authz logic; but verify no disclosure in 401/403)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-026a. Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
