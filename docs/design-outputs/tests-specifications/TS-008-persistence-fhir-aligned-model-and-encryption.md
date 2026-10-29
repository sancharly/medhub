---
id: TS-008
type: test-specification
title: Persistence, FHIR-aligned model and encryption verification
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-29"
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
Software items under test: SI-PERSIST.
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

## Acceptance criteria (class B unit level, §5.5.3)

- Boundary: encryption of empty and maximum-length values.
- Fault handling: a decryption failure raises rather than returning partial plaintext.
- Resource allocation: migrations do not lock tables longer than the deploy window.

## Notes

Four of these cases need Docker and were **blocked** in TR-001. The ciphertext envelope carries no key identifier (PRB-004), so key rotation is specified nowhere and untested.

TC-008.5 uses a fixed envelope that was produced under cryptography 49.0.0 (CR-003 AC-9), before the lock moved to 50.0.2, with the key, nonce and plaintext committed as test data. It needs no Docker. It is the §7.4.3 evidence that field values already at rest stay readable across the upgrade.
