# SR-012 Clinical entry creation with required fields

## Summary

The system shall allow a doctor to create a clinical entry associated with a patient, capturing at least date/time, patient, authoring doctor, and a description.

## Description

This requirement implements clinical-entry recording. A doctor creates an entry tied to a specific patient. The entry stores at minimum the date and time, the patient reference, the authoring doctor reference, and a textual description. The authoring doctor is recorded automatically from the authenticated session to ensure correct attribution. Saved entries become part of the patient's clinical history.

## Acceptance Criteria

1. A doctor can create a clinical entry and associate it with a specific patient.
2. The entry records date/time, patient, authoring doctor, and a description; the system rejects an entry missing any of these.
3. The authoring doctor is set from the authenticated user and cannot be spoofed by the client.
4. A saved entry is retrievable as part of the patient's clinical history by authorized users.

## Origin Requirement

Derived from: User Need UN-008 "Recording clinical entries for a patient".

## Risk Analysis

### Rationale

Accurate, well-attributed clinical entries are the core clinical asset and the basis for continuity of care.

### Potential Risks

- Safety risk: incomplete or mis-attributed entries can lead to incorrect clinical decisions.
- Data-integrity risk: associating an entry with the wrong patient breaches safety and confidentiality.

### Control Measures

- Validate required fields; derive authoring doctor from the session; confirm patient association.
- Retrieval gated by authorization (SR-005, SR-006, SR-007); attachments handled by SR-013.

## Status

Approved

## Version History

Version 1.0 - Initial creation
