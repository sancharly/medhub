# TASK-020 — PasswordService (policy + Argon2id)

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-AUTH / U-AUTH-PasswordPolicy
- **Implements:** SR-025 (password complexity & lifecycle), SR-002.4 (salted hashing, never clear text)
- **Depends on:** TASK-012 (typed repositories — password-history persistence)
- **Branch:** `feature/password-service`
- **Status:** Completed

## Objective

Provide the single server-side authority for password strength, lifecycle, and one-way
hashing. `PasswordService` validates every candidate password against the SR-025 complexity and
history/age policy, hashes accepted passwords with Argon2id, and verifies presented passwords —
so that no other unit re-implements policy or touches a raw credential. This is the credential
foundation for login (TASK-023), activation (TASK-032) and the erasure retrieval code
(TASK-035). Client-side validation is convenience only; this unit is authoritative (SR-025 AC-5,
SR-031.5, §8.6).

## Interfaces to honor

Provided in-process interface (from [12-interfaces.md](../../design/12-interfaces.md), SI-AUTH
`PasswordService`), signatures verbatim:

```python
class PasswordService:
    def validate_policy(self, account: Account, password: str) -> None: ...  # raises PasswordPolicyError on violation
    def hash(self, password: str) -> str: ...                                # Argon2id encoded hash
    def verify(self, hash: str, password: str) -> bool: ...                  # constant-time verify
```

Consumers: SI-IDENTITY (activation, account create), SI-API (`POST /auth/password`).

Must **not**: log, return, or persist any plaintext password (SR-002.4); store the password
history as plaintext (store only Argon2id hashes); implement its own DB access beyond the
repositories from TASK-012; expose which rule failed to the *attacker* path — it returns
structured rule violations to the caller, which the API maps to a field-level RFC 7807 body
(rule identity is shown only to the authenticated user setting their own password, SR-025 AC-5).

## Implementation detail

- Files to create:
  - `backend/app/auth/password.py` — `PasswordService`, `PasswordPolicyError`,
    `PasswordPolicyViolation` (enum of rule ids), policy constants.
  - `backend/app/auth/__init__.py` — export `PasswordService`.
- Library: **argon2-cffi** (`argon2.PasswordHasher`) — Argon2id is the default variant. Use the
  library default tuned parameters; do not hand-roll crypto (ADR-0011 posture). `verify()` wraps
  `PasswordHasher.verify` and returns `False` on `VerifyMismatchError` (never raises to the caller
  for a wrong password). Expose `check_needs_rehash` for future parameter upgrades.
- Policy constants (SR-025, authoritative — **note**: the SR fixes history=12 and max-age=180d;
  the planning shorthand "history of 5 / 365-day age" is superseded by the approved SR-025 ACs):
  - `MIN_LENGTH = 12` (SR-025 AC-1).
  - Four character classes, at least three-of-four **plus** the SR-025 AC-2 wording requires **all
    four** classes (uppercase, lowercase, digit, special from
    `!@#$%^&*()-_=+[]{}|;:'",.<>?/`). Implement AC-2 as written: reject unless **each** of the four
    classes is present. (If the design review later relaxes to "≥3 of 4", change only this rule and
    its test.)
  - `HISTORY_DEPTH = 12` — reject if the new password matches any of the user's last 12 (SR-025 AC-4).
  - `MAX_AGE_DAYS = 180`, `EXPIRY_WARNING_DAYS = 14` (SR-025 AC-7).
  - Reject if the password contains the account email or username as a case-insensitive substring
    (SR-025 AC-3).
- Password history: persisted via a `PasswordHistory` repository (rows
  `(account_id, password_hash, created_at)`); `validate_policy` calls `verify()` against the most
  recent `HISTORY_DEPTH` hashes (model/migration land in TASK-010/011 — this task adds the
  repository method if missing and the history-append helper invoked by callers on a successful set).
- Age / expiry: `Account.password_changed_at` drives `is_expired(account)` and
  `expires_within(account, days)` helpers used by login (TASK-023) and the change-password endpoint;
  this unit exposes the predicates, the enforcement (force-change on next login) is wired by the caller.
- Temporary/admin-assigned password must be force-changed on first login (SR-025 AC-6) — exposed as
  `Account.must_change_password` predicate honored by login (TASK-023).
- Error cases: `PasswordPolicyError` carries a list of `PasswordPolicyViolation` (one per failed
  rule); the API layer (TASK-026) maps it to `https://medhub.example/errors/validation-error` (400)
  with field-level `errors[]`, one entry per violated rule (api-design.md error catalog).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/auth/test_password_service.py`):
  - Rejects < 12 chars → `PasswordPolicyError` (SR-025 AC-1).
  - Rejects when any character class is missing; accepts when all four present (SR-025 AC-2), one
    parametrized case per missing class.
  - Rejects password containing email/username substring, case-insensitive (SR-025 AC-3).
  - Rejects a password matching any of the last 12 stored hashes; accepts the 13th-oldest (SR-025 AC-4).
  - `hash()` output is an Argon2id encoded string (`$argon2id$`), differs across calls (random salt),
    and is never equal to the input (SR-002.4).
  - `verify()` returns True for the matching password, False for a wrong one, and does not raise.
  - `is_expired` / `expires_within(14)` boundary cases at 180 days and 166 days (SR-025 AC-7).
  - No test fixture or assertion ever logs/echoes a plaintext password (SR-002.4) — assert logs are clean.
- Integration (`backend/tests/auth/test_password_history_repo.py`): policy check against the real
  `PasswordHistory` repository proves the union-of-last-12 query (crosses the SI-PERSIST interface).

## Acceptance criteria

Distilled from SR-025 (and SR-002.4):

- [ ] Passwords < 12 chars rejected (AC-1).
- [ ] All four character classes required (AC-2).
- [ ] Email/username substring rejected, case-insensitive (AC-3).
- [ ] New password matching any of last 12 rejected (AC-4).
- [ ] Violation error identifies the violated rule(s) to the user setting the password (AC-5).
- [ ] Predicate available to force-change a system-assigned password on first login (AC-6).
- [ ] 180-day max age and 14-day pre-expiry warning predicates available (AC-7).
- [ ] Passwords stored only as Argon2id salted hashes; never logged in clear text (SR-002.4).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit (and required integration) tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (N/A — no endpoint in this task)
- [ ] Audit events emitted for security-relevant actions (N/A — caller audits credential changes)
- [ ] Traceability matrix row updated (SR-025, SR-002.4 → TASK-020 → tests)
- [ ] Security review completed (auth/session/authz task — SR-031.6)
