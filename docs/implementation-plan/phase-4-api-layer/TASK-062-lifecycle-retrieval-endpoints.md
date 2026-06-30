# TASK-062 — Account lifecycle & anonymized-data retrieval endpoints

- **Phase:** 4 — API layer
- **Software item / unit:** SI-API / U-API-Routers, U-API-DTO
- **Implements:** SR-034 (deactivate/reactivate/delete, session kill ≤30 s, confirmation, email
  release); SR-024 (erasure/anonymization + code-authorized retrieval); ADR-0013 (5-year anonymized
  retention, user-held never-stored code)
- **Depends on:** TASK-033 (account lifecycle), TASK-035 (erasure/anonymize) — must be merged first
- **Branch:** `feature/lifecycle-retrieval-endpoints`
- **Status:** Completed

## Objective

Expose the account-lifecycle HTTP surface (`POST /accounts/{id}/deactivate`,
`POST /accounts/{id}/reactivate`, `DELETE /accounts/{id}`) restricted to system administrators, plus
the **code-authorized, session-less** anonymized-dataset retrieval endpoint
(`POST /anonymized-data/retrieve`). Routers delegate to `AccountService`; deactivation/deletion
trigger session kill within 30 s (SR-034.2 via SI-WORKER), deletion anonymizes into the 5-year
retained dataset and emails the user-held retrieval code (ADR-0013). Retrieval matches a presented
code against a stored **salted hash** — the code is never stored and never logged. Traces to SR-034,
SR-024, ADR-0013.

## Interfaces to honor

HTTP contract (verbatim from [api-design.md](../../specifications/api-design.md)):

| Method & path                    | Purpose                                                        | Key reqs                     |
|----------------------------------|----------------------------------------------------------------|------------------------------|
| `POST /accounts/{id}/deactivate` | deactivate (sysadmin), kills sessions ≤30 s                    | SR-034.1/2                   |
| `POST /accounts/{id}/reactivate` | reactivate, existing credentials                               | SR-034.4                     |
| `DELETE /accounts/{id}`          | delete → anonymize into retained dataset; emails retrieval code | SR-034.5/6, SR-024, ADR-0013 |
| `POST /anonymized-data/retrieve` | code-authorized retrieval of a deleted user's dataset          | SR-024, ADR-0013             |

Consumes ([12-interfaces.md](../../design/12-interfaces.md) §12.1) **verbatim**:

```python
AccountService.deactivate(self, account_id: UUID) -> None    # TASK-033 (triggers session kill)
AccountService.reactivate(self, account_id: UUID) -> None    # TASK-033
AccountService.delete(self, account_id: UUID) -> None        # TASK-033 → erase()/anonymize
AccountService.erase(self, account_id: UUID) -> AnonymizedDatasetRef  # TASK-035 (U-ID-Erasure)
# retrieval matches a presented code → locates the anonymized dataset (TASK-035)
```

Lifecycle endpoints declare the `require(action, resource_loader)` guard (TASK-025); only sysadmin
is authorized (SR-034). `POST /anonymized-data/retrieve` is **code-authorized, no account/session** —
explicitly listed as an unauthenticated route; the high-entropy code is the sole authorization
(ADR-0013). Session kill is propagated by `SI-WORKER.propagate_session_kill` (TASK-034); email
release and code email by `SI-WORKER` (TASK-031).

Must **not**: allow a sysadmin to deactivate their own account (SR-034.1); silently hard-delete
clinical records (deletion is anonymization-and-retention, SR-034.5, SR-024.4); store, log, or audit
the anonymization code in any recoverable form — only its salted KDF hash is persisted (ADR-0013,
SR-023); expose a recovery/reset path for a lost code (no back-channel by design, ADR-0013).

## Implementation detail

- Files to create:
  - `backend/app/api/routers/lifecycle.py` — `APIRouter` for the three `/accounts/{id}/...`
    operations, mounted under `/api/v1`.
  - `backend/app/api/routers/anonymized_data.py` — `APIRouter(prefix="/anonymized-data")` for
    retrieve.
  - `backend/app/api/schemas/lifecycle.py` — Pydantic v2 DTOs (camelCase):
    - `DeleteConfirmationRequest { confirmEmail: EmailStr, confirmAccountType: AccountType }`
      (the SR-034.6 explicit confirmation echoing email + type)
    - `DeletionResponse { anonymizedDatasetId: UUID, retentionDeadline: date }`
      (the code itself is **not** returned in the API body — it is emailed to the user, ADR-0013)
    - `AnonymizedRetrieveRequest { code: str }`
    - `AnonymizedRetrieveResponse { dataset: <anonymized dataset projection> }`
- `POST /accounts/{id}/deactivate` (sysadmin): authorize `account:deactivate`; reject self-target →
  403 (SR-034.1); `AccountService.deactivate` blocks auth and triggers session kill within 30 s via
  the worker (SR-034.2); retained data stays accessible (SR-034.3). 204. Audit `ACCOUNT_DEACTIVATE`
  with acting admin, target email+type, timestamp (SR-034.8).
- `POST /accounts/{id}/reactivate` (sysadmin): authorize `account:reactivate`; account can log in
  immediately with existing credentials, **no** new activation email (SR-034.4). 204. Audit.
