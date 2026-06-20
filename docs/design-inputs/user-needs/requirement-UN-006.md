# UN-006 Administrative personnel limited access and scheduling

## Summary

Administrative personnel need access to limited, non-clinical personal information of patients and doctors and the ability to schedule appointments between them, without access to clinical data.

## Description

Administrative staff run the operational side of a clinic: booking visits and managing basic identity information. To do this they need limited personal details (such as name, family name, and date of birth) of patients and doctors and the ability to arrange appointments between a doctor and a patient. They must never be able to access clinical data, as that would violate the principle of least privilege and patient confidentiality.

## Acceptance Criteria

1. Administrative personnel can view a limited set of non-clinical personal fields (at minimum name, family name, date of birth) of patients and doctors.
2. Administrative personnel can create appointments between a doctor and a patient.
3. Administrative personnel cannot view or access any clinical data.

## Risk Analysis

### Rationale

Derived from the MedHub goal "Administrative personal permissions": administrative personnel access limited personal information (name, family name, date of birth) but no clinical data, and can schedule appointments between doctors and patients.

### Potential Risks

- Privacy/security risk: leakage of clinical data to administrative staff breaches confidentiality and GDPR data-minimization.
- Operational risk: inability to schedule disrupts clinic operations.

### Control Measures

- A non-clinical data scope and a scheduling capability are specified in software requirements traced to this need.
- Clinical-data exclusion for this user type is enforced by the role-based access-control mechanism (UN-003) and verified by tests.

## Status

Approved

## Version History

Version 1.0 - Initial creation
