# SR-006 Doctor access to own patients' clinical data

## Summary

The system shall allow a doctor to view the clinical data of patients with whom they have a care relationship or who have granted them access, and shall deny access to all other patients' clinical data.

## Description

This requirement implements the doctor permissions need on top of the access-control mechanism. A doctor sees a list of patients they are authorized for and can open those patients' clinical data (clinical entries and attachments). Requests for unauthorized patients are denied.

## Acceptance Criteria

1. A doctor can retrieve the list of patients for whom they have a care relationship or granted access.
2. A doctor can open and view the clinical entries and attachments of an authorized patient.
3. A request by a doctor to view clinical data of a non-authorized patient is denied.
4. The authorization basis (relationship or granted consent) is recorded for audit.

## Origin Requirement

Derived from: User Need UN-004 "Doctor access to own patients' clinical data".

## Risk Analysis

### Rationale

Scoping doctor access to their own patients enforces patient confidentiality while ensuring treating clinicians have the data they need.

### Potential Risks

- Privacy risk: over-broad access exposes other doctors' patients.
- Safety risk: wrongly denied access could withhold needed clinical context.

### Control Measures

- Enforce via the central authorization mechanism (SR-005) using care relationships and consent (SR-008).
- Cover with automated negative tests; record access in the audit log (SR-023).

## Status

Approved

## Version History

Version 1.0 - Initial creation
