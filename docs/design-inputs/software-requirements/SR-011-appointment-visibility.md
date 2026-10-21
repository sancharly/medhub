---
id: "SR-011"
type: software-requirement
title: "Appointment visibility"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-10-21"
links:
  - target: "RISK-009"
    relation: mitigates
  - target: "UN-007"
    relation: derives_from
tags: ["control:design"]
---

## Summary

The system shall make an appointment visible to its associated doctor and patient and to authorized administrative personnel, and not to unrelated users.

## Description

This requirement implements appointment visibility. The doctor and patient named in an appointment can see it; administrative personnel can see appointments to perform scheduling; users with no relation to an appointment cannot see it. Visibility is enforced by the authorization mechanism.

## Acceptance Criteria

1. The doctor associated with an appointment can view it.
2. The patient associated with an appointment can view it.
3. Administrative personnel can view appointments for scheduling purposes.
4. A user not associated with an appointment and without an administrative role cannot view it.

## Origin Requirement

Derived from: User Need UN-007 "Appointment scheduling between doctors and patients".

## Risk Analysis

### Rationale

Scoped visibility ensures participants can prepare for encounters while preventing leakage of care-relationship information.

### Potential Risks

- Privacy risk: exposing appointments to unrelated users reveals care relationships.

### Control Measures

- Enforce visibility through the central authorization mechanism (SR-005).
- Cover with tests for participant and non-participant access.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-009 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.2 (2026-10-21) — Tagged `control:design` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
