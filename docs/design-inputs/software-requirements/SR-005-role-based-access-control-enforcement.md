---
id: "SR-005"
type: software-requirement
title: "Role-based access control enforcement"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "UN-003"
    relation: derives_from
  - target: "UN-004"
    relation: derives_from
  - target: "UN-006"
    relation: derives_from
  - target: "NFR-004"
    relation: derives_from
tags: []
---

## Summary

The system shall enforce role-based access control so that every request to data or modules is authorized against the requesting user's type, relationships, and consents, denying access by default.

## Description

This requirement implements the central access-control mechanism shared by multiple needs. Each protected operation is checked against a policy that considers the user's type, care relationships (doctor-patient), patient consent state, and group/module enablement. Access is denied unless explicitly permitted (deny-by-default). This mechanism realizes type differentiation, doctor scoping, administrative-personnel restriction, and data-minimization.

## Acceptance Criteria

1. Every request to clinical data, personal data, and modules passes through an authorization check before the resource is returned.
2. Access is denied by default; only explicitly permitted operations succeed.
3. Authorization decisions account for: user type, doctor-patient care relationship, patient consent state, and module/group enablement.
4. A denied request returns an authorization error and does not disclose protected data.

## Origin Requirement

Derived from: User Need UN-003 "Differentiated access by user type", UN-004 "Doctor access to own patients' clinical data", UN-006 "Administrative personnel limited access and scheduling", and Non-Functional Requirement NFR-004 "GDPR compliance".

## Risk Analysis

### Rationale

A single, consistently applied authorization mechanism is required to guarantee confidentiality and data-minimization across all features and to avoid divergent, error-prone per-feature checks.

### Potential Risks

- Security/privacy risk: broken access control is a leading cause of health-data exposure.
- Compliance risk: failure to minimize access violates GDPR.

### Control Measures

- Centralize authorization; deny-by-default; cover with automated tests including negative (forbidden) cases.
- Decisions are recorded by the audit log (SR-023); consent inputs maintained by SR-008.
