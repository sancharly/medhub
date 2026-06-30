# TASK-035 — Erasure → anonymize + retrieval code

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-IDENTITY / U-ID-Erasure
- **Implements:** SR-024 (erasure/anonymization), SR-034.5–7 (delete → anonymize, email released,
  confirm); ADR-0013
- **Depends on:** TASK-030 (AccountService), TASK-014 (AuditService), TASK-031 (email task)
- **Branch:** `feature/erasure-anonymize`
- **Status:** Completed

## Objective

Implement account deletion as an **anonymization-and-retention** operation (ADR-0013, runtime
§6.7): after the SR-034.6 confirmation, sever the user's credentials and PII from their record
data, re-key the records into an opaque **anonymized dataset** (5-year retention deadline),
release the email for reuse, and issue a single high-entropy **anonymization code** to the user by
email. The code is the user's sole handle and is **never stored** — only a salted Argon2id hash is
kept to locate-and-authorize retrieval. A scheduled worker (TASK-036) erases the dataset at 5
years. Losing the code makes the data unrecoverable by design (the intended privacy property,
ADR-0013).

## Interfaces to honor

Extends `AccountService` (from [12-interfaces.md](../../design/12-interfaces.md), SI-IDENTITY),
signatures verbatim:

```python
class AccountService:
    def delete(self, actor: Account, account_id: UUID) -> None: ...   # confirm step at the API boundary
    def erase(self, account_id: UUID) -> AnonymizedDataset: ...        # sever PII, re-key, set deadline, issue code
```

Plus the code-authorized retrieval used by `POST /anonymized-data/retrieve` (no account/session):

```python
    def retrieve_anonymized(self, code: str) -> AnonymizedDataset: ...  # match salted hash; never stores the code
```

Backs `DELETE /accounts/{id}` (SR-034.5/6, SYSADMIN, confirm step) and
`POST /anonymized-data/retrieve` (api-design.md). Consumes `PasswordService.hash`/`verify`
(TASK-020 — the KDF primitive, ADR-0013/0011), `SessionService.invalidate_all` +
`propagate_session_kill` (TASK-021/034), the email task (TASK-031), `AuditService` (TASK-014),
the persistence layer (TASK-010/011 models, TASK-013 crypto).

Must **not**: store the anonymization code in any recoverable form, in the DB, in logs, or in audit
records (ADR-0013, store only the salted KDF hash); provide any recovery/reset/admin back-channel
for a lost code (no recovery by design); leave identifiers or quasi-identifiers linking the dataset
back to the natural person (true anonymization, not pseudonymization — ADR-0013 verification
obligation); skip the confirmation step (SR-034.6) or session kill on delete (SR-034.2).

## Implementation detail

- Files to create:
  - `backend/app/identity/erasure.py` — `delete`, `erase`, `retrieve_anonymized`,
    `AnonymizedDataset` value type.
- Confirmation (SR-034.6): the API boundary (TASK-062) displays the account email + type and
  requires explicit confirmation before `delete` runs; deletion is irreversible. The service
  assumes the confirmation has been validated.
- `erase(account_id)` (ADR-0013 steps 1–4, SR-034.5/7):
  1. **Sever PII:** remove authentication credentials and personal identifying fields; re-key the
     user's clinical/record data into an `AnonymizedDataset` with an opaque id and **no**
     back-reference to the person (anonymize, do not silently erase — SR-024 AC-4, SR-034.5). After
     this, the subject's identifying data is no longer retrievable through the application
     (SR-024 AC-2).
  2. **Release email** for reuse (SR-034.7) — drop the unique-email reservation.
  3. **Generate the code:** `secrets.token_urlsafe(32)` (≥128 bits CSPRNG, ADR-0013 step 2). Send it
     to the user by email via TASK-031 at deletion time; it leaves the process only in that email.
  4. **Store only the salted hash:** `PasswordService.hash(code)` (Argon2id salted KDF, ADR-0011)
     persisted on the dataset row as the locate-and-authorize value. The raw code is never written
     anywhere (ADR-0013 step 3).
  5. **Set the 5-year retention deadline** on the dataset (`retention_deadline = now + 5y`,
     ADR-0013 step 4); the scheduled worker (TASK-036) erases it after.
  6. Kill the account's sessions (synchronous `invalidate_all` + enqueue `propagate_session_kill`,
     SR-034.2).
  7. Audit `ACCOUNT_DELETED` / `DATA_ANONYMIZED` with acting admin, affected email + type, the
     **anonymized dataset id**, ts — **never** the code (SR-024 AC-3, SR-034.8, ADR-0013).
