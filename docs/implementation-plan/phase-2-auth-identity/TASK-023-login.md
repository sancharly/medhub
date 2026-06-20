# TASK-023 — Login flow

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-AUTH / U-AUTH-Login
- **Implements:** SR-002 (email/password authentication, generic failure); SR-029 (drives the
  lockout counter implemented in TASK-024)
- **Depends on:** TASK-020 (PasswordService), TASK-021 (SessionService), TASK-014 (AuditService)
- **Branch:** `feature/login-flow`
- **Status:** Not started

## Objective

Implement the credential-verification core of login: look up the account by email, verify the
password with Argon2id, and on success create a Redis session, set the hardened cookie + CSRF
token, and audit success; on any failure return a single **generic** error (no field disclosure,
no user enumeration) and audit the failure. This is the orchestration step of runtime view §6.1;
the lockout counter/threshold is layered in TASK-024 and the HTTP endpoint in TASK-060.

## Interfaces to honor

Provides an internal `LoginService.login(...)` used by the auth router:

```python
class LoginResult:  # discriminated: success carries session + csrf; failure carries only a generic code
    ...

class LoginService:
    def login(self, email: str, password: str, ip: str) -> LoginResult: ...  # generic failure, never raises per-field
```

Consumes `PasswordService.verify` (TASK-020), `SessionService.create_session` (TASK-021),
`AuditService.record` (TASK-014), the account repository (TASK-012), cookie/CSRF helpers (TASK-022).

Must **not**: reveal whether the email exists, the password was wrong, or the account is
locked/inactive — all map to the same generic failure (SR-002.2, SR-029.6); allow login for
INACTIVE accounts (SR-033.8); skip the audit side effect.

## Implementation detail

- Files to create:
  - `backend/app/auth/login.py` — `LoginService`, `LoginResult`.
- Flow (runtime §6.1):
  1. Normalize email (lowercase/trim). Look up account.
  2. **Always** run `PasswordService.verify` against a stored hash. If the account does not exist,
     verify against a fixed **dummy hash** so timing is uniform (anti-enumeration, SR-002.2,
     SR-029.1). Account-existence and password-correctness are indistinguishable to the caller.
  3. Reject (generic) when: account missing, password mismatch, account INACTIVE
     (SR-033.8), account locked (delegated to TASK-024, surfaced generically — SR-029.6), or
     password expired/`must_change_password` (route to forced-change rather than a session;
     SR-025 AC-6/AC-7 — return a distinct *internal* result the endpoint handles, still no
     enumeration leak).
  4. On success: reset the failed-attempt counter (SR-029.4), `create_session`, set cookie +
     issue CSRF (TASK-022), and return success including the 3-session-cap eviction notice if any
     (SR-030.7).
- Audit (SR-002, SR-029.5, §8.4): record `LOGIN_SUCCESS` (actor=account, ip, ts) and
  `LOGIN_FAILURE` (attempted email, ip, ts, generic reason); **never** log the password or which
  field failed.
- Error cases: every authentication failure → `https://medhub.example/errors/unauthenticated`
  (401), single generic message (api-design.md: 401 generic, no field disclosure; 423 account-locked
  is surfaced *as* 401 during login per SR-029.6).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/auth/test_login_service.py`):
  - Valid email+password for an ACTIVE account → success, session created, cookie+CSRF set,
    `LOGIN_SUCCESS` audited (SR-002.1).
  - Unknown email and wrong password produce the **identical** generic failure result and both
    audit `LOGIN_FAILURE` (SR-002.2, SR-029.1).
  - Unknown email path still calls `verify` against the dummy hash (timing-uniform; assert verify
    invoked) (SR-002.2).
  - INACTIVE account → generic failure, no session (SR-033.8).
  - Locked account → generic failure (indistinguishable from invalid creds) (SR-029.6).
  - Successful login resets the failed-attempt counter to zero (SR-029.4).
  - 4th concurrent successful login returns the eviction notice (SR-030.7).
  - No test path logs a plaintext password (SR-002.4).
- Integration (`backend/tests/api/test_login_integration.py`, with TASK-060): full `POST
  /auth/login` returns `Set-Cookie` (hardened) on success and a 401 generic problem+json on failure.

## Acceptance criteria

Distilled from SR-002 (and SR-029 interplay):

- [ ] Valid email/password grants a session (SR-002.1).
- [ ] Unknown email and wrong password are indistinguishable, generic failure (SR-002.2, SR-029.1/6).
- [ ] Unauthenticated/failed access is denied (SR-002.3); INACTIVE accounts cannot log in (SR-033.8).
- [ ] Passwords verified via Argon2id; never logged in clear text (SR-002.4).
- [ ] Successful login resets the failed-attempt counter (SR-029.4).
- [ ] Success and failure are audited (§8.4, SR-029.5).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit (and required integration) tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (endpoint wiring lands in TASK-060)
- [ ] Audit events emitted for security-relevant actions (LOGIN_SUCCESS / LOGIN_FAILURE — SR-023)
- [ ] Traceability matrix row updated (SR-002, SR-029 → TASK-023 → tests)
- [ ] Security review completed (auth/session/authz task — SR-031.6)
