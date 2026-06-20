# UN-012 User account creation and lifecycle management by authorized personnel

## Summary

Administrative personnel and system administrators need to create new user accounts with basic identifying information and to deactivate or remove accounts when access is no longer needed, so that the user population is controlled and access to protected health information is properly governed throughout each user's relationship with the organization.

## Description

MedHub holds Protected Health Information (PHI) that must not be accessible to unauthorized individuals. No user should be able to self-register; instead, accounts must be created by personnel who have the authority and context to decide who should have access and at what role. Once created, accounts must follow a secure activation flow before the new user can access the system. Administrators also need to revoke access promptly — by deactivating or permanently removing an account — when a user leaves a role or the organization.

## Acceptance Criteria

1. A new user account can only be created by administrative personnel or a system administrator; no self-registration path exists.
2. The minimum information required to create an account is first name, surname, and email address.
3. Administrative personnel can create accounts for patients, doctors, and other administrative personnel, but not for system administrators.
4. System administrators can create accounts for all user types, including other system administrators.
5. A newly created account is inactive until the user completes email-based activation; the user cannot log in before activation.
6. System administrators can deactivate an account, preventing the user from logging in without permanently deleting their data.
7. System administrators can permanently delete an account, removing the user from the system.

## Risk Analysis

### Rationale

Derived from the MedHub goals "User types" and "User profiles": the platform distinguishes four user roles and each user is identified by email and password. Unauthorized account creation or failure to revoke access in a timely manner would expose PHI to individuals who should not have it, creating compliance risks under GDPR, MDR, and FDA cybersecurity guidance.

### Potential Risks

- **Privacy:** Unrestricted account creation allows unauthorized individuals to obtain access to PHI.
- **Security:** Accounts that are not deactivated when a user leaves the organization remain an active attack surface.
- **Compliance:** Lack of controlled user provisioning conflicts with GDPR data minimization and access-control requirements, and with MDR/FDA cybersecurity expectations.

### Control Measures

- Role constraints on who can create which account types are specified in software requirements derived from this need.
- Email-based activation ensures that a valid email address is confirmed before any PHI is accessible.
- Deactivation and deletion capabilities give administrators the tools to enforce timely access revocation.

## Status

Approved

## Version History

Version 1.0 - Initial creation
