---
id: "TASK-022"
type: task
title: "Hardened session cookie + CSRF token"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-030"
    relation: implements
  - target: "SR-031"
    relation: implements
  - target: "TASK-021"
    relation: relates_to
tags: ["phase:2-auth-session-authorization-identity"]
---

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-AUTH / U-AUTH-Cookie
- **Implements:** SR-030.6 (hardened cookie attributes); SR-031.3 (CSRF protection on state-changing requests)
- **Depends on:** TASK-021 (SessionService — the opaque id carried by the cookie)
- **Branch:** `feature/cookie-csrf`
- **Status:** Completed

## Objective

Deliver the opaque `session_id` to the browser in a cookie carrying `Secure`, `HttpOnly`,
`SameSite=Strict` (SR-030.6, ADR-0012), and issue/validate an anti-CSRF token so every
state-changing request (POST/PUT/PATCH/DELETE) is CSRF-protected (SR-031.3). This is the
transport hardening that makes the session token resistant to XSS theft and CSRF; the actual
session lifecycle lives in TASK-021 and the global header middleware in TASK-069.

## Interfaces to honor

No cross-item service interface; this unit provides FastAPI helpers consumed by SI-API:

```python
def set_session_cookie(response: Response, session_id: str) -> None: ...
def clear_session_cookie(response: Response) -> None: ...
def issue_csrf_token(response: Response) -> str: ...     # double-submit token
def require_csrf(request: Request) -> None: ...           # raises CsrfError on mismatch; FastAPI dependency
```

Cookie name `medhub_session`; CSRF cookie `medhub_csrf` (readable by JS for the double-submit
header), session cookie **not** JS-readable. Consumes `SessionService` output (the opaque id only).

Must **not**: store the session id anywhere JS-readable; weaken `SameSite`; apply CSRF checks to
safe methods (GET/HEAD/OPTIONS); set the global security headers (CSP/X-Frame-Options) — those are
the centralized middleware in TASK-069 (SR-031.2/4).

## Implementation detail

- Files to create:
  - `backend/app/auth/cookies.py` — cookie set/clear helpers, attribute constants.
  - `backend/app/auth/csrf.py` — `issue_csrf_token`, `require_csrf` dependency, `CsrfError`.
- Session cookie attributes (SR-030.6): `Secure=True`, `HttpOnly=True`, `SameSite="strict"`,
  `Path="/"`, no `Domain` pinning beyond deployment default, `Max-Age` aligned to the role
  inactivity timeout but treated as advisory (server TTL in Redis is authoritative). In
  non-production/local HTTP, `Secure` is driven by the `SESSION_COOKIE_SECURE` config (default
  `True`; only relaxable for local dev) — never silently disabled in production.
- CSRF (double-submit cookie pattern, complementary to `SameSite=Strict`, SR-031.3): on session
  creation issue `medhub_csrf` = `secrets.token_urlsafe(32)` (CSPRNG), `HttpOnly=False`,
  `Secure`, `SameSite=Strict`. The SPA echoes it in an `X-CSRF-Token` header on every
  state-changing request; `require_csrf` rejects when the header is missing or does not match the
  cookie (constant-time compare). Safe methods bypass the check.
- Config keys (TASK-003): `SESSION_COOKIE_NAME=medhub_session`, `CSRF_COOKIE_NAME=medhub_csrf`,
  `SESSION_COOKIE_SECURE=true`.
- Error cases: CSRF mismatch/absence → `CsrfError` mapped to
  `https://medhub.example/errors/forbidden` (403) by TASK-026; no protected data disclosed.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/auth/test_cookies.py`): `set_session_cookie` emits a `Set-Cookie` with
  `Secure; HttpOnly; SameSite=Strict; Path=/` (SR-030.6); `clear_session_cookie` expires it.
- Unit (`backend/tests/auth/test_csrf.py`):
  - State-changing request without `X-CSRF-Token` → `CsrfError` (403) (SR-031.3).
  - Header present but mismatching cookie → `CsrfError`.
  - Header matching cookie → passes.
  - GET/HEAD/OPTIONS bypass CSRF (SR-031.3).
- Integration (`backend/tests/api/test_csrf_integration.py`): a POST through the test client with a
  valid session cookie but no CSRF header gets 403 problem+json; with the header it succeeds.

## Acceptance criteria

- [x] Session cookie carries `Secure`, `HttpOnly`, `SameSite=Strict` (SR-030.6).
- [x] Session id is never JS-readable; only the CSRF token is (double-submit).
- [x] All POST/PUT/PATCH/DELETE require a valid CSRF token; safe methods do not (SR-031.3).
- [x] CSRF failures return 403 problem+json with no protected data (api-design.md).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit (and required integration) tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (N/A — helpers, no new schema)
- [x] Audit events emitted for security-relevant actions (N/A — login audit in TASK-023)
- [x] Traceability matrix row updated (SR-030.6, SR-031.3 → TASK-022 → tests)
- [x] Security review completed (auth/session/authz task — SR-031.6)

## Audit verdict (2026-06-29)

- **Verdict:** FAIL → PASS (remediated 2026-06-30)
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-069a completed. `CsrfError` extends `AuthorizationError` (403); `CsrfEnforcementMiddleware` in `backend/app/core/security_middleware.py` enforces CSRF on all state-changing requests centrally. Session cookie (`backend/app/auth/cookies.py`) carries `Secure`, `HttpOnly`, `SameSite=strict`. All AC and DoD items verified by QA 2026-06-30.
