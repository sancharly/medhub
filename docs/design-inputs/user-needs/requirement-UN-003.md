# UN-003 Differentiated access by user type

## Summary

The platform needs to distinguish between doctors, patients, administrative personnel, and system administrators so each user type can access only the data and modules appropriate to their role.

## Description

MedHub serves four distinct user types with very different responsibilities and data-access needs. A doctor manages clinical care, a patient owns their own health data, administrative personnel handle scheduling and basic personal data, and a system administrator configures the platform. Each user must be associated with a user type, and the data and modules they can reach must depend on that type. Mixing these responsibilities would breach confidentiality and clinical-safety expectations.

## Acceptance Criteria

1. Every user account is associated with exactly one of the four user types: doctor, patient, administrative personnel, system administrator.
2. The data and modules a user can access are determined by their user type.
3. A user of one type cannot access data or modules reserved for another type.

## Risk Analysis

### Rationale

Derived from the MedHub goal "User types": the application shall consider doctor, patient, system administrator, and administrative personnel, where different user types can access different data and modules.

### Potential Risks

- Security/privacy risk: incorrect type assignment could expose clinical or personal data to users who should not see it.
- Compliance risk: improper data segregation conflicts with GDPR data-minimization principles.

### Control Measures

- User-type assignment and type-based access gating are specified in software requirements and enforced by the role-based access-control mechanism.
- Type-specific data scoping is further refined by UN-004, UN-005, and UN-006.

## Status

Approved

## Version History

Version 1.0 - Initial creation
