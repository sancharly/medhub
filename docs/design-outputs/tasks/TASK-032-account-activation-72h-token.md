---
id: "TASK-032"
type: task
title: "Account activation (72h token)"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-033"
    relation: implements
  - target: "TASK-030"
    relation: relates_to
  - target: "TASK-031"
    relation: relates_to
  - target: "TASK-020"
    relation: relates_to
tags: ["phase:2-auth-session-authorization-identity"]
---

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-IDENTITY / U-ID-Activation
- **Implements:** SR-033 (account activation via email)
- **Depends on:** TASK-030 (AccountService create), TASK-031 (email task), TASK-020 (PasswordService)
- **Branch:** `feature/account-activation`
- **Status:** Completed

## Objective

Convert an INACTIVE account into an ACTIVE one via a single-use, 72-hour activation link: validate
the token, present a password-creation form, accept a policy-compliant password entered twice,
transition the account to ACTIVE, and invalidate the link. Provide admin resend that issues a new
single-use link and invalidates the prior one. This is the SR-033 flow in runtime view §6.5 and
the second gate before any PHI access (the user, not an admin, sets their own credential).

## Interfaces to honor

Extends `AccountService` (from [12-interfaces.md](../../design/12-interfaces.md), SI-IDENTITY),
signature verbatim for activation:

```python
class AccountService:
    def activate(self, token: str, password: str) -> Account: ...   # validates token + policy, sets ACTIVE
    # plus token issuance + resend helpers:
    def issue_activation_token(self, account_id: UUID) -> str: ...   # single-use, 72h
    def resend_activation(self, actor: Account, account_id: UUID) -> None: ...  # new link, invalidates prior
```

Backs `GET /activation/{token}` (validate) and `POST /activation/{token}` (set password ×2,
activate) and `POST /accounts/{id}/resend-activation` (api-design.md). Consumes `PasswordService`
(TASK-020), the email task (TASK-031), the account repository (TASK-012), `AuditService` (TASK-014).

Must **not**: store the activation token in recoverable form if it doubles as a secret — store a
**hash** of the token and compare (consistent with credential posture); allow login before ACTIVE
(SR-033.8); allow a used or expired link to activate (SR-033.2/5); reveal which of the two password
fields differs on mismatch (SR-033.4).

## Implementation detail

- Files to create:
  - `backend/app/identity/activation.py` — token issue/validate/consume, `activate`,
    `resend_activation`.
- Token: `secrets.token_urlsafe(32)` (CSPRNG, single-use). Persist `activation_token_hash`
  (sha256) + `activation_token_expires_at = now + 72h` on the account (model/migration TASK-010/011;
  add columns/repository methods if missing). The raw token goes only into the email (TASK-031);
  the DB holds the hash (no plaintext token at rest).
- Validity: 72 hours from issuance (SR-033.2). `GET /activation/{token}` validates: token hash
  matches, not expired, account still INACTIVE → returns OK to render the form; else reject.
- `activate(token, password)` (SR-033.3/4/5):
  1. Validate token (hash match, unexpired, account INACTIVE).
  2. `PasswordService.validate_policy(account, password)` — full SR-025 rules (SR-033.3).
  3. The endpoint enforces the **two-field match** (Password / Confirm password) before calling
     `activate`; mismatch → generic mismatch error, no field-specific leak (SR-033.4).
  4. `PasswordService.hash`, store; append to password history (TASK-020); set state **ACTIVE**;
     clear/invalidate the token (single-use, SR-033.5).
  5. Audit `ACCOUNT_ACTIVATED` (email + ts) (SR-033.9).
- `resend_activation` (SR-033.7): ADMIN/SYSADMIN only (authorized via `AuthorizationService`);
  issue a new token (invalidating any prior by overwriting the stored hash) and enqueue
  `send_activation_email`; audit `ACTIVATION_LINK_RESENT` and link-expiry context (SR-033.9).
- INACTIVE accounts cannot authenticate (SR-033.8) — enforced in login (TASK-023); restated here as
  an invariant.
- Error cases: expired/used/unknown token → `https://medhub.example/errors/not-found` (404) or a
  generic rejection (do not distinguish expired vs. invalid to avoid enumeration); policy violation
  → 400 `/errors/validation-error` with the violated rule (SR-033.3 + SR-025 AC-5); password
  mismatch → 400 generic mismatch (SR-033.4).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/identity/test_activation.py`) with frozen clock:
  - Valid token + policy-compliant matching password → account ACTIVE, token invalidated, can then
    log in (SR-033.5/6).
  - Token older than 72 h → rejected, cannot activate (SR-033.2).
  - Re-using an already-consumed token → rejected (single-use) (SR-033.5).
  - Policy-violating password → validation error naming the rule (SR-033.3, SR-025 AC-5).
  - Two-field mismatch → generic mismatch error, no field-specific disclosure (SR-033.4).
  - INACTIVE account cannot authenticate before activation (SR-033.8, cross-check with login).
  - `resend_activation` by ADMIN issues a new token and **invalidates the previous** link; non-admin
    resend denied (SR-033.7).
  - The raw token is never persisted (only its hash) and never audited (SR-033.9).
- Integration (`backend/tests/api/test_activation_flow.py`): `GET` then `POST /activation/{token}`
  end-to-end → 200 + ACTIVE; expired token → rejected.

## Acceptance criteria

Distilled from SR-033:

- [x] Activation email with a single-use link sent on creation (SR-033.1, via TASK-031).
- [x] Link valid 72 h; rejected after expiry (SR-033.2).
- [x] Activation enforces full SR-025 password policy (SR-033.3).
- [x] Password entered twice; mismatch rejected without field-specific disclosure (SR-033.4).
- [x] On valid set, account → ACTIVE and link invalidated (single-use) (SR-033.5).
- [x] Activated account can log in with the set password (SR-033.6).
- [x] Admin resend issues a new single-use link and invalidates the prior one (SR-033.7).
- [x] INACTIVE accounts cannot authenticate (SR-033.8).
- [x] Link-sent / activated / resend events audited with email + ts; never the token (SR-033.9).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit (and required integration) tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (activation endpoints in TASK-061)
- [x] Audit events emitted for security-relevant actions (ACCOUNT_ACTIVATED / link sent / resent — SR-033.9)
- [x] Traceability matrix row updated (SR-033 → TASK-032 → tests). SR-033 row in traceability-matrix.md maps to SI-IDENTITY (U-ID-Activation) + SI-WORKER (U-WK-Email). TASK-032 declares `Implements: SR-033`; new tests reference SR-033.1 and SR-033.7 ACs by name.
- [x] Security review completed. QA Engineer review (2026-06-28) verified: raw token never appears in logs or audit records (audit emits email + timestamp only, SR-033.9); `secrets.compare_digest` used for constant-time hash comparison; token hash stored as SHA-256 (no plaintext at rest); `issue_activation_token` moved outside best-effort try block so token issuance failures surface as exceptions rather than silently producing stuck-inactive accounts.

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL → PASS (remediated 2026-06-30)
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-026a completed. `ActivationRequest` schema now includes `confirm_password: str`; `backend/app/api/routers/activation.py` checks `body.password != body.confirm_password` before calling `svc.activate()` and raises `ValidationProblem` (400) on mismatch. `PasswordPolicyError` extends `ValidationProblem` so policy violations return 400 not 500. Tests in `backend/tests/api/test_activation_router.py` verify mismatch→400 and missing-confirm→400/422. All AC and DoD items verified by QA 2026-06-30.
