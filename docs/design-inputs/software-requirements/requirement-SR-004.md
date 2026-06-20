# SR-004 User type assignment

## Summary

The system shall associate each user account with exactly one user type from the set {doctor, patient, administrative personnel, system administrator}.

## Description

This requirement implements the differentiation of user types. Every account has a single user type, set at creation and managed by a system administrator. The user type is the primary input to access-control decisions and to automatic group membership.

## Acceptance Criteria

1. Every account has exactly one user type, drawn from the four defined types.
2. An account cannot exist without a user type.
3. A system administrator can set or change an account's user type.
4. The user type is available to the access-control mechanism for every request.

## Origin Requirement

Derived from: User Need UN-003 "Differentiated access by user type".

## Risk Analysis

### Rationale

Reliable user-type classification is a precondition for correct, least-privilege access control under GDPR and confidentiality obligations.

### Potential Risks

- Security risk: a missing or wrong user type could grant inappropriate access.
- Operational risk: ambiguous typing complicates group automation.

### Control Measures

- Constrain user type to the enumerated set at the data layer; require it on account creation.
- Type-driven access enforced by SR-005; automatic grouping by SR-014.

## Status

Approved

## Version History

Version 1.0 - Initial creation
