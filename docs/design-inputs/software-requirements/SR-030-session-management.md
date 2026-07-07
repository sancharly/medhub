---
id: "SR-030"
type: software-requirement
title: "Session management"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "NFR-007"
    relation: derives_from
tags: ["split-from:SR-025"]
---

## Summary

The system shall expire sessions after role-dependent inactivity periods and an absolute maximum lifetime, immediately invalidate sessions on logout, and secure session tokens against interception and theft, aligned with IEC 62443-3-3:2013 SR 1.5 (Session lock) at Security Level 2.

## Description

An authenticated but unattended session is an open door to PHI. This requirement controls how long sessions remain active, how they are terminated, and how tokens are protected in transit and storage. Two inactivity tiers are defined: a shorter timeout for clinical roles (where unattended workstations in care settings carry higher risk) and a longer timeout for administrative roles (where workflows are less time-pressured). An absolute session lifetime caps exposure regardless of continuous use.

## Acceptance Criteria

1. Sessions for users in clinical roles (doctor, patient) expire after **15 minutes** of inactivity.
2. Sessions for users in administrative roles (administrative personnel, system administrator) expire after **30 minutes** of inactivity.
3. Regardless of activity, all sessions have an absolute maximum lifetime of **8 hours**. After 8 hours the user is required to re-authenticate.
4. Users are warned with a visible countdown **2 minutes** before an inactivity timeout fires, with the option to extend the session.
5. On explicit logout, the server-side session token is immediately invalidated and cannot be reused.
6. Session tokens are transmitted only over TLS (enforced by SR-022) and stored in cookies with the `Secure`, `HttpOnly`, and `SameSite=Strict` attributes set.
7. No more than **3 concurrent active sessions** are permitted per user account. Opening a fourth session invalidates the oldest active session and presents a notification to the user.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-007 "Cybersecurity".

## Risk Analysis

### Rationale

IEC 62443-3-3 SR 1.5 (SL 2) requires the system to lock or terminate sessions after a period of inactivity to prevent unauthorized access from unattended terminals. Clinical workstations in shared care environments are particularly susceptible to opportunistic access if sessions are not actively managed.

### Potential Risks

- **Security:** Long-lived or improperly secured session tokens expose authenticated sessions to replay attacks or XSS-based token theft.
- **Privacy:** An unattended authenticated session in a shared clinical space could expose a patient's PHI to unauthorized viewers.
- **Availability:** Overly short inactivity timeouts disrupt clinical workflows requiring sustained concentration; the 2-minute warning (criterion 4) mitigates this.

### Control Measures

- Inactivity timers are enforced server-side; the 2-minute countdown (criterion 4) reduces workflow disruption.
- Server-side token invalidation on logout (criterion 5) ensures that stolen or cached tokens cannot be replayed.
- `Secure`/`HttpOnly`/`SameSite=Strict` cookie attributes (criterion 6) defend against XSS-based token extraction and cross-site request forgery.
- Concurrent session limit (criterion 7) limits the impact of token theft by bounding the number of parallel sessions an attacker can maintain.
