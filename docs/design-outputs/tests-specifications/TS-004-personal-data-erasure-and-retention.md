---
id: TS-004
type: test-specification
title: Personal data erasure and retention verification
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 7793e8ee7f3dcf5e545ff8db0b5f86c2d04756e1a6e39f7a4c48a3594f255ee3
approval_note: self-approved
links:
  - target: SR-024
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-004 — Personal data erasure and retention verification

## Scope

Software requirements covered: SR-024.
Software items under test: SI-IDENTITY, SI-WORKER, SI-PERSIST.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 20 with `frontend/package-lock.json`.
Unit and service tests run with no external services (in-memory repositories; frozen clock for deadlines). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-004.1 | SR-024 | `backend/tests/identity/test_erasure.py` | Deletion anonymizes the account and re-keys clinical data into the anonymized dataset | No identifying field survives; clinical rows are not dropped |
| TC-004.2 | SR-024 | `backend/tests/api/test_anonymized_retrieve.py` | Retrieval with the correct code works before the deadline and is refused after it | Only the salted hash of the code is stored |
| TC-004.3 | SR-024 | `backend/tests/workers/test_retention_erase.py` | The scheduled job erases datasets past the five-year deadline | Erasure recorded; datasets before the deadline untouched |

## Acceptance criteria (class B unit level, §5.5.3)

- Boundary: retrieval exactly at the deadline, one second before and one second after.
- Fault handling: a failure mid-sweep must not leave a partially erased dataset or leak a session.

## Notes

PRB-012 (session leak and missing retry in the sweep) and TASK-116 (re-keying) are open; the re-keying criterion is therefore specified here but not yet verified.
