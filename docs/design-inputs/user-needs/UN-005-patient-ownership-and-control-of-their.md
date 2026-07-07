---
id: "UN-005"
type: user-need
title: "Patient ownership and control of their clinical data"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links: []
tags: []
---

## Summary

A patient needs to access their own personal and clinical data and to grant or revoke a doctor's access to that clinical data.

## Description

Patients are the owners of their own health information. They need to view their personal and clinical data held in MedHub and to decide which doctors may access their clinical data, granting access when they seek care and revoking it when the care relationship ends. This consent control is central to patient autonomy and to GDPR's lawful-basis and data-subject-rights requirements.

## Acceptance Criteria

1. A patient can view their own personal data and their own clinical data.
2. A patient can grant a specific doctor access to their clinical data.
3. A patient can revoke a previously granted doctor's access to their clinical data.
4. After revocation, the affected doctor can no longer access that patient's clinical data.

## Risk Analysis

### Rationale

Derived from the MedHub goal "Patient permissions": patients can access their own personal and clinical data and can give or revoke clinical-data access to doctors.

### Potential Risks

- Compliance risk: inability to grant/revoke consent conflicts with GDPR data-subject rights.
- Privacy risk: a revocation that does not take effect leaves clinical data exposed to a doctor the patient no longer authorizes.
- Safety risk: accidental revocation could deprive a treating doctor of needed data.

### Control Measures

- Grant/revoke workflows and their immediate enforcement are specified in software requirements traced to this need.
- Consent state drives the doctor access checks defined for UN-004.
- Consent changes are audit-logged under NFR-007.
