# SR-003 Unique user account and profile view

## Summary

The system shall maintain a unique account per email address and allow each authenticated user to view their own profile information.

## Description

This requirement implements the profile aspect of the authenticated-user need. Each account is uniquely keyed by email; the system rejects creation of a second account with an existing email. Authenticated users can view their personal profile data. Profile data exposure follows data-minimization.

## Acceptance Criteria

1. The system rejects creation of an account with an email that already exists.
2. An authenticated user can view a profile page showing their own personal information.
3. A user cannot view another user's profile data except where their role explicitly permits it.

## Origin Requirement

Derived from: User Need UN-002 "Personal, authenticated user profile" and Non-Functional Requirement NFR-004 "GDPR compliance".

## Risk Analysis

### Rationale

Unique identification underpins access control; profile self-service supports the GDPR right of access while data-minimization limits exposure.

### Potential Risks

- Privacy risk: profile data leaking to other users breaches confidentiality.
- Data-integrity risk: duplicate accounts for one email break access decisions.

### Control Measures

- Enforce email uniqueness at the data layer; scope profile retrieval to the authenticated user.
- Broader access scoping enforced by SR-005.

## Status

Approved

## Version History

Version 1.0 - Initial creation
