---
id: "SR-025"
type: software-requirement
title: "Password complexity policy"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "NFR-007"
    relation: derives_from
tags: []
---

## Summary

The system shall enforce password complexity and lifecycle rules at account creation and every credential change, aligned with IEC 62443-3-3:2013 SR 5.1 (Authentication credentials management) at Security Level 2.

## Description

Passwords are the primary credential protecting PHI in MedHub. This requirement defines the structural and lifecycle rules that passwords must satisfy to resist brute-force and dictionary attacks. Rules are enforced server-side at every point where a password is set or changed; client-side validation is supplementary only. Error feedback identifies the violated rule without revealing the rejected password.

## Acceptance Criteria

1. The system rejects any password shorter than **12 characters**.
2. The system rejects any password that does not contain at least one character from each of the following four classes: uppercase letter (A–Z), lowercase letter (a–z), decimal digit (0–9), and special character (e.g., `!@#$%^&*()-_=+[]{}|;:'",.<>?/`).
3. The system rejects any password that contains the user's username or email address as a substring (case-insensitive).
4. The system rejects any new password that matches any of the user's last **12** passwords.
5. Rules are enforced at account creation, password change, and administrator-initiated password reset. The error message identifies which rule was violated.
6. A system-assigned (temporary) password must be changed by the user on first login before any other action is permitted.
7. The system enforces a maximum password age of **180 days**. Users are notified 14 days before expiry and required to change their password at next login after expiry.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-007 "Cybersecurity".

## Risk Analysis

### Rationale

Weak passwords are the most common vector for PHI data breaches. IEC 62443-3-3 SR 5.1 (SL 2) requires management of authentication credentials including strength rules and lifecycle controls.

### Potential Risks

- **Security:** Weak or reused passwords allow brute-force or credential-stuffing attacks that expose clinical data.
- **Compliance:** Absence of documented complexity rules conflicts with IEC 62443 SL 2 and MDR/FDA cybersecurity expectations.

### Control Measures

- Server-side enforcement at every credential-change entry point; client-side validation is a convenience layer only.
- Password history (criterion 4) and maximum age (criterion 7) prevent credential reuse and limit the exposure window of a compromised password.
- Account lockout after repeated failures is covered separately in SR-029.


## Revision History

Version 1.0 - Initial creation
Version 1.1 - Requirement split from combined SR-025; scope narrowed to password complexity and lifecycle
