---
id: TS-002
type: test-specification
title: Authorization, consent and visibility verification
status: approved
version: "1.7"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-07"
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
| TC-002.9 | SR-005, SR-009 (defence in depth; server remains the control); SR-010 AC 4 and SR-011 AC 3 (administrative personnel keep the appointments page) | `frontend/src/app/App.test.tsx` (route x role matrix of 8 routes x 4 roles = 32 deep-link cases driven by a hard-coded expected matrix, and `routeRoles` asserted equal to it; unknown path; unauthenticated to login; `me` loading; `me` failing with 403; a `/me` failing with 500 is requested exactly 4 times (1 plus 3 retries) and shows an alert; 500 then 200 recovers through "Try again"; a 401 is requested once and goes to login; a failed background refetch of a loaded `/me` keeps the page mounted with no alert, PRB-067), `frontend/src/api/queryClient.test.tsx` (`["me"]` does not retry on mount; `["me","consents"]` still does), `frontend/src/app/RequireRole.test.tsx` (allowed, PATIENT/DOCTOR denied at `/admin/accounts`, loading, failing, unknown role), `frontend/src/core/nav/routeRoles.test.ts` (compiler-API scan of every `<Route>` in the production sources under `frontend/src`: string-literal path, in the table, `element={guarded("<same path>", ...)}` in either attribute order; no `useRoutes`, `createBrowserRouter`, `createMemoryRouter`, `createHashRouter` or `createRoutesFromElements`; nav roles equal the table; fails on a renamed or namespaced `react-router-dom` import; fixtures for the element-first, expression-path, wrong-guard, exempt-path, renamed-import and namespace-import shapes) | A role not listed for a route is redirected to `/profile`, the page never mounts and fires no query; nothing mounts while `me` loads or after it fails; a failing `/me` is retried a bounded number of times, not in a loop, and shows a retry alert instead of a blank screen; an unauthenticated deep link goes to login; a `<Route>` declared in JSX without a literal path, a table entry or the guard fails a test | Removing the guard from one route, adding or dropping a role in the table, adding an unguarded or expression-path route, removing the `["me"]` `retryOnMount: false` default, restoring `retry: false` or removing the alert in `RequireAuth`, and removing the consents override each fail a test. Routes declared by other means than JSX `<Route>` are rejected, not scanned |

## Acceptance criteria (class B unit level, §5.5.3)

- Every acceptance criterion of the seven SRs maps to a case.
- Data and control flow: each decision input (user type, relationship, consent, module) is varied independently.
- Boundary: consent revoked during an active session takes effect on the next request.

## Notes

Client-side route guards (PRB-014, TASK-142) are defence in depth under SR-005 and SR-009 (CR-004 Q-4: no AC added to SR-005); TC-002.9 verifies them. The server-side cases above stay the evidence of the control.

## Version history

- 1.2 (2026-10-31) — TASK-187: TC-002.7 added (decision table of the appointment list scope, appointment visibility and module access; characterisation before and after the move); `verifies` SR-015 added. Returned to `in_review`; approval record cleared.
- 1.2 (2026-10-31) — QA review (TASK-187 round 2): approved (`in_review → approved`).
- 1.3 (2026-10-31) — TASK-189: TC-002.8 added (router rules in the decision table, static check against role comparisons outside `app/authz/`). Returned to `in_review`.
- 1.3 (2026-10-31) — TASK-189 round 2: TC-002.8 static check strengthened (alias tracking, exact-expression exceptions); `LockoutService.admin_unlock` no longer re-decides the unlock rule.
- 1.3 (2026-10-31) — QA review (TASK-189 round 2): approved (`in_review → approved`).
- 1.4 (2026-11-02) — TASK-142: TC-002.9 added (frontend route-level role guards, defence in depth); Notes updated. Returned to `in_review`.
- 1.5 (2026-11-06) — TASK-142 round 2: TC-002.9 rewritten (hard-coded expected matrix, `/appointments` open to all four roles, compiler-API route scan, bounded `/me` requests for PRB-067). Stays `in_review`.
- 1.6 (2026-11-07) — TASK-142 round 3: TC-002.9 extended (`RequireAuth` retry policy and retry alert, consents default, renamed-import scan). Stays `in_review`.
- 1.7 (2026-11-07) — TASK-142 R3-1: TC-002.9 covers a failed background refetch of a loaded `/me`. Stays `in_review`.
- 1.7 (2026-11-07) — QA review (TASK-142, R3-1 check, CR-004 D-15): approved (`in_review → approved`).
