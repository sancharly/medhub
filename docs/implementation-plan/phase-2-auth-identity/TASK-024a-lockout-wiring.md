# TASK-024a — Wire account lockout into the login flow (remediation)

- **Phase:** 2 — Auth & identity
- **Implements / restores:** SR-029; remediates TASK-024, TASK-023
- **Depends on:** TASK-024 (LockoutService), TASK-023 (LoginService)
- **Branch:** `feature/lockout-wiring`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-024 verdict **FAIL**

## Objective

`LockoutService` is implemented and unit-tested, but `LoginService.login` accepts an optional
`lockout_svc` that the auth router **never supplies** (`app/api/routers/auth.py`), so brute-force
protection does not run in production — the green unit tests exercise `LockoutService` directly, not the
wired login path. Wire it, and reconcile the two parallel counters (account-id keyed vs email keyed).

## Implementation detail

- Construct `LockoutService` in `_get_login_service` (deps) and pass it to `svc.login(...)`.
- Ensure failed logins increment, successful logins reset, and a locked account/email is rejected
  during login; reconcile `is_locked` so the email-keyed counter (unknown-account path) and the
  account-keyed counter agree (`app/auth/lockout.py`).
- Add an admin unlock endpoint `POST /accounts/{id}/unlock` (SYSADMIN, audited) — `admin_unlock` exists
  but is unreachable.

## Acceptance criteria

- [x] After N failed attempts the account is locked and subsequent correct credentials are rejected
  until the window elapses / admin unlock (SR-029) — verified through the **wired login endpoint**.
- [x] A successful login resets the counter.
- [x] Admin unlock endpoint exists, is SYSADMIN-only, and is audited.
- [x] Lockout events are audited; responses are generic (no enumeration).

## Definition of Done

- [x] Lint + type-check pass
- [x] **Integration** tests through `POST /auth/login` prove lock-after-N and reset (not unit-only)
- [x] OpenAPI regenerated (unlock endpoint)
- [x] Traceability row updated (SR-029 → TASK-024a → tests)
- [x] Security review completed (SR-031.6)
