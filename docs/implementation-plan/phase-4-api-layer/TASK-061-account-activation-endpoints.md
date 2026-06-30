# TASK-061 — Account & activation endpoints

- **Phase:** 4 — API layer
- **Software item / unit:** SI-API / U-API-Routers, U-API-DTO
- **Implements:** SR-032 (role-constrained account creation, mandatory fields, unique email,
  inactive on create); SR-033 (email activation: validate token, set password ×2, activate, resend)
- **Depends on:** TASK-030 (AccountService.create / read), TASK-032 (activation) — must be merged
  first
- **Branch:** `feature/account-activation-endpoints`
- **Status:** Completed

## Objective

Expose the account-creation and activation HTTP surface of SI-IDENTITY: privileged account creation
and read (`POST /accounts`, `GET /accounts`, `GET /accounts/{id}`), the public activation flow
(`GET /activation/{token}`, `POST /activation/{token}`), and admin resend
(`POST /accounts/{id}/resend-activation`). Routers are thin adapters delegating to `AccountService`;
the creator-role constraint and uniqueness are enforced server-side (SR-032), and the password set
at activation goes through the full SR-025 policy. Traces to SR-032, SR-033.

## Interfaces to honor

HTTP contract (verbatim from [api-design.md](../../specifications/api-design.md)):

| Method & path                           | Purpose                                          | Key reqs         |
|-----------------------------------------|--------------------------------------------------|------------------|
| `POST /accounts`                        | create account (role-constrained) → activation   | SR-032, SR-033.1 |
| `GET /accounts`                         | list (non-clinical projection for admin)         | SR-009           |
| `GET /accounts/{id}`                    | view account                                     | SR-003, SR-009   |
| `GET /activation/{token}`               | validate activation token                        | SR-033.2         |
| `POST /activation/{token}`              | set password (×2), activate                      | SR-033.3/4/5     |
| `POST /accounts/{id}/resend-activation` | new single-use link, invalidates prior           | SR-033.7         |

Consumes ([12-interfaces.md](../../design/12-interfaces.md) §12.1) **verbatim**:

```python
AccountService.create(self, creator: Account, data: AccountCreate) -> Account     # TASK-030
AccountService.activate(self, token: str, password: str) -> Account               # TASK-032
# token validation + resend live in TASK-032 (U-ID-Activation); router calls those service methods
```

Protected endpoints (`/accounts*`) declare the `require(action, resource_loader)` guard (TASK-025);
`AuthorizationService` (TASK-027) authorizes deny-by-default. Activation endpoints
(`/activation/{token}`) are **token-authorized, no session** — explicitly listed as unauthenticated
routes; the token itself is the authorization. Uses error handlers (TASK-026), `AuditService`.

Must **not**: allow self-registration — `/accounts` requires an admin/sysadmin session (SR-032.1);
let the client decide which account types it may create — the creator role gates allowed types
server-side (SR-032.4/5); return clinical fields in the admin projection (SR-009); leak whether an
email exists other than via the documented 409 on create (SR-032.3).

## Implementation detail

- Files to create:
  - `backend/app/api/routers/accounts.py` — `APIRouter(prefix="/accounts")` (create/list/get,
    resend-activation) + `APIRouter(prefix="/activation")` (validate/activate); both mounted under
    `/api/v1`.
  - `backend/app/api/schemas/account.py` — Pydantic v2 DTOs (camelCase):
    - `AccountCreateRequest { firstName: str, surname: str, email: EmailStr, accountType: AccountType }`
      (mandatory: firstName, surname, email — SR-032.2)
    - `AccountResponse { id, firstName, surname, email, accountType, status }` (status ∈
      `INACTIVE|ACTIVE|DEACTIVATED`); non-clinical projection only (SR-009)
    - `AccountListResponse { items: list[AccountResponse], nextCursor: str | None }` (paginated,
      access-scoped per api-design.md Conventions)
    - `ActivationTokenStatus { valid: bool, email: EmailStr }`
    - `ActivationRequest { password: str, confirmPassword: str }`
- `POST /accounts` (admin/sysadmin only): authorize `account:create`; `AccountService.create`
  enforces creator-role → allowed-types (admin personnel may create Patient/Doctor/Administrative
  Personnel **only**, never System Administrator — SR-032.4; sysadmin may create all — SR-032.5),
  mandatory fields (SR-032.2), unique email across active/inactive/deleted (DB unique constraint +
  app check, SR-032.3), and creates the account **INACTIVE** (SR-032.6). Creation triggers the
  activation email via the worker (SR-033.1, enqueued in TASK-031/032). 201 `AccountResponse`. Audit
  records creator id, new email + type, timestamp (SR-032.7).