- `DELETE /accounts/{id}` (sysadmin): authorize `account:delete`; require the
  `DeleteConfirmationRequest` body whose `confirmEmail`/`confirmAccountType` must match the target
  account (server-side check of the SR-034.6 confirmation; the UX confirmation dialog is TASK-083).
  On match: `AccountService.delete` → `erase()` severs credentials + PII, re-keys record data into an
  anonymized dataset, sets the **5-year** retention deadline, generates a ≥128-bit CSPRNG code,
  stores **only its salted KDF hash** (Argon2id), releases the email for reuse (SR-034.7), and
  enqueues the code email to the user (ADR-0013). Session kill within 30 s (SR-034.2). 200
  `DeletionResponse`. Audit `ACCOUNT_DELETE` with the **anonymized dataset id**, acting admin, target
  email+type, timestamp — **never** the code (SR-034.8, SR-024.3, ADR-0013).
- `POST /anonymized-data/retrieve` (no session): derive the same salted-hash value from the presented
  `code`, locate-and-authorize the matching anonymized dataset, verify it is within the 5-year window
  (expired/erased → 404), and return the anonymized projection. Audit `ANONYMIZED_RETRIEVE` with the
  dataset id only (SR-024.3) — never the code. Apply rate limiting against code guessing
  (`429 /errors/rate-limited`).
- Edge cases: a lost code makes the dataset unrecoverable — no recovery endpoint (ADR-0013 trade-off,
  by design). Datasets past the 5-year deadline are erased by the scheduled worker (TASK-036); a
  retrieve against an erased/expired dataset returns 404, not a distinguishing error.
- Error cases (RFC 7807, base `https://medhub.example/errors/`): self-deactivation → `403
  /errors/forbidden` (SR-034.1); confirmation mismatch on delete → `400 /errors/validation-error`;
  unauthorized caller → `403`; absent target → `404 /errors/not-found`; invalid/expired retrieval
  code → `404 /errors/not-found` (generic, no enumeration); retrieval throttling → `429
  /errors/rate-limited`.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/api/test_lifecycle_router.py`):
  - sysadmin deactivates another account → 204, auth blocked, session-kill enqueued (SR-034.2).
  - sysadmin deactivating their **own** account → 403 (SR-034.1).
  - reactivate → 204, account logs in with existing credentials, no activation email (SR-034.4).
  - `DELETE` without a matching confirmation body → 400; with matching email+type → 200, PII severed,
    anonymized dataset created with a 5-year deadline, email released, code emailed (not in body),
    session-kill enqueued (SR-034.5/6/7, ADR-0013).
  - audit for deactivate/reactivate/delete records admin + target email+type + timestamp; the delete
    audit carries the dataset id and **never** the code (SR-034.8, SR-024.3).
  - non-sysadmin caller on any lifecycle op → 403.
- Unit (`backend/tests/api/test_anonymized_retrieve.py`):
  - valid code → 200 anonymized dataset (no session required) (SR-024, ADR-0013).
  - wrong/absent code → 404 generic (no enumeration); repeated attempts → 429 (anti-guessing).
  - dataset past the 5-year deadline (erased) → 404 (SR-024.4).
  - no test path stores or logs the plaintext code (ADR-0013).
- Integration (`backend/tests/api/test_lifecycle_integration.py`): delete an account → retrieve its
  anonymized dataset with the issued code end-to-end through the test client.

## Acceptance criteria

- [x] Sysadmin can deactivate any account except their own; sessions die ≤30 s (SR-034.1/2).
- [x] Deactivated data is retained and accessible to authorized users (SR-034.3).
- [x] Reactivate restores login with existing credentials, no new activation email (SR-034.4).
- [x] Delete requires explicit email+type confirmation; anonymizes record data, severs PII, releases the email (SR-034.5/6/7).
- [x] Deletion creates a 5-year-retained anonymized dataset; only a salted hash of the code is stored; the code is emailed, never persisted/logged (ADR-0013, SR-024).
- [x] Code-authorized retrieval works without a session within 5 years; invalid/expired code → 404; guessing is rate-limited (SR-024, ADR-0013).
- [x] All lifecycle and retrieval actions audited without the code (SR-034.8, SR-024.3).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit + integration tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (four endpoints + DTOs; retrieve documented as unauthenticated)
- [x] Audit events emitted for security-relevant actions (deactivate/reactivate/delete/retrieve — SR-023, SR-024.3)
- [x] Traceability matrix row updated (SR-034, SR-024, ADR-0013 → TASK-062 → tests)
- [x] Security review N/A for the router shell — no code leakage confirmed (anonymized retrieve path stores only hash, code is never in response body or audit log); TASK-069a confirmed rate-limiting/brute-force exemption scope.

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL (CSRF gap — resolved by TASK-069a)
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-069a completed. All AC/DoD items now satisfied.

## QA sign-off

- **Date:** 2026-06-30
- **Reviewer:** QA Engineer agent (phase-4 audit remediation)
- **Evidence:** CSRF gap closed by TASK-069a; OpenAPI regenerated in TASK-068a; 484 tests pass (ruff + mypy clean).
