# UN-004 Doctor access to own patients' clinical data

## Summary

A doctor needs to access the clinical data of their own patients so they can review history and deliver care, while being prevented from accessing other doctors' patients.

## Description

During consultations and procedures a doctor needs the clinical context of the patients under their care: prior clinical entries, attached files, diagnoses, and results. They must be able to see this information efficiently. At the same time, a doctor must not be able to access the clinical data of patients who are not under their care or who have not granted them access, to preserve patient confidentiality and meet legal and ethical obligations.

## Acceptance Criteria

1. A doctor can view the clinical data of patients for whom they have a care relationship or have been granted access.
2. A doctor cannot view the clinical data of patients with whom they have no relationship and no granted access.
3. The set of patients a doctor can access is explicit and auditable.

## Risk Analysis

### Rationale

Derived from the MedHub goal "Doctors permissions": doctors can access the clinical data of their own patients but not other doctors' patients.

### Potential Risks

- Privacy/security risk: over-broad access exposes patients' clinical data to clinicians not involved in their care.
- Safety risk: if a treating doctor cannot reach relevant clinical data, care decisions may be made on incomplete information.

### Control Measures

- Doctor-to-patient access scoping is enforced by role-based access-control software requirements traced to this need and coordinated with patient consent (UN-005).
- Access decisions are subject to audit logging defined under the cybersecurity NFR (NFR-007).

## Status

Approved

## Version History

Version 1.0 - Initial creation
