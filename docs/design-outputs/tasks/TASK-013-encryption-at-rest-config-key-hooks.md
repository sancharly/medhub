---
id: "TASK-013"
type: task
title: "Encryption-at-rest config + key hooks"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-022"
    relation: implements
  - target: "TASK-011"
    relation: relates_to
tags: ["phase:1-persistence-audit"]
---

- **Phase:** 1 — Persistence & audit
- **Software item / unit:** SI-PERSIST / U-PER-Crypto
- **Implements:** SR-022
- **Depends on:** TASK-011 (must be merged first)
- **Branch:** `feature/persist-crypto-at-rest`
- **Status:** Completed

## Objective

Establish the at-rest encryption configuration and key-management hooks for personal and health data (SR-022.2/3). The primary control is infrastructure-level (encrypted Postgres volume + MinIO SSE-AES256 from TASK-004); this task wires the operator-managed key configuration into the application and provides a column-level encryption hook (pgcrypto / app-side) for any field requiring encryption beyond volume-level protection, so keys are managed such that data is not recoverable without authorized key access.

## Interfaces to honor

- Extends `SI-PERSIST` with a crypto configuration/hook surface consumed by repositories (TASK-012) where field-level encryption is applied; does not change repository public signatures.
- Consumes the `at_rest_encryption_key` (`SecretStr`) and object-store key config from `Settings`/§8.11 (TASK-003) — keys are env-injected, operator-managed, never committed (NFR-007, 07-deployment-view).
- Must **not** weaken or replace the infrastructure controls from TASK-004 (encrypted volume, MinIO SSE); must **not** log, expose, or persist key material; must **not** invent a bespoke cipher — use a recognized algorithm (AES-256) per SR-022.2.

## Implementation detail

- Files to create / modify under `backend/app/db/`:
  - `crypto.py` — key-access hook: `get_data_key()` reads the operator-managed key from `Settings` (`SecretStr`), plus a thin `encrypt(value)`/`decrypt(value)` helper over a recognized AES-256 primitive (e.g. `cryptography` Fernet/AES-GCM) for app-side field encryption. Centralizes algorithm choice and key sourcing.
  - `types.py` — an `EncryptedString` SQLAlchemy `TypeDecorator` (transparent encrypt-on-write / decrypt-on-read) available for columns that need field-level encryption beyond volume encryption. Applied selectively; document which columns (if any) use it.
  - Migration note: if pgcrypto is chosen for any column, add a follow-on Alembic migration enabling the `pgcrypto` extension (kept consistent with TASK-011).
  - Update `infra/DEPLOY.md` (TASK-004) and `infra/.env.example` (TASK-003) documenting: encrypted Postgres volume requirement, MinIO SSE-AES256, and the operator-supplied `at_rest_encryption_key` (rotation is an operator procedure).
- Libraries (exact stack): `cryptography` (AES-256) and/or PostgreSQL `pgcrypto`; MinIO SSE (S3) configured in infra.
- Config keys: `at_rest_encryption_key`, `object_store_*` (from TASK-003).
- Error cases: missing/invalid key → fail fast at startup (no plaintext-fallback path); decrypt failure raises rather than returning partial/plaintext data.

## Tests (write first — TDD, CLAUDE.md §4)

- `backend/tests/db/test_crypto.py`:
  - Round-trip: `encrypt` then `decrypt` returns the original; ciphertext differs from plaintext and is not readable without the key (SR-022.2/3).
  - With a wrong/absent key, decryption fails (no silent plaintext fallback) — verifies "not recoverable without authorized key access" (SR-022.3).
  - `EncryptedString` column stores ciphertext at rest (raw DB value is not the plaintext) and returns plaintext on read.
  - Key material is never logged or included in `repr` (`SecretStr` masking, consistent with TASK-003).
- Infrastructure controls (encrypted volume, MinIO SSE) are verified by the TASK-004 bring-up checks; this task references them for SR-022 coverage rather than re-testing infra.

## Acceptance criteria

Distilled from SR-022 (at-rest portions; transit covered by TASK-004):

- [x] Personal/health data at rest is protected by a recognized algorithm (AES-256): encrypted Postgres volume + MinIO SSE (infra, TASK-004) and an app-side field-encryption hook available where needed (SR-022.2).
- [x] Encryption keys are operator-managed, env-injected, never committed; data is not recoverable without authorized key access (SR-022.3, NFR-007, §8.11).
- [x] Missing/invalid key fails fast; there is no plaintext fallback path.
- [x] Key material is never logged, serialized, or persisted.
- [x] Algorithm and key-sourcing choices are centralized in one module.

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (N/A)
- [x] Audit events emitted for security-relevant actions (N/A — config/hook layer)
- [x] Traceability matrix row updated (SR-022 → TASK-013 → crypto tests + TASK-004 infra checks)
- [x] Security review completed (crypto config noted for the system-test security review; algorithm/key handling reviewed)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** AUDIT-FINDINGS.md (field-level PHI / key versioning). Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.

## QA remediation sign-off (2026-06-30)

- **Verdict:** PASS
- `ClinicalEntry.description` confirmed using `EncryptedString()` (not `Text()`); import is from `app.db.types`.
- Migration `0005_clinical_entry_description_encrypted.py` alters the column from `Text` to `String` in `upgrade()` and reverses it in `downgrade()`. Properly chained: `down_revision = "0004"`.
- `backend/app/db/crypto.py` uses AES-256-GCM (`cryptography.hazmat.primitives.ciphers.aead.AESGCM`); key sourced exclusively from `Settings.at_rest_encryption_key` (a `SecretStr`); fails fast on missing/wrong-length key; nonce is 96-bit random per encrypt call.
- DECISION docstring in `crypto.py` names `ClinicalEntry.description` as the only encrypted column with rationale.
- `EncryptedString` TypeDecorator in `types.py` sets `cache_ok = False` (correct for key-rotation safety).
- `test_crypto.py` covers: round-trip, ciphertext differs from plaintext, wrong key raises, `EncryptedString` stores ciphertext in DB, `SecretStr` not in repr.
- All acceptance criteria and DoD items verified met.
