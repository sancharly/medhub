# TASK-024 — Account lockout

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-AUTH / U-AUTH-Lockout
- **Implements:** SR-029 (account lockout after failed login attempts)
- **Depends on:** TASK-023 (login flow — the counter is incremented/reset there)
- **Branch:** `feature/account-lockout`
- **Status:** Completed

## Objective

Limit automated brute-force / credential-stuffing by locking an account for 30 minutes after 5
consecutive failed login attempts, treating wrong-password and unknown-username identically, and
surfacing the lock generically (indistinguishable from invalid credentials). Provides an admin
manual unlock and audits every lockout. This layers onto the login orchestration of TASK-023 and
runtime view §6.1.

## Interfaces to honor

Provides an internal `LockoutService` consumed by `LoginService` (TASK-023):

```python
class LockoutService:
    def is_locked(self, account_id: UUID | None) -> bool: ...
    def record_failure(self, account_id: UUID | None, email: str, ip: str) -> None: ...  # increments; locks at threshold
    def reset(self, account_id: UUID) -> None: ...        # on successful login (SR-029.4)
    def admin_unlock(self, account_id: UUID, actor: Account) -> None: ...  # SR-029.3
```

`account_id` is `None` for unknown-username attempts so they are counted/handled identically to
wrong-password attempts without disclosing existence (SR-029.1) — keyed by a stable surrogate
(see below). Consumes `AuditService` (TASK-014).

Must **not**: distinguish "locked" from "invalid credentials" in any caller-visible output during
the lockout period (SR-029.6) — that mapping lives in TASK-023's generic 401.

## Implementation detail

- Files to create:
  - `backend/app/auth/lockout.py` — `LockoutService`, constants.
- Counter store: **Redis** (SI-AUTH owns Redis, §12.3.3). Key the counter by a stable identifier
  derived from the **submitted email** (e.g. `lockout:{sha256(normalized_email)}`) so unknown and
  existing accounts are counted identically and no enumeration leaks (SR-029.1). When the email
  maps to a real account, the lock state is also reflected on the account so admin unlock and the
  login check are consistent.
- Constants (SR-029): `MAX_FAILURES = 5` (AC-1), `LOCK_DURATION = 30 min` (AC-2). The lock is a
  Redis key with a 30-minute TTL → **automatic re-enable** on expiry (AC-2) with no admin action.
- `record_failure`: increment counter; at the **5th consecutive** failure set the lock key (30 min
  TTL) and audit `ACCOUNT_LOCKOUT` (SR-029.5) with attempted username, source IP, timestamp.
- `reset`: clear counter and lock on successful login (SR-029.4).
- `admin_unlock`: SYSADMIN clears the lock and counter before expiry (SR-029.3); audited
  (`ACCOUNT_UNLOCK`, actor + target). Exposed to the lifecycle/admin endpoints (TASK-060/095).
- Edge: the counter resets implicitly when its window/TTL lapses; "consecutive" means it is reset
  on any success (SR-029.4) — non-consecutive failures interleaved with a success do not stack.
- Error cases: none new; login maps a locked account to the generic 401 (SR-029.6, api-design.md
  423 surfaced as 401).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/auth/test_lockout.py`) with fakeredis + frozen clock:
  - 5 consecutive failures lock the account; the 5th triggers the lock and `ACCOUNT_LOCKOUT` audit
    (SR-029.1, AC-5).
  - Unknown-username failures increment the same keyed counter and lock identically — no behavioral
    difference vs. a real account (SR-029.1).
  - While locked, `is_locked` is True; after 30 min TTL it auto-clears (SR-029.2).
  - A successful login (`reset`) zeroes the counter so the next failure starts fresh (SR-029.4).
  - `admin_unlock` by SYSADMIN clears the lock before expiry and audits it (SR-029.3).
  - Lockout audit record includes attempted username, source IP, timestamp; no password (SR-029.5).
- Integration (`backend/tests/api/test_lockout_integration.py`): 5 bad `POST /auth/login` calls →
  the 6th returns the **same generic 401** as an invalid-credentials attempt (SR-029.6).

## Acceptance criteria

Distilled from SR-029:

- [ ] 5 consecutive failures lock the account; unknown-username and wrong-password counted alike (AC-1).
- [ ] Lock lasts 30 min then auto-re-enables (AC-2).
- [ ] SYSADMIN can manually unlock before expiry (AC-3).
- [ ] Counter resets on successful login (AC-4).
- [ ] Each lockout audited with attempted username, source IP, timestamp (AC-5).
- [ ] Locked state is indistinguishable from invalid credentials to the user (AC-6).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit (and required integration) tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (N/A — endpoint wiring in TASK-060)
- [ ] Audit events emitted for security-relevant actions (ACCOUNT_LOCKOUT / ACCOUNT_UNLOCK — SR-029.5)
- [ ] Traceability matrix row updated (SR-029 → TASK-024 → tests)
- [ ] Security review completed (auth/session/authz task — SR-031.6)
