# SR-032 Role-constrained user account creation

## Summary

The system shall allow only administrative personnel and system administrators to create new user accounts, enforcing minimum required fields and restricting each creator role to the account types it is permitted to create.

## Description

User account creation is a privileged operation that determines who gains access to PHI. This requirement defines the data required to create an account and the constraints on which user roles may create which account types. No self-registration mechanism shall exist. The constraint that administrative personnel cannot create system administrator accounts prevents privilege escalation: only an existing system administrator may grant system-level access.

## Acceptance Criteria

1. No user registration form or endpoint is accessible without an authenticated session belonging to an administrative personnel or system administrator account.
2. The following fields are mandatory for account creation; the system rejects submissions where any of these is absent or empty: first name, surname, email address.
3. The email address supplied must be unique across the system; the system rejects creation if the email is already registered to an existing account (active, inactive, or deleted).
4. An administrative personnel user can create accounts of the following types only: Patient, Doctor, Administrative Personnel. The system prevents selection or submission of the System Administrator type for this creator role.
5. A system administrator user can create accounts of all types: Patient, Doctor, Administrative Personnel, and System Administrator.
6. Upon successful creation the account is created in an **inactive** state (see SR-033 for the activation flow); the new user cannot log in until activation is complete.
7. The creating user's identity, the new account's email address and type, and the creation timestamp are recorded in the audit log (per SR-023).

## Origin Requirement

Derived from: User Need UN-012 "User account creation and lifecycle management by authorized personnel" and User Need UN-003 "Differentiated access by user type".

## Risk Analysis

### Rationale

Controlled account creation is the first gate in preventing unauthorized access to PHI. Restricting creation to authorized roles and capturing minimum identifying information ensures accountability and reduces the risk of phantom or unauthorized accounts.

### Potential Risks

- **Security:** If any authenticated user could create accounts, an attacker with a low-privilege account could create additional accounts to maintain persistence.
- **Privilege escalation:** If administrative personnel could create system administrator accounts, they could grant themselves or others elevated access beyond their authorization.
- **Data integrity:** Duplicate email addresses would make authentication and communication unreliable.

### Control Measures

- The account creation endpoint enforces the creator's role server-side; the permitted account types are not solely controlled by the client UI.
- Uniqueness of email (criterion 3) is enforced at the database level with a unique constraint in addition to application-layer validation.
- Audit logging (criterion 7) provides a traceable record of every account creation event for security review and compliance.

## Status

Approved

## Version History

Version 1.0 - Initial creation
