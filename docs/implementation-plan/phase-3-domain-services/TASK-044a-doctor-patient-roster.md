# TASK-044a — Doctor patient-roster endpoint (remediation)

- **Phase:** 3 — Domain services (+ API surface in phase 4)
- **Implements / restores:** SR-006 (a doctor lists the patients they are authorized for); remediates
  TASK-044, TASK-066, and unblocks frontend TASK-091/092
- **Depends on:** TASK-044, TASK-028 (consent)
- **Branch:** `feature/doctor-patient-roster`
- **Status:** Not started
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

- [ ] A doctor receives exactly the patients they have active consent for; no others (SR-006 AC-2).
- [ ] A doctor with no consents receives an empty list (not 404/500).
- [ ] Non-doctor roles are denied (problem+json).
- [ ] The frontend `listPatients()` path resolves (no 404) and the patient list renders end-to-end.
- [ ] Access is audited with the authorization basis (SR-006 AC-4).

## Definition of Done

- [ ] Lint + type-check pass
- [ ] Unit + integration tests pass (consent/no-consent/denied)
- [ ] OpenAPI regenerated + frontend types regenerated; the frontend view loads against the real backend
- [ ] Traceability row updated (SR-006 → TASK-044a → tests)
- [ ] Security review completed