- `retrieve_anonymized(code)` (ADR-0013 step 5, runtime §6.7): derive/verify the salted hash
  (`PasswordService.verify`) against stored dataset hashes; on match within the 5-year window,
  authorize and return the dataset; audit the retrieval (dataset id + ts, never the code). No
  account or session required (the subject is anonymous).
- Anonymization quality: enumerate and sever all back-references and quasi-identifiers in the
  re-key mapping (ADR-0013 "Negative" / verification obligation); the precise field-level mapping is
  fixed in `U-PER-Models`/`U-PER-Crypto` (TASK-010/013) and asserted by tests here.
- Error cases: invalid/lost/expired code → **generic** denial, audited (no distinction between
  wrong and never-existed, runtime §6.7); a dataset past its deadline (already erased by TASK-036)
  → `https://medhub.example/errors/not-found` (404); non-sysadmin delete → 403.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/identity/test_erasure.py`):
  - `erase` severs credentials + PII; the account's identifying data is no longer retrievable via
    the app; the record data survives re-keyed into an `AnonymizedDataset` (SR-024 AC-2, SR-034.5).
  - The email is released and can be re-registered to a new account (SR-034.7) (cross-check
    TASK-030 unique-email).
  - A code ≥128 bits is generated and emailed (assert the email task is enqueued with the code in
    the body only); the **raw code never appears** in the DB row, logs, or audit (ADR-0013) — assert
    persisted value is an `$argon2id$` hash, not the code.
  - `retrieve_anonymized` with the correct code returns the dataset and audits it (dataset id, not
    the code); a wrong/lost code → generic denial, no recovery path (ADR-0013 by-design).
  - The retention deadline is set to now + 5 years (ADR-0013 step 4).
  - Delete kills the account's sessions (inline + enqueued task) (SR-034.2).
  - Delete audited with admin, email + type, anonymized dataset id, ts; never the code (SR-024 AC-3,
    SR-034.8).
  - Anonymization completeness: no stored field on the dataset links back to the person
    (back-references/quasi-identifiers severed) (ADR-0013 verification obligation).
- Integration (`backend/tests/identity/test_erasure_flow.py`): `DELETE /accounts/{id}` after
  confirmation → anonymized dataset created, email released, retrieval code emailed; then
  `POST /anonymized-data/retrieve` with the code returns the dataset (runtime §6.7).

## Acceptance criteria

Distilled from SR-024 / SR-034.5–7 / ADR-0013:

- [ ] Authorized operator (SYSADMIN) initiates erasure after explicit confirmation (SR-024 AC-1, SR-034.6).
- [ ] After erasure, the subject's identifying data is no longer retrievable through the app (SR-024 AC-2).
- [ ] Clinical records are anonymized per the retention policy, not silently erased (SR-024 AC-4, SR-034.5).
- [ ] Email is released for reuse (SR-034.7).
- [ ] A ≥128-bit code is emailed to the user; only its salted Argon2id hash is stored; the code never
      appears in the DB, logs, or audit (ADR-0013).
- [ ] A 5-year retention deadline is set; the dataset is retrievable by the code within the window (ADR-0013).
- [ ] A lost/invalid code yields a generic denial with no recovery path (by design, ADR-0013).
- [ ] Erasure and retrieval audited with actor/dataset id/ts, never the code (SR-024 AC-3, SR-034.8).

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit (and required integration) tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (delete + retrieval endpoints in TASK-062)
- [ ] Audit events emitted for security-relevant actions (ACCOUNT_DELETED / DATA_ANONYMIZED /
      ANONYMIZED_RETRIEVAL — SR-024 AC-3; never the code)
- [ ] Traceability matrix row updated (SR-024, SR-034.5–7, ADR-0013 → TASK-035 → tests)
- [ ] Security review completed (auth/session/authz task — SR-031.6; verify no-stored-code invariant)

## Audit verdict (2026-06-29)

- **Verdict:** FAIL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** TASK-035a. Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
