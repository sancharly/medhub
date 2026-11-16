---
id: SR-030
type: software-requirement
title: Session management
status: approved
version: "1.5"
author: Carlos Santiago Liceras
created: "2026-07-07"
updated: "2026-11-16"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-16"
approved_digest: 5434a4d098fceb9ef6047f226ada07608684fbd7aac01929e730a5614090af41
approval_note: self-approved
links:
  - target: RR-003
    relation: satisfies
  - target: RISK-005
    relation: mitigates
  - target: NFR-007
    relation: derives_from
tags:
  - split-from:SR-025
  - control:design
---

## Summary

The system shall expire sessions after role-dependent inactivity periods and an absolute maximum lifetime, immediately invalidate sessions on logout, and secure session tokens against interception and theft, aligned with IEC 62443-3-3:2013 SR 1.5 (Session lock) at Security Level 2.

## Description

An authenticated but unattended session is an open door to PHI. This requirement controls how long sessions remain active, how they are terminated, and how tokens are protected in transit and storage. Two inactivity tiers are defined: a shorter timeout for clinical roles (where unattended workstations in care settings carry higher risk) and a longer timeout for administrative roles (where workflows are less time-pressured). An absolute session lifetime caps exposure regardless of continuous use.

## Acceptance Criteria

1. Sessions for users in clinical roles (doctor, patient) expire after **15 minutes** of inactivity. Inactivity is a period in which the user makes no request to the server and does not extend the session (AC 4). The check of the user's enabled modules, which the web application makes in the background (SR-015 AC 5), does not count as a request; mouse, keyboard, touch or scroll input that sends no request does not count either. The server ends the session 15 minutes after the last request that counts. The web application ends it at the deadline the server last reported (AC 8): never later than the server, and earlier when requests after the last report moved the server's deadline.
2. Sessions for users in administrative roles (administrative personnel, system administrator) expire after **30 minutes** of inactivity. Inactivity has the meaning of AC 1: no request by the user, the background module check and input without a request excluded, and no extension of the session (AC 4). The server ends the session 30 minutes after the last request that counts; the web application ends it at the deadline the server last reported (AC 8), never later than the server.
3. Regardless of activity, all sessions have an absolute maximum lifetime of **8 hours**. After 8 hours the user is required to re-authenticate.
4. Users are warned with a visible countdown **2 minutes** before an inactivity timeout fires, with the option to extend the session.
5. On explicit logout, the server-side session token is immediately invalidated and cannot be reused.
6. Session tokens are transmitted only over TLS (enforced by SR-022) and stored in cookies with the `Secure`, `HttpOnly`, and `SameSite=Strict` attributes set.
7. No more than **3 concurrent active sessions** are permitted per user account. Opening a fourth session invalidates the oldest active session and presents a notification to the user.
8. The client derives its inactivity deadline and the countdown warning of AC 4 from the session expiry reported by the server, not from a value held in the client. A request that finds the session expired or invalid produces one redirect to sign-in and no repeated session-check requests.

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

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-005 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.2 (2026-09-17) — Added `satisfies` link to RR-003 (regulatory requirements
  extracted from the NFRs with clause citations). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.3 (2026-10-21) — Tagged `control:design` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.4 (2026-11-13) — Content change, so the approval is cleared and the record returns to review (CR-006, GitHub sancharly/medhub#28). Added AC 8 (client deadline from the server-reported expiry; a single redirect on an expired session). Reason: the client seeded a hard-coded 15-minute expiry and re-requested the session from nine places with differing retry settings (PRB-016; RISK-005).
- 1.5 (2026-11-16) — Content change, so the approval is cleared and the record returns to review (CR-006 D-37, human decision on P-21). AC 1 and AC 2 define "inactivity" as built in TASK-222 (CR-006 D-32, D-33): no request by the user, the background module check (`GET /me/modules`, which does not extend the session) and input that sends no request excluded, and no Extend. They also state that the web application ends the session at the server-reported deadline, so it may end it earlier than the server but never later.
