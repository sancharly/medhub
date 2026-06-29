# TASK-060 — Auth & session endpoints

- **Phase:** 4 — API layer
- **Software item / unit:** SI-API / U-API-Routers, U-API-DTO
- **Implements:** SR-002 (login, generic failure); SR-029 (lockout surfaced generically);
  SR-030 (logout, session extend); SR-025 (password change with policy + history)
- **Depends on:** TASK-023 (LoginService), TASK-024 (lockout), TASK-022 (cookie/CSRF), TASK-020
  (PasswordService) — must be merged first
- **Branch:** `feature/auth-endpoints`
- **Status:** In Progress (audit 2026-06-29)

## Objective

Expose the HTTP surface of SI-AUTH: `POST /auth/login`, `POST /auth/logout`,
`POST /auth/session/extend`, and `POST /auth/password`. Each router function is a thin adapter that
validates the request DTO (Pydantic v2, authoritative — SR-031.5), delegates to the already-built
SI-AUTH services, sets/clears the hardened cookie + CSRF token (TASK-022), and renders RFC 7807
errors. Login and password-change failures are **generic** (no field/enumeration disclosure,
SR-002.2, SR-029.6). Traces to SR-002, SR-029, SR-030, SR-025.

## Interfaces to honor

HTTP contract (verbatim from [api-design.md](../../specifications/api-design.md)):

| Method & path               | Purpose                                | Key reqs               |
|-----------------------------|----------------------------------------|------------------------|
| `POST /auth/login`          | email+password → session cookie        | SR-002, SR-029, SR-030 |
| `POST /auth/logout`         | invalidate server-side session         | SR-030.5               |
| `POST /auth/session/extend` | reset inactivity timer                 | SR-030.4               |
| `POST /auth/password`       | change password (policy + history)     | SR-025                 |

Consumes (in-process, [12-interfaces.md](../../design/12-interfaces.md) §12.1) **verbatim**:

```python
LoginService.login(self, email: str, password: str, ip: str) -> LoginResult   # TASK-023
SessionService.invalidate(self, session_id: str) -> None                       # TASK-021
SessionService.resolve(self, session_id: str) -> Session | None                # extend: touch TTL
PasswordService.validate_policy(self, account: Account, password: str) -> None # TASK-020 (raises)
PasswordService.hash(self, password: str) -> str                               # TASK-020
```

Uses the SI-API plumbing: `get_session`/`get_current_user`/`require(...)` (TASK-025), cookie/CSRF
helpers (TASK-022), error handlers (TASK-026), `AuditService.record` (TASK-014).

Must **not**: re-implement credential verification, lockout counting, or session lifecycle (those
are TASK-023/024/021); disclose which field failed or whether an account exists on login or
password change (SR-002.2, SR-029.6); skip the `require_csrf` dependency on these state-changing
POSTs (SR-031.3); accept the actor id from the request body — the authenticated session is the only
source (SR-031.5).

## Implementation detail

- Files to create:
  - `backend/app/api/routers/auth.py` — `APIRouter(prefix="/auth")` with the four endpoints.
  - `backend/app/api/schemas/auth.py` — Pydantic v2 DTOs (camelCase):
    - `LoginRequest { email: EmailStr, password: str }`
    - `LoginResponse { user: MeSummary, mustChangePassword: bool, evictedSession: bool }`
      (the eviction notice surfaces SR-030.7; the forced-change flag surfaces SR-025.6/AC-7)
    - `PasswordChangeRequest { currentPassword: str, newPassword: str, confirmNewPassword: str }`
    - `SessionExtendResponse { expiresAt: datetime }`
  - Wire the router into the app factory (`backend/app/main.py`) under `/api/v1`.
- `POST /auth/login` (unauthenticated route, explicitly listed): call `LoginService.login(email,
  password, request.client.host)`. On success: `set_session_cookie` + `issue_csrf_token`
  (TASK-022), 200 `LoginResponse`. On the forced-change internal result, return 200 with
  `mustChangePassword=true` and **no** general session (route the SPA to the change-password flow,
  SR-025.6). On any failure: 401 `/errors/unauthenticated` (generic). Locked accounts are surfaced
  as 401, not 423, during login (SR-029.6). Login success/failure audited by TASK-023.