- `GET /accounts` / `GET /accounts/{id}` (admin/sysadmin): authorize `account:list` / `account:read`;
  return the non-clinical projection (SR-009); `GET /accounts/{id}` for an absent/invisible id → 404.
- `POST /accounts/{id}/resend-activation` (admin/sysadmin): generate a **new single-use** link,
  invalidate any prior link for that account (SR-033.7); 202; audit the resend (SR-033.9).
- `GET /activation/{token}` (no session): validate the token (single-use, ≤72 h, SR-033.2) → 200
  `ActivationTokenStatus`; expired/used/unknown → 404 `/errors/not-found` (no enumeration).
- `POST /activation/{token}` (no session): require `password == confirmPassword` (SR-033.4); run the
  full SR-025 policy (all four classes, 12-char min, history/age established at first set);
  `AccountService.activate(token, password)` transitions INACTIVE → ACTIVE and invalidates the link
  (SR-033.5). 204. Audit `ACTIVATION_COMPLETED` (SR-033.9).
- Error cases (RFC 7807, base `https://medhub.example/errors/`): missing mandatory field →
  `400 /errors/validation-error`; duplicate email → `409 /errors/conflict` (SR-032.3); admin
  attempting to create a System Administrator → `403 /errors/forbidden` (SR-032.4); unauthorized
  caller → `403`; expired/used/unknown token → `404 /errors/not-found`; password mismatch or policy
  violation at activation → `400 /errors/validation-error` (generic on mismatch, SR-033.4).

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/api/test_accounts_router.py`):
  - admin creates a Doctor with all mandatory fields → 201, account INACTIVE, activation enqueued
    (SR-032.2/6, SR-033.1).
  - missing firstName/surname/email → 400 validation-error, nothing persisted (SR-032.2).
  - duplicate email (active, inactive, or previously deleted) → 409 conflict (SR-032.3).
  - admin personnel creating a System Administrator → 403; sysadmin creating any type → 201
    (SR-032.4/5).
  - unauthenticated `POST /accounts` → 401 (no self-registration, SR-032.1).
  - `GET /accounts` returns the non-clinical projection only, paginated and access-scoped (SR-009).
  - creation audited with creator id, new email+type, timestamp (SR-032.7).
- Unit (`backend/tests/api/test_activation_router.py`):
  - valid token → `GET` 200 `{valid:true}`; expired/used/unknown → 404 (SR-033.2).
  - `POST` with matching, policy-compliant password → 204, account ACTIVE, link invalidated; reusing
    the link → 404 (SR-033.5).
  - mismatched password/confirm → 400 generic; policy violation → 400 with per-rule `errors[]`
    (SR-033.4, SR-025).
  - resend invalidates the prior link and issues a new one (SR-033.7).
- Integration (`backend/tests/api/test_account_activation_integration.py`): create → activation
  email enqueued → activate → the account can now authenticate (cross-check with TASK-060).

## Acceptance criteria

- [x] Only an admin/sysadmin session can create accounts; no self-registration (SR-032.1).
- [x] firstName, surname, email are mandatory; missing → rejected (SR-032.2).
- [x] Email is unique across active/inactive/deleted; duplicate → 409 (SR-032.3).
- [x] Creator role constrains allowed account types server-side (SR-032.4/5).
- [x] New accounts are created INACTIVE and cannot log in until activated (SR-032.6, SR-033.8).
- [x] Activation token validates ≤72 h, single-use; expired/used → rejected (SR-033.2/5).
- [x] Activation requires password ×2 match and full SR-025 policy; success activates the account (SR-033.3/4/5).
- [x] Resend issues a new single-use link and invalidates the prior one (SR-033.7).
- [x] `GET /accounts*` returns the non-clinical projection (SR-009); creation/activation audited (SR-032.7, SR-033.9).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit + integration tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (six endpoints + DTOs)
- [x] Audit events emitted for security-relevant actions (account create, activation, resend — SR-023)
- [x] Traceability matrix row updated (SR-032, SR-033 → TASK-061 → tests)
- [x] Security review N/A (authz/identity services consumed, not implemented here; password policy in TASK-020/060)

## Audit verdict (2026-06-29)

- **Verdict:** FAIL (CSRF enforcement missing — resolved by TASK-069a)
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-069a completed. All AC/DoD items now satisfied.

## QA sign-off

- **Date:** 2026-06-30
- **Reviewer:** QA Engineer agent (phase-4 audit remediation)
- **Evidence:** CSRF gap closed by TASK-069a (CsrfEnforcementMiddleware); OpenAPI regenerated with security annotations in TASK-068a; 484 tests pass (ruff + mypy clean).
