---
id: "TASK-123"
type: task
title: "Doctor patient-roster endpoint (remediation)"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-006"
    relation: implements
  - target: "TASK-044"
    relation: relates_to
  - target: "TASK-066"
    relation: relates_to
  - target: "TASK-091"
    relation: relates_to
  - target: "TASK-092"
    relation: relates_to
  - target: "TASK-028"
    relation: relates_to
tags: ["phase:3-domain-services-api-surface", "remediation-of:TASK-044", "original-id:TASK-044a"]
---

- **Phase:** 3 — Domain services (+ API surface in phase 4)
- **Implements / restores:** SR-006 (a doctor lists the patients they are authorized for); remediates
  TASK-044, TASK-066, and unblocks frontend TASK-091/092
- **Depends on:** TASK-044, TASK-028 (consent)
- **Branch:** `feature/doctor-patient-roster`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-044/091 verdict **FAIL**; `SMOKE-RESULTS.md` F2

*Originally filed as TASK-044a.*

## Objective

The frontend doctor landing page calls `GET /clinical-entries/patients`, which **returns 404** — no
such endpoint or service method exists anywhere. Doctors therefore cannot list their patients or reach
clinical entries. Implement the missing roster: the distinct patients a doctor currently has access to
(active consent — MANUAL or APPOINTMENT-linked).

## Implementation detail

- Add `ClinicalDataService.list_accessible_patients(doctor_id)` (or `ConsentService` query) returning
  distinct patients with an active `ConsentGrant` for the doctor. ORM-only, authz-scoped.
- Add `GET /clinical-entries/patients` (path the frontend already calls) — or align both sides on a
  single agreed path — returning `PatientSummary[]` (id, name, surname, dob as permitted). Deny-by-default;
  doctor-only.
- Audit the access (`CLINICAL_ACCESS` or a roster-specific action) including the authorization basis.

## Acceptance criteria

- [x] A doctor receives exactly the patients they have active consent for; no others (SR-006 AC-2).
- [x] A doctor with no consents receives an empty list (not 404/500).
- [x] Non-doctor roles are denied (problem+json).
- [x] The frontend `listPatients()` path resolves (no 404) and the patient list renders end-to-end.
- [x] Access is audited with the authorization basis (SR-006 AC-4).

## Definition of Done

- [x] Lint + type-check pass
- [x] Unit + integration tests pass (consent/no-consent/denied)
- [x] OpenAPI regenerated + frontend types regenerated; the frontend view loads against the real backend
- [x] Traceability row updated (SR-006 → TASK-044a → tests)
- [x] Security review completed

## QA sign-off

- **Date:** 2026-06-29
- **Reviewer:** QA Engineer agent
- **Evidence:** All non-deferred acceptance criteria and DoD items confirmed with code and tooling evidence: `ConsentRepository.list_patients_for_doctor` filters on `ConsentGrant.active.is_(True)` and `ConsentGrant.doctor_id`; `list_accessible_patients` calls `audit_svc.record`; router denies non-DOCTOR roles with `AuthorizationError`; `client.ts` `listPatients()` calls `/clinical-entries/patients` matching the registered backend path `/api/v1/clinical-entries/patients`; `openapi.json` contains the GET operation and `PatientSummaryResponse` schema; `types.ts` exports `PatientSummary` aliased to that schema; ruff + black exit 0; 9/9 pytest tests pass; `npm run typecheck` exits 0.

## Security review (2026-07-01)

The two DoD items left open by the 2026-06-29 QA pass are now closed:

- **Traceability row**: added to `docs/design/traceability-matrix.md` under "Phase-7 frontend core task → test traceability" (SR-006 → TASK-044a → backend test files).
- **Security review**: prior test coverage exercised deny-by-default (403 for PATIENT/ADMIN, 401 unauthenticated in `test_clinical_router.py`) but only via a **mocked** `list_accessible_patients` — no test exercised the real consent-scoping query against a database, which is exactly the "recurring root cause" (mock-only evidence) the phase-audit calls out. Closed the gap:
  - Added `test_list_patients_for_doctor_excludes_patients_without_consent` (`backend/tests/db/test_repositories.py`) — a real-DB integration test asserting `ConsentRepository.list_patients_for_doctor` returns a patient with an active grant for the doctor, and excludes both a patient with no grant and a patient consented to a *different* doctor (SR-006 AC-2/AC-3).
  - Added `test_list_accessible_patients_emits_audit_with_basis` (`backend/tests/clinical/test_clinical_service.py`) — asserts the roster access audit record carries the `CLINICAL_ACCESS` action and the doctor's id (SR-006 AC-4).
  - Confirmed the endpoint is deny-by-default (doctor-only, 403 otherwise) at the router level (pre-existing tests, re-verified passing).
  - Full backend suite re-run green after the additions.
