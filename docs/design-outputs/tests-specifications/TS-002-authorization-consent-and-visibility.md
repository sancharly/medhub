---
id: "TS-002"
type: test-specification
title: "Authorization, consent and visibility verification"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
links:
  - target: "SR-005"
    relation: verifies
  - target: "SR-006"
    relation: verifies
  - target: "SR-007"
    relation: verifies
  - target: "SR-008"
    relation: verifies
  - target: "SR-009"
    relation: verifies
  - target: "SR-011"
    relation: verifies
  - target: "SR-036"
    relation: verifies
tags: ["level:unit", "class:B"]
---

# TS-002 — Authorization, consent and visibility verification

## Scope

Software requirements covered: SR-005, SR-006, SR-007, SR-008, SR-009, SR-011, SR-036.
Software items under test: SI-AUTHZ, SI-API, SI-FE-CORE.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 20 with `frontend/package-lock.json`.
Unit and service tests run with no external services (in-memory repositories; no network). Tests marked *real DB* require a
PostgreSQL 16 container through testcontainers and therefore a working Docker daemon.
Exact SOUP versions: the `soup` records in [`../../soup/`](../../soup/).

## Test cases

| ID | Verifies | Automated test reference | Expected result | Pass criteria |
|---|---|---|---|---|
| TC-002.1 | SR-005 | `backend/tests/authz/test_authorization_service.py` | Every decision denies unless a rule grants it, including unknown actions | Negative cases outnumber positive ones; no default-allow path |
| TC-002.2 | SR-006, SR-007 | `backend/tests/clinical/test_clinical_service.py`, `backend/tests/api/test_clinical_router.py` | A doctor reads only their own patients; a patient reads only their own data | Cross-tenant reads return 403/404, never data |
| TC-002.3 | SR-008, SR-036 | `backend/tests/authz/test_consent_service.py`, `backend/tests/appointments/test_consent_link.py`, `backend/tests/api/test_consents_router.py` | Grant and revoke take effect immediately; per-source union computed for cases A/B/C | Revocation of one source leaves other grants intact |
| TC-002.4 | SR-009 | `backend/tests/authz/test_admin_projection.py`, `backend/tests/api/test_admin_projection_integration.py` | Administrative personnel receive non-clinical fields only | Clinical fields absent from the response payload |
| TC-002.5 | SR-011 | `backend/tests/authz/test_appointment_visibility.py` | Appointments are visible only to their participants and authorized administrative personnel | Each role asserted separately |
| TC-002.6 | SR-007, SR-008 | `frontend/src/core/consent/ConsentPage.test.tsx`, `frontend/src/core/clinical/ClinicalEntriesPage.test.tsx`, `frontend/src/core/patients/PatientListPage.test.tsx` | The UI shows only permitted data and reflects consent changes | Rendering asserted per role |

## Acceptance criteria (class B unit level, §5.5.3)

- Every acceptance criterion of the seven SRs maps to a case.
- Data and control flow: each decision input (user type, relationship, consent, module) is varied independently.
- Boundary: consent revoked during an active session takes effect on the next request.

## Notes

Route-level role guards are missing in the frontend (PRB-014, TASK-142), so client-side defense in depth is not yet verifiable.
