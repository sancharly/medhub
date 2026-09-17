---
id: "TS-006"
type: test-specification
title: "Appointments and notification verification"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links:
  - target: "SR-010"
    relation: verifies
  - target: "SR-035"
    relation: verifies
tags: ["level:unit", "class:B"]
---

# TS-006 — Appointments and notification verification

## Scope

Software requirements covered: SR-010, SR-035.
Software items under test: SI-APPT, SI-WORKER, SI-FE-CORE.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 20 with `frontend/package-lock.json`.
Unit and service tests run with no external services (in-memory repositories and a fake mailer; Celery in eager mode). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: [ADD-004](../architecture/ADD-004-soup-list.md).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-006.1 | SR-010 | `backend/tests/appointments/test_appointment_create.py`, `backend/tests/api/test_appointments_router.py` | Appointments validate their references and datetime | Past datetimes and unknown participants rejected |
| TC-006.2 | SR-035 | `backend/tests/appointments/test_appointment_state.py`, `backend/tests/appointments/test_state_table.py` | Only the patient confirms or declines; transitions follow the state table | Every illegal transition rejected |
| TC-006.3 | SR-035 | `backend/tests/appointments/test_notify.py`, `backend/tests/workers/test_email_tasks.py` | In-app and email notifications are dispatched on the relevant transitions | Both channels asserted; failures are logged |
| TC-006.4 | SR-011, SR-035 | `frontend/src/core/appointments/AppointmentsPage.test.tsx` | The patient sees the appointment and can confirm or decline | Confirm and decline both asserted |

## Acceptance criteria (class B unit level, §5.5.3)

- Fault handling: an unavailable broker must log and surface the failure (currently PRB-013).
- Boundary: confirmation of an already declined appointment is refused.

## Notes

Delivery is best effort by design (no proof of delivery at MVP), so TC-006.3 verifies dispatch, not receipt.
