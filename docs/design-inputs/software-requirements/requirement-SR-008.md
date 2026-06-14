# SR-008 Patient grant and revoke of clinical-data access

## Summary

The system shall allow a patient to grant and revoke a specific doctor's access to the patient's clinical data, with revocation taking effect immediately.

## Description

This requirement implements patient consent control. A patient can select a doctor and grant access to their clinical data, and can later revoke that access. The current consent state is an input to the authorization mechanism, so granting enables and revoking immediately disables the doctor's access. All consent changes are recorded.

## Acceptance Criteria

1. A patient can grant a named doctor access to the patient's clinical data.
2. After a grant, the doctor can view that patient's clinical data (subject to SR-006).
3. A patient can revoke a previously granted doctor's access.
4. After revocation, any subsequent request by that doctor to view the patient's clinical data is denied.
5. Each grant and revoke action is recorded in the audit log with actor, target, and timestamp.

## Origin Requirement

Derived from: User Need UN-005 "Patient ownership and control of their clinical data" and Non-Functional Requirement NFR-004 "GDPR compliance".

## Risk Analysis

### Rationale

Grant/revoke consent realizes GDPR data-subject control and is the basis for lawful doctor access to clinical data.

### Potential Risks

- Privacy risk: a revoke that does not take effect leaves data exposed.
- Safety risk: accidental revoke could remove a treating doctor's access.
- Compliance risk: missing consent records weaken accountability.

### Control Measures

- Drive authorization (SR-005, SR-006) from current consent state so revocation is immediate.
- Require confirmation for revoke (per NFR-009 via SR-027); record changes in audit log (SR-023).

## Status

Draft

## Version History

Version 1.0 - Initial creation
