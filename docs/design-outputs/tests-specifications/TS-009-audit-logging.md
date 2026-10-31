---
id: TS-009
type: test-specification
title: Audit logging verification
status: approved
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-30"
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

Build: branch `bug/minio-object-store`, the commit that carries TASK-183 (subject: "FIX, TEST: Commit failure audit events on their own transaction (TASK-183)"). Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24) with `frontend/package-lock.json`.
Unit and service tests run with no external services (in-memory repository). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-009.1 | SR-023 | `backend/tests/audit/test_audit_writer.py` | Every security-relevant action writes one entry with actor, action, target, outcome and timestamp | Entry asserted per action type |
| TC-009.2 | SR-023 | `backend/tests/audit/test_audit_writer.py` | Credentials and secrets never appear in an audit entry | Secret-shaped values scrubbed |
| TC-009.3 | SR-023 | `backend/tests/db/test_models.py` *(real DB)* | Audit rows persist and are not updated by the application | Insert and select asserted |
| TC-009.4 | SR-023 | `backend/tests/audit/test_failure_audit_persistence.py::test_authz_denied_persists_after_403` *(real DB)* | `AUTHZ_DENIED` (FAILURE, actor, target) is in `audit_log` after the 403, read on a separate session | Row asserted; fails if events are written back into the request transaction |
| TC-009.5 | SR-023 | `backend/tests/audit/test_failure_audit_persistence.py::test_login_failure_*` *(real DB)* | `LOGIN_FAILURE` persists after the 401 for unknown email, wrong password, inactive account and locked account; `ACCOUNT_LOCKOUT` (outcome SUCCESS) persists after the 5th wrong password | Rows asserted per branch |
| TC-009.6 | SR-023 | `backend/tests/audit/test_failure_audit_persistence.py::test_activation_failed_persists_after_401` *(real DB)* | `ACTIVATION_FAILED` persists after the 401 on a wrong token | Row asserted |
| TC-009.7 | SR-023 | `backend/modules/dicom_viewer/tests/test_failure_audit_persistence.py` *(real DB; run apart from `backend/tests`)* | `DICOM_STUDY_READ` FAILURE persists after the 403 | Row asserted |
| TC-009.8 | SR-023 | `backend/tests/audit/test_failure_audit_persistence.py::test_failure_row_persists_while_business_row_and_success_event_roll_back`, `backend/tests/audit/test_audit_writer.py` *(real DB for the first)* | A business row and a SUCCESS event added in a failing request are rolled back while its FAILURE row persists; `record` has no `durable` parameter and the repository has no session-wide commit | Business row and SUCCESS row absent, FAILURE row present |

## Acceptance criteria (class B unit level, §5.5.3)

- Self-diagnostics: an audit write failure must not silently drop the event.
- Data flow: the source address is part of the entry (currently missing for authz events, PRB-010).

## Notes

TC-007.6's persistence test (TS-007) now runs without `durable`: the FAILURE row is committed by the writer itself (ADR-0016).

Append-only is a convention, not a database grant (PRB-005); TC-009.3 therefore verifies persistence, not immutability.