- `POST /auth/logout` (authenticated, CSRF-checked): `SessionService.invalidate(session_id)` then
  `clear_session_cookie`; 204. Idempotent — invalidating an already-dead session still returns 204.
  Audit `LOGOUT` (SR-023, §8.4).
- `POST /auth/session/extend` (authenticated, CSRF-checked): touch the session TTL via
  `SessionService` (sliding inactivity, ADR-0012), return 200 `SessionExtendResponse` with the new
  `expiresAt`. This is the server side of the 2-minute warning (SR-030.4); does **not** bypass the
  8-hour absolute lifetime — if the absolute cap is reached, return 401 (re-auth required, SR-030.3).
- `POST /auth/password` (authenticated, CSRF-checked): verify `currentPassword` via
  `PasswordService.verify`; require `newPassword == confirmNewPassword`;
  `PasswordService.validate_policy(account, newPassword)` enforces **all four** character classes,
  12-char minimum, username/email substring rejection, **history of 12**, and **max age 180 days**
  reset on change (SR-025 AC-1..7, authoritative server-side). On success: `hash` + persist, push the
  old hash onto the 12-entry history, reset `must_change_password`, **invalidate other sessions**
  (ADR-0012). Audit `PASSWORD_CHANGE` (SR-023). On policy violation: 400 `/errors/validation-error`
  with one `errors[]` entry per violated rule (SR-025.5); mismatch → 400 with a generic mismatch
  message (no per-field disclosure, SR-033.4 parity).
- Error cases (RFC 7807, base `https://medhub.example/errors/`): login/lockout failures → `401
  /errors/unauthenticated`; CSRF absent/mismatch → `403 /errors/forbidden`; password policy/mismatch
  → `400 /errors/validation-error`; absolute-lifetime exceeded on extend → `401`.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/api/test_auth_router.py`):
  - `POST /auth/login` happy path → 200 + `Set-Cookie` (`Secure; HttpOnly; SameSite=Strict`) +
    CSRF cookie (SR-002.1, SR-030.6).
  - Unknown email and wrong password both → identical 401 `/errors/unauthenticated`, no
    enumeration (SR-002.2, SR-029.1).
  - Locked account during login → 401 (not 423), indistinguishable from invalid creds (SR-029.6).
  - `mustChangePassword` result routes to change flow, grants no general session (SR-025.6).
  - 4th concurrent login returns `evictedSession=true` (SR-030.7).
  - `POST /auth/logout` invalidates the session, clears the cookie, 204; second call still 204
    (SR-030.5).
  - `POST /auth/session/extend` touches TTL, returns new `expiresAt`; past the 8-hour absolute cap →
    401 (SR-030.3/4).
  - `POST /auth/password`: rejects a password missing any of the four classes / under 12 chars /
    containing the username/email / matching any of the last 12 / unchanged max-age on success
    (SR-025 AC-1..7); mismatch of new/confirm → 400 generic; success invalidates sibling sessions.
  - Every state-changing endpoint rejects a missing `X-CSRF-Token` with 403 (SR-031.3).
- Integration (`backend/tests/api/test_auth_integration.py`): end-to-end login → authenticated
  call → extend → logout through the test client; problem+json shape verified on each failure.

## Acceptance criteria

- [ ] Valid email/password grants a session via `Set-Cookie` (SR-002.1, SR-030.6).
- [ ] Unknown email, wrong password, and locked account are indistinguishable 401s (SR-002.2, SR-029.6).
- [ ] Logout immediately invalidates the server-side session (SR-030.5).
- [ ] Session extend resets the inactivity timer but not the 8-hour absolute cap (SR-030.3/4).
- [ ] Password change enforces all four classes, 12-char min, username/email exclusion, history of 12,
      and 180-day max age — server-side authoritative (SR-025 AC-1..7).
- [ ] All four POSTs require a valid CSRF token (SR-031.3); errors are problem+json.
- [ ] Login/logout/password-change are audited (SR-023, §8.4).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit + integration tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (four auth endpoints + DTOs + problem+json responses)
- [ ] Audit events emitted for security-relevant actions (LOGIN/LOGOUT/PASSWORD_CHANGE — SR-023)
- [ ] Traceability matrix row updated (SR-002, SR-029, SR-030, SR-025 → TASK-060 → tests)
- [ ] **Security review completed (auth/session task — SR-031.6)**

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-069a / TASK-068a. Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
