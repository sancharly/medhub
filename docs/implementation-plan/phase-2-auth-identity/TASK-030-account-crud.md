# TASK-030 — AccountService create + profile

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-IDENTITY / U-ID-AccountCrud
- **Implements:** SR-003 (unique account + profile view), SR-004 (single user type), SR-032
  (role-constrained creation)
- **Depends on:** TASK-027 (AuthorizationService)
- **Branch:** `feature/account-crud`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Implement account creation and profile read in `SI-IDENTITY`: role-constrained creation (only
ADMIN/SYSADMIN may create; ADMIN cannot create SYSADMIN), mandatory minimum fields, system-wide
unique email, exactly one user type, and an INACTIVE initial state that blocks login until
activation (TASK-032). Creation triggers the activation email (TASK-031) and is audited. This is
the first gate guarding access to PHI (SR-032 rationale) and the runtime view §6.5 creation step.

## Interfaces to honor

Provided interface (from [12-interfaces.md](../../design/12-interfaces.md), SI-IDENTITY
`AccountService`), the create/read portion (lifecycle/activation/erasure are TASK-032/033/035):

```python
class AccountService:
    def create(self, creator: Account, data: AccountCreate) -> Account: ...  # role-constrained, INACTIVE
    # activate/deactivate/reactivate/delete/erase added by TASK-032/033/035
```

Plus profile read used by `GET /me` and `GET /accounts/{id}`:

```python
    def get_profile(self, actor: Account, account_id: UUID) -> Account: ...   # scoped by AuthorizationService
```

`AccountCreate` carries `first_name`, `surname`, `email`, `user_type` (∈ {PATIENT, DOCTOR, ADMIN,
SYSADMIN}, SR-004). Consumes `AuthorizationService` (TASK-027), the account repository (TASK-012),
`AuditService` (TASK-014), and enqueues `send_activation_email` (TASK-031). Profile read is scoped
by `AuthorizationService` (self for users; projection for ADMIN via TASK-029).

Must **not**: allow self-registration — creation requires an authenticated ADMIN/SYSADMIN session
(SR-032 AC-1); let ADMIN create SYSADMIN (privilege-escalation guard, SR-032 AC-4); create an
ACTIVE account (always INACTIVE first, SR-032 AC-6); accept a duplicate email.

## Implementation detail

- Files to create:
  - `backend/app/identity/account_service.py` — `AccountService` (create + profile), `AccountCreate`.
  - `backend/app/identity/__init__.py`.
- Creation flow (SR-032, runtime §6.5):
  1. Authorize: `AuthorizationService.authorize(creator, "account:create", target_type)` — only
     ADMIN/SYSADMIN (SR-032 AC-1). Role-pair rule: ADMIN may create only {PATIENT, DOCTOR, ADMIN}
     (SR-032 AC-4); SYSADMIN may create all four including SYSADMIN (SR-032 AC-5). Enforced
     **server-side**, not by client choice (SR-032 control measure).
  2. Validate mandatory fields present/non-empty: first name, surname, email (SR-032 AC-2) — via
     Pydantic v2 at the boundary (authoritative).
  3. Unique email across **all** accounts including inactive/deleted-then-released (SR-032 AC-3):
     application check **plus** a DB unique constraint (TASK-011) for the race; duplicate →
     `ConflictError` 409 `/errors/conflict` (SR-032.3, TASK-026).
  4. Set exactly one `user_type` (SR-004 AC-1/AC-2); persist with state **INACTIVE** (SR-032 AC-6).
  5. Enqueue `send_activation_email` (TASK-031) → kicks off SR-033 flow.
  6. Audit `ACCOUNT_CREATED` with creator identity, new email + type, ts (SR-032 AC-7).
- Profile read (SR-003/SR-007): `get_profile` returns the caller's own account (SR-003 AC-2); other
  accounts only where the role permits (SR-003 AC-3) — delegated to `AuthorizationService` +
  admin projection (TASK-029).
- SYSADMIN may change an account's user type (SR-004 AC-3) — exposed as a guarded update used by
  the admin UI (TASK-095); minimal here, full lifecycle in TASK-033.
- Config keys: none beyond TASK-003.
- Error cases: missing field → 400 `/errors/validation-error`; duplicate email → 409
  `/errors/conflict`; unauthorized creator/role-pair → 403 `/errors/forbidden`.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/identity/test_account_service.py`):
  - Creation by ADMIN of PATIENT/DOCTOR/ADMIN succeeds, INACTIVE, activation email enqueued
    (SR-032 AC-6, SR-033.1).
  - ADMIN creating SYSADMIN → denied (403), privilege escalation blocked (SR-032 AC-4).
  - SYSADMIN can create all four types including SYSADMIN (SR-032 AC-5).
  - Unauthenticated / non-admin creator → denied (SR-032 AC-1).
  - Missing first name / surname / email → validation error (SR-032 AC-2).
  - Duplicate email (active, inactive, or previously-deleted-then-reused address still registered)
    → 409 conflict (SR-032 AC-3).
  - Account always created with exactly one user type and INACTIVE state (SR-004 AC-1, SR-032 AC-6).
  - `ACCOUNT_CREATED` audited with creator, email, type, ts (SR-032 AC-7).
  - `get_profile` returns own profile; cross-account read denied unless role permits (SR-003 AC-2/AC-3).
- Integration (`backend/tests/identity/test_account_unique_email.py`): the DB unique constraint
  rejects a concurrent duplicate-email insert (SR-032 AC-3 control measure).

## Acceptance criteria

Distilled from SR-032 / SR-004 / SR-003:

- [x] Only authenticated ADMIN/SYSADMIN can create accounts; no self-registration (SR-032 AC-1).
- [x] First name, surname, email mandatory (SR-032 AC-2); email unique system-wide (SR-032 AC-3).
- [x] ADMIN cannot create SYSADMIN; SYSADMIN can create all types (SR-032 AC-4/AC-5).
- [x] New account is INACTIVE and cannot log in until activated (SR-032 AC-6).
- [x] Exactly one user type from the four; required at creation (SR-004 AC-1/AC-2).
- [x] Creation audited with creator, new email + type, timestamp (SR-032 AC-7).
- [x] Authenticated user can view own profile; cross-account read role-gated (SR-003 AC-2/AC-3).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit (and required integration) tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (account endpoints land in TASK-061/067)
- [x] Audit events emitted for security-relevant actions (ACCOUNT_CREATED — SR-032 AC-7)
- [x] Traceability matrix row updated (SR-003, SR-004, SR-032 → TASK-030 → tests)
- [x] Security review completed (N/A for auth-gate per template, but creation guards privilege
      escalation — include in the SR-031.6 review scope)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
