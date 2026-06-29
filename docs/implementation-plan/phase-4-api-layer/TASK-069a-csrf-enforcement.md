# TASK-069a — App-wide CSRF enforcement (remediation)

- **Phase:** 4 — API layer
- **Implements / restores:** SR-031.3; remediates TASK-022, TASK-069 (and the CSRF gap in TASK-061/063/065/066)
- **Depends on:** TASK-069 (merged)
- **Branch:** `feature/csrf-enforcement`
- **Status:** Not started
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

- [ ] Every state-changing request without a valid CSRF token is rejected with **403 problem+json**, on
  core routes **and** mounted module routes (structural/route-introspection test).
- [ ] `POST /appointments`, `POST /accounts`, group/clinical/attachment mutations all require CSRF.
- [ ] Public no-session flows (login, activation) are exempt and still work.
- [ ] A new router added without extra wiring inherits CSRF protection (regression test).

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Unit + integration tests pass (incl. negative missing-token → 403 for each router and a module route)
- [ ] OpenAPI regenerated; `X-CSRF-Token` header documented on state-changing ops (see TASK-068a)
- [ ] Traceability row updated (SR-031.3 → TASK-069a → tests)
- [ ] Security review completed (SR-031.6)
