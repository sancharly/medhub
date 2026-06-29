# TASK-069 — Security headers middleware & CSRF enforcement

- **Phase:** 4 — API layer
- **Software item / unit:** SI-API / U-API-Routers (cross-cutting middleware)
- **Implements:** SR-031 (web-vulnerability mitigations: CSP, `X-Content-Type-Options`,
  `X-Frame-Options`, `Referrer-Policy`, HSTS coordination; CSRF enforcement on state-changing
  requests; server-side access control as the sole authority)
- **Depends on:** TASK-025 (API auth/session deps — the auth pipeline the middleware composes with),
  TASK-026 (RFC 7807 error handlers — CSRF/denial rendering) — must be merged first
- **Branch:** `feature/security-middleware`
- **Status:** In Progress (audit 2026-06-29)

## Objective

Implement the single centralized security middleware that sets the security-relevant HTTP response
headers on **every** response (CSP, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
`Referrer-Policy: strict-origin-when-cross-origin`) and coordinates HSTS with the TLS reverse proxy,
plus app-level enforcement of CSRF on all state-changing requests (POST/PUT/PATCH/DELETE). This is
the §8.3 "one security middleware" the whole app — including plugin modules — inherits, giving
uniform coverage (SR-031 AC-4). Traces to SR-031.

## Interfaces to honor

No service interface; this unit registers a Starlette/FastAPI middleware and composes the CSRF
dependency from TASK-022:

```python
class SecurityHeadersMiddleware:  # sets CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy
    async def __call__(self, request, call_next): ...

def enforce_csrf_on_state_change(request: Request) -> None: ...  # wraps require_csrf (TASK-022)
```

Composes with the auth pipeline (TASK-025) and renders failures via the RFC 7807 handlers (TASK-026).
HSTS is set at the reverse proxy (Traefik/nginx, ADR-0010/0011); the middleware **coordinates** by
not contradicting it and by relying on the proxy for HTTP→HTTPS redirect (SR-022).

Must **not**: re-implement the CSRF token mechanism (that is TASK-022 — this task **enforces** it
app-wide on state-changing methods); set headers per-route (uniform coverage is the requirement,
SR-031 AC-4); be bypassable by plugin module routers (middleware applies to the whole app, §8.7);
weaken `SameSite`/cookie attributes (owned by TASK-022).

## Implementation detail

- Files to create / modify:
  - `backend/app/core/security_middleware.py` — `SecurityHeadersMiddleware` and the CSRF enforcement
    wiring.
  - Register the middleware in the app factory (`backend/app/main.py`) so it wraps **all** routes
    including mounted module routers (`/api/v1/modules/{key}`, SI-MODHOST).
- Headers on every response (SR-031 AC-2/4):
  - `Content-Security-Policy` — restrict `default-src 'self'`; allow only the sources the SPA needs
    (script/style/connect/img/worker per Vite/MUI/Cornerstone3D); no `unsafe-inline` scripts. The
    exact policy is a config key (`CSP_POLICY`, TASK-003) so it can be tightened without code change.
  - `X-Content-Type-Options: nosniff`.
  - `X-Frame-Options: DENY`.
  - `Referrer-Policy: strict-origin-when-cross-origin`.
- HSTS coordination (SR-022): HSTS is emitted by the reverse proxy; document the expected
  `Strict-Transport-Security` value and ensure the app does not strip/duplicate it. Local/dev over
  HTTP is governed by the same `SESSION_COOKIE_SECURE`/proxy config as TASK-022 (never silently
  disabled in production).
- CSRF enforcement (SR-031.3): every state-changing method must carry a valid `X-CSRF-Token` matching
  the `medhub_csrf` cookie (double-submit, TASK-022). Safe methods (GET/HEAD/OPTIONS) bypass. This is
  enforced centrally so a new endpoint or module router cannot forget it.
- Server-side access control (SR-031.5): assert (in a structural test) that no route relies on a
  client-side-only gate; the authorization guard (TASK-025) is the sole authority — this middleware
  does not make access decisions, it hardens transport/response.
- Error cases (RFC 7807, base `https://medhub.example/errors/`): CSRF absence/mismatch on a
  state-changing request → `403 /errors/forbidden` (no protected data).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/api/test_security_headers.py`):
  - Every response (success and error, on a sample route **and** a mounted module route) carries
    `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
    `Referrer-Policy: strict-origin-when-cross-origin` (SR-031 AC-2/4, uniform coverage).
  - The CSP value comes from config and contains no `unsafe-inline` script source.
- Unit (`backend/tests/api/test_csrf_enforcement.py`):
  - A POST/PUT/PATCH/DELETE without a valid `X-CSRF-Token` → 403 problem+json, on a core route and a
    module route (SR-031.3, uniform).
  - GET/HEAD/OPTIONS bypass CSRF (SR-031.3).
- Structural (`backend/tests/api/test_server_side_access.py`): introspect routes to assert every
  non-public route depends on the authorization guard (TASK-025); no route is access-gated only by
  the client (SR-031.5).
- Integration (`backend/tests/api/test_security_middleware_integration.py`): a full request through
  the app shows the headers and CSRF behavior end-to-end, including through a mounted module router.

## Acceptance criteria

- [ ] CSP is set on all application responses, restricting script sources (SR-031 AC-2).
- [ ] `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` on all responses (SR-031 AC-4).
- [ ] HSTS is coordinated with the reverse proxy and not contradicted by the app (SR-022).
- [ ] All state-changing requests require a valid CSRF token; safe methods do not (SR-031.3).
- [ ] Coverage is uniform — core routes and mounted module routers alike (SR-031 AC-4, §8.7).
- [ ] Access control is enforced server-side for every request; no client-only gate is relied upon (SR-031.5).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit + integration + structural tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (security headers/CSRF are runtime; contract updated if any scheme metadata changes)
- [ ] Audit events emitted for security-relevant actions (CSRF denials need not be audited; auth denials audited by TASK-027)
- [ ] Traceability matrix row updated (SR-031 → TASK-069 → tests)
- [ ] **Security review completed (security/CSRF middleware — SR-031.6)**

## Audit verdict (2026-06-29)

- **Verdict:** FAIL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-069a. Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
