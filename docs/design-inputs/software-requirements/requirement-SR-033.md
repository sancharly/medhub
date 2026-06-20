# SR-033 Account activation via email

## Summary

The system shall send a time-limited activation email to newly created accounts; the account becomes active only after the user follows the link and sets a password that satisfies the complexity policy.

## Description

Accounts created by administrative personnel or system administrators are initially inactive. This requirement defines the activation flow that converts an inactive account into a usable one: the system sends a unique, expiring activation link to the account's registered email address; the user opens the link, sets their password (subject to SR-025), and the account transitions to active. The flow confirms that the registered email address is reachable by the intended user before any PHI becomes accessible. If the link expires before the user activates, the creating administrator must trigger a new one.

## Acceptance Criteria

1. Immediately after account creation (SR-032), the system sends an activation email to the registered email address. The email contains a single-use activation link.
2. The activation link is valid for **72 hours** from the moment it is generated. After expiry the link is rejected and cannot be used to activate the account.
3. Following the activation link presents the user with a password-creation form. The system enforces all password complexity rules defined in SR-025 before accepting the password.
4. The password-creation form requires the user to enter the password twice in two separate fields ("Password" and "Confirm password"). The system rejects the submission if the two values do not match and displays an error message indicating the mismatch; no indication of which field is incorrect is given to avoid information leakage.
5. Once a valid, confirmed password is submitted, the account transitions from inactive to **active** and the activation link is invalidated.
6. An active account can log in using the registered email address and the password set during activation.
7. If the activation link expires before use, a system administrator or administrative personnel can resend a new activation email, which generates a new single-use link and invalidates any previously issued link for that account.
8. While an account is inactive (pending activation), the user cannot authenticate or access any part of the application.
9. Account activation events (link sent, activation completed, link expiry and resend) are recorded in the audit log (per SR-023) with account email and timestamp.

## Origin Requirement

Derived from: User Need UN-012 "User account creation and lifecycle management by authorized personnel" and Non-Functional Requirement NFR-007 "Cybersecurity".

## Risk Analysis

### Rationale

Email-based activation serves two security purposes: it verifies that the registered email address is reachable by the intended person, and it ensures the user themselves sets their own password rather than receiving one from an administrator. This prevents administrators from knowing user credentials and confirms the identity channel before PHI access is granted.

### Potential Risks

- **Security:** A compromised or incorrectly entered email address at account creation could allow an unintended person to activate the account and access PHI.
- **Security:** A non-expiring activation link is a persistent attack surface if the email is intercepted.
- **Availability:** If the activation email is lost (spam filter, wrong address), the account is inaccessible until an admin resends the link.

### Control Measures

- Email address uniqueness (SR-032 criterion 3) reduces the chance of address typos resulting in activation emails reaching an unintended recipient.
- 72-hour expiry (criterion 2) limits the window during which an intercepted link is exploitable, while being long enough to accommodate users across time zones and work schedules.
- Single-use links (criteria 2 and 7) ensure that link reuse or replay after activation is not possible.
- Admin resend capability (criterion 7) provides a recovery path without requiring account deletion and re-creation.
- Password is set by the user (criterion 3), ensuring the administrator never knows the credential; SR-025 complexity rules apply from first set.
- Password confirmation (criterion 4) prevents activation with an inadvertently mistyped password, which would immediately lock the user out of the account they just activated.

## Status

Approved

## Version History

Version 1.0 - Initial creation
