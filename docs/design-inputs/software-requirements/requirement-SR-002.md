# SR-002 Email and password authentication

## Summary

The system shall authenticate users with an email address as username and a password before granting access to any protected resource.

## Description

This requirement implements user authentication. Users log in with their email and password. Successful authentication establishes a session; failed authentication denies access. All protected resources require an authenticated session. Password handling follows secure practices (hashing, never stored or logged in clear text).

## Acceptance Criteria

1. A user can authenticate by submitting a valid email/password pair and is granted a session on success.
2. Authentication with an unknown email or incorrect password is rejected with a generic failure message (no disclosure of which field was wrong).
3. Unauthenticated requests to protected resources are denied and redirected to the login flow.
4. Passwords are stored only as salted cryptographic hashes and never logged in clear text.

## Origin Requirement

Derived from: User Need UN-002 "Personal, authenticated user profile" and Non-Functional Requirement NFR-007 "Cybersecurity".

## Risk Analysis

### Rationale

Authentication is the foundation of access control and data protection required by GDPR and medical-device cybersecurity.

### Potential Risks

- Security risk: weak authentication exposes all health and personal data.
- Compliance risk: clear-text credential storage violates security expectations.

### Control Measures

- Use a vetted authentication library and salted hashing; generic error messages to avoid user enumeration.
- Credential strength and lockout are reinforced by SR-025.

## Status

Approved

## Version History

Version 1.0 - Initial creation
