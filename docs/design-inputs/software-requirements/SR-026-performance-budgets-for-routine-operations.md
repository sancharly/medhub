---
id: SR-026
type: software-requirement
title: Performance budgets for routine operations
status: approved
version: "1.6"
author: Carlos Santiago Liceras
created: "2026-07-07"
updated: "2026-11-13"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-13"
approved_digest: 006224474ad88681023e6daf56e2b0aec368cbde14b733cb63c0e58cff93ed0a
approval_note: self-approved
links:
  - target: RR-010
    relation: satisfies
  - target: RISK-007
    relation: mitigates
  - target: NFR-008
    relation: derives_from
tags:
  - control:design
---

## Summary

The system shall meet defined response-time budgets for routine interactive operations and for initial DICOM image display under normal load.

## Description

This requirement implements the performance NFR with concrete, testable budgets. Routine operations complete within 3 seconds, saving a clinical entry (excluding upload time) within 3 seconds, and initial DICOM image rendering within 10 seconds for a typical study, all under normal load.

## Acceptance Criteria

1. Page navigation and data-listing operations (profile, appointments, clinical entries) complete within 3 seconds under normal load.
2. Saving a clinical entry (excluding large file upload time) completes within 3 seconds under normal load.
3. Opening a DICOM image presents an initial rendered image within 10 seconds under normal load for a typical study.
4. These budgets are verified by performance/system tests.
5. With 20 authenticated clients issuing requests at the same time (reads and writes mixed) against one API worker, no request is answered with a 5xx status and the budgets of AC 1 and AC 2 hold. A slow database or object-store call made for one request does not delay unrelated requests beyond those budgets. (20 clients, CR-006 D-3.)
6. The cost of data-access paths used by authorization and module gating does not grow with the size of the data set: validating an activation token reads at most one account row, listing a user's groups issues a constant number of queries independent of the number of memberships, and the lookups by appointment time, by consent appointment, by patient for clinical entries and for attachments, by clinical entry for attachments, and by doctor for active consents are served by an index (a query-plan check on a seeded database shows no sequential scan of those tables).
7. The initial JavaScript payload of the web application excludes the code of routes and modules that the landing route does not render; those are loaded when first navigated to. The initial JavaScript payload is at most 165 kB gzip on the production build (CR-006 D-8, Plan gate P-2; baseline measured 2026-11-13: one chunk, 559.07 kB minified, 172.55 kB gzip).
8. The web application's inactivity tracking re-arms its timers at most once per second of continuous user activity, and the inactivity deadlines of SR-030 AC 1 and AC 2 remain accurate to within that second.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-008 "Performance and responsiveness".

## Risk Analysis

### Rationale

Concrete budgets make the performance NFR testable and protect clinical-workflow efficiency.

### Potential Risks

- User/operational risk: slow responses disrupt clinical and administrative workflows.

### Control Measures

- Define performance budgets and verify with automated performance/system tests; defer heavy operations to preserve responsiveness.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-007 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.2 (2026-09-17) — Added `satisfies` link to RR-010 (regulatory requirements
  extracted from the NFRs with clause citations). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.3 (2026-10-21) — Tagged `control:design` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.4 (2026-11-13) — Content change, so the approval is cleared and the record returns to review (CR-006, GitHub sancharly/medhub#28). Added AC 5 to AC 8: the budgets under concurrent load, non-growing data-access cost, route-level code splitting and bounded inactivity tracking. Reason: AC 1 to AC 4 say 'under normal load' without defining it or the cost of the paths that run on every request, and the review found blocking IO, a missing index set, a full table scan, an N+1 query, an unsplit bundle and an unbounded event handler (PRB-008, PRB-009, PRB-020, PRB-021, PRB-022, PRB-024, PRB-025; RISK-007).
- 1.5 (2026-11-13) — Content change, so the approval is cleared and the record returns to review (CR-006 Plan gate P-2). AC 7 budget set: initial JavaScript at most 165 kB gzip on the production build (baseline 172.55 kB gzip).
- 1.6 (2026-11-13) — Content change, so the approval is cleared and the record returns to review (CR-006 D-29, Software Architect role at the human's direction). AC 6 extended with the two lookups the code issues that no index served after migration 0011: attachments by clinical entry and active consents by doctor (TASK-219 QA finding 1; TASK-220, migration 0012). The four lookups already listed stay.
