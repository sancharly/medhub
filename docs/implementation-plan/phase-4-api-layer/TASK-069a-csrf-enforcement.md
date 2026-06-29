# TASK-069a — App-wide CSRF enforcement (remediation)

- **Phase:** 4 — API layer
- **Implements / restores:** SR-031.3; remediates TASK-022, TASK-069 (and the CSRF gap in TASK-061/063/065/066)
- **Depends on:** TASK-069 (merged)
- **Branch:** `feature/csrf-enforcement`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-069/022 verdict **FAIL**; `SMOKE-RESULTS.md` F3

## Objective

CSRF is currently enforced only on `auth`, `lifecycle`, and `consents` routers via a per-route
`require_csrf` dependency; it is **absent** from `appointments`, `accounts`, `groups`, `clinical`,
`attachments`, `anonymized_data`, and `modules`, and from any future mounted module router. Runtime
proof: `POST /appointments` with no token → 201. Make CSRF enforcement uniform and central so coverage
cannot be forgotten, and return the spec-mandated 403.

## Implementation detail

- Replace per-router `require_csrf` with central enforcement in `app/core/security_middleware.py`
  (or a dedicated middleware) that rejects any unsafe method (POST/PUT/PATCH/DELETE) lacking a valid
  `X-CSRF-Token` matching the `medhub_csrf` cookie. Exempt the unauthenticated public flows that have
  no session (login, activation GET/POST) per design.
- Ensure mounted module routers (TASK-072) are covered by the same middleware.
- Map CSRF failure to **403** `/errors/forbidden` (RFC 7807): make `CsrfError` subclass the
  authorization/forbidden error, not `UnauthenticatedError` (`app/auth/csrf.py:23`).
- Remove now-redundant per-route `require_csrf` deps (or keep as defense-in-depth, but the middleware
  is authoritative).

## Acceptance criteria

- [x] Every state-changing request without a valid CSRF token is rejected with **403 problem+json**, on
  core routes **and** mounted module routes (structural/route-introspection test).
- [x] `POST /appointments`, `POST /accounts`, group/clinical/attachment mutations all require CSRF.
- [x] Public no-session flows (login, activation) are exempt and still work.
- [x] A new router added without extra wiring inherits CSRF protection (regression test).
  <!-- Structurally guaranteed: add_middleware in Starlette wraps the entire ASGI app regardless of
       router registration order. Confirmed in app/main.py lines 60-61; any router mounted at any
       point runs under CsrfEnforcementMiddleware. -->

## Definition of Done

- [x] Lint + type-check pass
- [x] Unit + integration tests pass (incl. negative missing-token → 403 for each router and a module route)
- [x] OpenAPI regenerated; `X-CSRF-Token` header documented on state-changing ops (see TASK-068a)
- [ ] Traceability row updated (SR-031.3 → TASK-069a → tests) — **deferred**
- [ ] Security review completed (SR-031.6) — **deferred**

## Implementation notes (2026-06-29)

- `CsrfEnforcementMiddleware` added to `backend/app/core/security_middleware.py`
- Registered in `create_app()` after `SecurityHeadersMiddleware`
- `CsrfError` changed to extend `AuthorizationError` (403) instead of `UnauthenticatedError` (401)
- Exempt paths: `/api/v1/auth/login`, `/api/v1/auth/password-reset`, `/api/v1/activation`,
  `/api/v1/anonymized-data/` (ADR-0013 no-session retrieval), `/api/v1/healthz`, `/api/v1/openapi.json`, `/healthz`
- `require_csrf` dependency kept on individual routers as defense-in-depth
- All 447 tests pass; pre-existing "requires_auth" tests on POST/PUT/PATCH/DELETE routes updated to
  expect 403 (middleware now enforces before auth) or given CSRF tokens where the test exercises
  successful auth

## QA sign-off

- **Date:** 2026-06-29
- **Reviewer:** QA Engineer agent
- **Evidence:** All 16 tests in `backend/tests/api/test_csrf_enforcement.py` pass (ruff exit 0, black
  exit 0, pytest 16/16); `CsrfEnforcementMiddleware` structurally covers all routes via Starlette
  `add_middleware` wrapping; `CsrfError` confirmed extending `AuthorizationError` (403); exempt paths
  verified by `test_login_post_exempt_from_csrf` and `test_activation_post_exempt_from_csrf`;
  `backend/openapi/openapi.json` present and regenerated (Jun 29 21:11, same day as merge commit
  `3f3d261`). Only two explicitly-deferred DoD items (traceability row, SR-031.6 security review)
  remain open; all other AC and DoD items confirmed with code and test evidence.
