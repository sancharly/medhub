---
id: TS-008
type: test-specification
title: Persistence, FHIR-aligned model and encryption verification
status: approved
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-30"
links:
  - target: SR-021
    relation: verifies
  - target: SR-022
    relation: verifies
  - target: SR-031
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-008 — Persistence, FHIR-aligned model and encryption verification

## Scope

Software requirements covered: SR-021, SR-022, SR-031.
Software items under test: SI-PERSIST; for TC-008.6, SI-OBJSTORE unit `U-OBJ-Init` (ADD-025); for TC-008.7, the migration tooling `backend/scripts/migrate_object_store.py` and `infra/migration/compose.minio-legacy.yml`.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24) with `frontend/package-lock.json`.
Unit and service tests run with no external services (SQLite/in-memory for model tests; real DB for constraints and migrations). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-008.1 | SR-021 | `backend/tests/db/test_fhir_mapping.py`, `backend/tests/db/test_models.py` *(real DB)* | The model maps to the documented FHIR R4 resources | Every mapped field asserted against `fhir-mapping.md` |
| TC-008.2 | SR-022 | `backend/tests/db/test_crypto.py` | Encrypted fields round-trip and are unreadable without the key | Ciphertext differs from plaintext; tampering fails authentication |
| TC-008.3 | SR-031 | `backend/tests/db/test_no_raw_sql.py`, `backend/tests/db/test_repositories.py` *(real DB)* | Repositories use parameterized queries only; SQL metacharacters are inert | A metacharacter payload is stored and returned as data |
| TC-008.4 | SR-003, SR-010 | `backend/tests/db/test_constraints.py`, `backend/tests/db/test_migration.py` *(real DB)* | Database constraints and migrations apply cleanly to an empty database | Migration runs forward without error |
| TC-008.5 | SR-022 | `backend/tests/db/test_crypto_known_answer.py` | A field value encrypted under cryptography 49.0.0 decrypts to its original plaintext under the locked version, and the locked version produces the identical envelope for the same key and nonce | Both assertions pass; a tampered tag raises `InvalidTag` |
| TC-008.6 | SR-022 (AC 4) | Unit: `backend/tests/core/test_object_store_init.py` (`cd backend && uv run pytest tests/core/test_object_store_init.py -v`). Started stack: manual, steps in TASK-175 Verification | The bucket initialiser sets `AES256` as the bucket's default encryption and reads it back; any other read-back fails it. In the started stack, `get_bucket_encryption` returns an `AES256` rule and a plain `put_object` with no server-side-encryption request is reported `ServerSideEncryption: AES256` by `head_object` | Unit: all tests pass. Started stack: both reads return `AES256`, recorded in TASK-175 "Verification results" |
| TC-008.7 | SR-022, SR-013 (AC-5) | Unit: `backend/tests/scripts/test_migrate_object_store.py` (`cd backend && uv run pytest tests/scripts/test_migrate_object_store.py -v`); `infra/tests/test_compose_minio_legacy.py` (`python3 -m unittest discover -s infra/tests`). Rehearsal: manual, on restored copies following `infra/DEPLOY.md` "Migrating from MinIO", steps and counts in TASK-178 "Rehearsal record" and "Round 2" | The migration copies every attachment object from the legacy store to the new one with `ServerSideEncryption=AES256`, comparing SHA-256 with the recorded checksum before and after the write; it reports copied, already-present, missing and mismatched counts and the orphans, exits non-zero on any missing or mismatched object or when the database has no attachment rows while the source holds objects, prints attachment ids and key hashes but never storage keys, requests `AES256` on every write (botocore Stubber tests of the S3 adapter), and a re-run copies nothing. In the rehearsal on restored copies: an object written through the legacy path before the change downloads through the API with the same bytes and passes the checksum check, and a search of the new store's volume for a plaintext marker finds nothing | Unit: all tests pass, and each fails when its comparison is removed. Rehearsal: counts as recorded (3 copied, then 3 already present), 3 of 3 API downloads match, 0 marker hits, source volume tree hash identical before and after, legacy MinIO run only on a copy |

## Acceptance criteria (class B unit level, §5.5.3)

- Boundary: encryption of empty and maximum-length values.
- Fault handling: a decryption failure raises rather than returning partial plaintext.
- Resource allocation: migrations do not lock tables longer than the deploy window.

## Notes

Four of these cases need Docker and were **blocked** in TR-001. The ciphertext envelope carries no key identifier (PRB-004), so key rotation is specified nowhere and untested.

TC-008.5 uses a fixed envelope that was produced under cryptography 49.0.0 (CR-003 AC-9), before the lock moved to 50.0.2, with the key, nonce and plaintext committed as test data. It needs no Docker. It is the §7.4.3 evidence that field values already at rest stay readable across the upgrade.
