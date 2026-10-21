---
id: "TS-013"
type: test-specification
title: "Lifecycle record and traceability verification"
status: obsolete
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
links:
  - target: "SR-028"
    relation: verifies
tags: ["level:review", "class:B"]
---

> **Obsolete (2026-10-21).** It verified only SR-028, which is now the regulatory requirement
> RR-011. That obligation is evidenced by the `traceability-check` gap reports and the release gate
> of PLAN-001, not by a test specification. Kept below because IDs are never reused.

# TS-013 — Lifecycle record and traceability verification

## Scope

Software requirements covered: SR-028.
Software items under test: the design record set (no code under test).
Levels: review.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 20 with `frontend/package-lock.json`.
Unit and service tests run with no external services (the repository itself). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-013.1 | SR-028 | `medical-records:traceability-check` over `docs/` | Zero schema, status and required-link errors | Errors = 0 in the committed gap report |
| TC-013.2 | SR-028 | `backend/tests/test_toolchain.py`, `frontend/tests/toolchain.test.ts` | The declared toolchain matches what the project actually runs | Versions asserted |
| TC-013.3 | SR-028 | `backend/tests/test_export_openapi.py` | The committed OpenAPI export matches the application | Export diff empty |
| TC-013.4 | SR-028 | `git log` on `docs/` plus the record `version` fields | Every record change is version-controlled and versioned | Reviewed at release |

## Acceptance criteria (class B unit level, §5.5.3)

- The check runs before QA approval and before release, per PLAN-001.
- Warnings are triaged, not silenced.

## Notes

This TS verifies the process requirement by review, which IEC 62304 §5.5 accepts as unit verification evidence alongside tests.
