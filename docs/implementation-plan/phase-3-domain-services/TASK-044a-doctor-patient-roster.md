# TASK-044a — Doctor patient-roster endpoint (remediation)

- **Phase:** 3 — Domain services (+ API surface in phase 4)
- **Implements / restores:** SR-006 (a doctor lists the patients they are authorized for); remediates
  TASK-044, TASK-066, and unblocks frontend TASK-091/092
- **Depends on:** TASK-044, TASK-028 (consent)
- **Branch:** `feature/doctor-patient-roster`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-044/091 verdict **FAIL**; `SMOKE-RESULTS.md` F2

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
- [ ] Traceability row updated (SR-006 → TASK-044a → tests)
- [ ] Security review completed

## QA sign-off

- **Date:** 2026-06-29
- **Reviewer:** QA Engineer agent
- **Evidence:** All non-deferred acceptance criteria and DoD items confirmed with code and tooling evidence: `ConsentRepository.list_patients_for_doctor` filters on `ConsentGrant.active.is_(True)` and `ConsentGrant.doctor_id`; `list_accessible_patients` calls `audit_svc.record`; router denies non-DOCTOR roles with `AuthorizationError`; `client.ts` `listPatients()` calls `/clinical-entries/patients` matching the registered backend path `/api/v1/clinical-entries/patients`; `openapi.json` contains the GET operation and `PatientSummaryResponse` schema; `types.ts` exports `PatientSummary` aliased to that schema; ruff + black exit 0; 9/9 pytest tests pass; `npm run typecheck` exits 0. Deferred items (Traceability row TASK-114, Security review) remain open.
