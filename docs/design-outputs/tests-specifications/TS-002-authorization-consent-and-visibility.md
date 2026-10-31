---
id: TS-002
type: test-specification
title: Authorization, consent and visibility verification
status: approved
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-31"
links:
  - target: SR-005
    relation: verifies
  - target: SR-006
    relation: verifies
  - target: SR-007
    relation: verifies
  - target: SR-008
    relation: verifies
  - target: SR-009
    relation: verifies
  - target: SR-011
    relation: verifies
  - target: SR-015
    relation: verifies
  - target: SR-036
    relation: verifies
tags:
  - level:unit
  - class:B
---

# TS-002 — Authorization, consent and visibility verification

## Scope

Software requirements covered: SR-005, SR-006, SR-007, SR-008, SR-009, SR-011, SR-036; TC-002.7 also SR-015 (module access decision).
Software items under test: SI-AUTHZ, SI-API, SI-FE-CORE.
Levels: unit, integration.

## Preconditions and environment

Build: branch `doc/agentic-os-migration`, commit `40401a1`. Backend Python 3.12 with the
dependencies locked in `backend/uv.lock`; frontend Node 24 LTS (build stage node:24.22.2-trixie-slim; CI node-version 24) with `frontend/package-lock.json`.
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
| TC-002.7 | SR-005 AC 1, AC 3, SR-011 AC 4, SR-015 | `backend/tests/authz/test_decision_table.py` (38 cases: list scope 4 roles, denied list 1; single read 12 role x relation, 1 consent, 4 missing; module access 4 roles x 4 membership states, with the 403 message asserted), `backend/tests/authz/test_authorization_service.py` (`appointment_scope`, `module:access`), `backend/tests/authz/test_appointment_visibility.py`, `backend/tests/api/test_appointments_router.py::TestGetAppointment` | The appointment list scope, single-appointment visibility and module access are decided only in `AuthorizationService`; the decision table was run green against the code before the logic moved (characterisation, RISK-004 control) and stays green, unchanged, after; a not-visible appointment is answered 404 | Same allow/deny and status code per case before and after the move; weakening the visibility rule or the list scope makes the table fail |
| TC-002.8 | SR-005 AC 1, AC 3, SR-008, SR-009 | `backend/tests/authz/test_decision_table.py` (router rules: 6 routes x 4 roles = 24 cases, 6 no-role cases; `test_router_check_by_role`, `test_router_check_denies_actor_with_no_known_role`), `backend/tests/authz/test_no_role_decisions_outside_authz.py` (static check: comparisons, aliases, subscripts, `.get`, method calls on a role; exact-expression exceptions), `backend/tests/auth/test_lockout.py` (`admin_unlock` holds no role check), `backend/tests/api/test_admin_projection_integration.py` | The account unlock, module list, consent grant/revoke/list and patient roster rules are decided in `AuthorizationService` (status and `detail` unchanged, table written green before the move); no role comparison decides access outside `backend/app/authz/`; the admin projection is unchanged (SR-009) | Same status and message per case before and after; a comparison added outside `app/authz/` makes the static check fail; weakening a moved rule makes the table fail |

## Acceptance criteria (class B unit level, §5.5.3)

- Every acceptance criterion of the seven SRs maps to a case.
- Data and control flow: each decision input (user type, relationship, consent, module) is varied independently.
- Boundary: consent revoked during an active session takes effect on the next request.

## Notes

Route-level role guards are missing in the frontend (PRB-014, TASK-142), so client-side defense in depth is not yet verifiable.

## Version history

- 1.2 (2026-10-31) — TASK-187: TC-002.7 added (decision table of the appointment list scope, appointment visibility and module access; characterisation before and after the move); `verifies` SR-015 added. Returned to `in_review`; approval record cleared.
- 1.2 (2026-10-31) — QA review (TASK-187 round 2): approved (`in_review → approved`).
- 1.3 (2026-10-31) — TASK-189: TC-002.8 added (router rules in the decision table, static check against role comparisons outside `app/authz/`). Returned to `in_review`.
- 1.3 (2026-10-31) — TASK-189 round 2: TC-002.8 static check strengthened (alias tracking, exact-expression exceptions); `LockoutService.admin_unlock` no longer re-decides the unlock rule.
- 1.3 (2026-10-31) — QA review (TASK-189 round 2): approved (`in_review → approved`).
