# SR-011 Appointment visibility

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

## Status

Approved

## Version History

Version 1.0 - Initial creation
