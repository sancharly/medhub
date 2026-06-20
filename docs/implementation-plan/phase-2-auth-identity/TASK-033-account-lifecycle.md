# TASK-033 — Account deactivate / reactivate

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-IDENTITY / U-ID-Lifecycle
- **Implements:** SR-034.1–4 (deactivate with ≤30 s session kill; data retained; reactivate)
- **Depends on:** TASK-030 (AccountService), TASK-021 (SessionService)
- **Branch:** `feature/account-lifecycle`
- **Status:** Not started

## Objective

Let a system administrator deactivate any account (blocking access while retaining all data) and
reactivate it (restoring login with existing credentials, no new activation email). Deactivation
must terminate any active sessions **within 30 seconds** (SR-034.2) by both invalidating sessions
synchronously and dispatching the worker propagation (TASK-034). A SYSADMIN cannot deactivate
their own account (SR-034.1). This is the deactivate/reactivate branch of runtime view §6.5;
deletion/erasure is TASK-035.

## Interfaces to honor

Extends `AccountService` (from [12-interfaces.md](../../design/12-interfaces.md), SI-IDENTITY),
signatures verbatim:

```python
class AccountService:
    def deactivate(self, actor: Account, account_id: UUID) -> None: ...
    def reactivate(self, actor: Account, account_id: UUID) -> None: ...
```

Backs `POST /accounts/{id}/deactivate` and `POST /accounts/{id}/reactivate` (api-design.md,
SYSADMIN only). Consumes `AuthorizationService` (TASK-027), `SessionService.invalidate_all`
(TASK-021), the worker `propagate_session_kill` (TASK-034), the account repository (TASK-012),
`AuditService` (TASK-014).

Must **not**: delete or anonymize any data on deactivation (data is **retained**, SR-034.3 —
deletion is TASK-035); allow a SYSADMIN to deactivate their own account (SR-034.1); send a new
activation email on reactivate (SR-034.4); leave a deactivated account's session alive beyond 30 s
(SR-034.2).

## Implementation detail

- Files to create:
  - `backend/app/identity/lifecycle.py` — `deactivate`, `reactivate`.
- `deactivate(actor, account_id)` (SR-034.1/2/3):
  1. Authorize: SYSADMIN only (`AuthorizationService`); reject `actor.account_id == account_id`
     (no self-deactivation, SR-034.1) → `ConflictError`/`ForbiddenError`.
  2. Set account state INACTIVE/DEACTIVATED (distinct from never-activated; login rejects both).
  3. **Session kill ≤30 s (SR-034.2):** call `SessionService.invalidate_all(account_id)`
     synchronously (immediate, enumerable revocation, ADR-0012) **and** enqueue the worker
     `propagate_session_kill(account_id)` (TASK-034) as the belt-and-suspenders propagation path
     bounded to 30 s. The synchronous call already revokes; the worker covers any distributed
     propagation delay (SR-034.2 "30-second bound accommodates distributed session stores").
  4. Data (profile, clinical records, audit entries) is **untouched** and remains accessible to
     authorized users/admins (SR-034.3).
  5. Audit `ACCOUNT_DEACTIVATED` with acting admin, affected email + type, operation, ts (SR-034.8).
- `reactivate(actor, account_id)` (SR-034.4): SYSADMIN only; restore state to ACTIVE; the account
  logs in immediately with existing credentials; **no** new activation email; audit
  `ACCOUNT_REACTIVATED` (SR-034.8).
- A deactivated account cannot authenticate (SR-034.2) — enforced in login (TASK-023) as an
  invariant restated here.
- Error cases: self-deactivation → 403/409 (TASK-026); non-sysadmin → 403; unknown account → 404.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/identity/test_lifecycle.py`):
  - SYSADMIN deactivates any account type; state becomes DEACTIVATED; login then rejected
    (SR-034.1/2).
  - Deactivation calls `SessionService.invalidate_all` and enqueues `propagate_session_kill`
    (assert both) — sessions gone (SR-034.2).
  - SYSADMIN cannot deactivate their own account (SR-034.1).
  - Deactivated account's data (profile, clinical records, audit) still retrievable by authorized
    users (SR-034.3).
  - `reactivate` restores ACTIVE; account logs in with existing credentials; no activation email
    enqueued (SR-034.4).
  - Non-sysadmin deactivate/reactivate denied (SR-034.1).
  - Deactivate/reactivate audited with admin, affected email + type, op, ts (SR-034.8).
- Integration (`backend/tests/identity/test_deactivate_session_kill.py`, with TASK-021/034): after
  deactivation, `SessionService.resolve` returns `None` for all the account's sessions within the
  30 s bound (SR-034.2).

## Acceptance criteria

Distilled from SR-034.1–4 / .8:

- [ ] SYSADMIN can deactivate any account type except their own (AC-1).
- [ ] Deactivated account cannot authenticate; active sessions invalidated within 30 s (AC-2).
- [ ] Deactivated account's data is retained and remains accessible to authorized users (AC-3).
- [ ] SYSADMIN can reactivate; reactivated account logs in with existing credentials, no new email (AC-4).
- [ ] Deactivation and reactivation audited with admin, affected email + type, op, ts (AC-8).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit (and required integration) tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (lifecycle endpoints in TASK-062)
- [ ] Audit events emitted for security-relevant actions (ACCOUNT_DEACTIVATED / _REACTIVATED — SR-034.8)
- [ ] Traceability matrix row updated (SR-034.1–4 → TASK-033 → tests)
- [ ] Security review completed (auth/session/authz task — SR-031.6)
