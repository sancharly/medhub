---
id: TS-009
type: test-specification
title: Audit logging verification
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: c0da9ec556d9bf897d0f5427386036b22700d32b9139ceade13869435e8792c7
approval_note: self-approved
links:
  - target: SR-023
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-009 — Audit logging verification

## Scope

Software requirements covered: SR-023.
Software items under test: SI-AUDIT.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 20 with `frontend/package-lock.json`.
Unit and service tests run with no external services (in-memory repository). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-009.1 | SR-023 | `backend/tests/audit/test_audit_writer.py` | Every security-relevant action writes one entry with actor, action, target, outcome and timestamp | Entry asserted per action type |
| TC-009.2 | SR-023 | `backend/tests/audit/test_audit_writer.py` | Credentials and secrets never appear in an audit entry | Secret-shaped values scrubbed |
| TC-009.3 | SR-023 | `backend/tests/db/test_models.py` *(real DB)* | Audit rows persist and are not updated by the application | Insert and select asserted |

## Acceptance criteria (class B unit level, §5.5.3)

- Self-diagnostics: an audit write failure must not silently drop the event.
- Data flow: the source address is part of the entry (currently missing for authz events, PRB-010).

## Notes

Append-only is a convention, not a database grant (PRB-005); TC-009.3 therefore verifies persistence, not immutability.
