---
id: "SR-034"
type: software-requirement
title: "Account deactivation and deletion by system administrator"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "UN-012"
    relation: derives_from
  - target: "NFR-004"
    relation: derives_from
  - target: "NFR-007"
    relation: derives_from
tags: []
---

## Summary

The system shall allow system administrators to deactivate a user account (blocking access while retaining data) or permanently delete it (removing the user record), with immediate effect on any active sessions.

## Description

Access revocation is as critical as access provisioning. When a user leaves an organization or role, their account must be disabled promptly to prevent further access to PHI. This requirement provides two distinct operations: **deactivation**, which suspends access without destroying data (appropriate for temporary suspension, role change, or pending investigation), and **deletion**, which permanently removes the user record (appropriate for permanent offboarding or a GDPR erasure request). Only system administrators have this authority. Any active sessions belonging to the affected account are terminated immediately when either operation is applied.

## Acceptance Criteria

1. A system administrator can deactivate any user account regardless of type (including other system administrators), except their own account.
2. A deactivated account cannot authenticate; any active sessions belonging to the account are invalidated within **30 seconds** of deactivation.
3. A deactivated account's data (profile, clinical records, audit log entries) is retained and remains accessible to authorized users and administrators.
4. A system administrator can reactivate a deactivated account. The reactivated account can log in immediately with its existing credentials; no new activation email is sent.
5. A system administrator can permanently delete a user account. Deletion removes the user's authentication credentials and personal identifying information. Clinical records authored by or associated with that user are anonymized or handled per the data retention policy defined under SR-024, not silently erased.
6. Before permanent deletion the system presents a confirmation step that displays the account's email address and type and requires explicit confirmation; deletion cannot be undone.
7. A deleted account's email address is released and can be registered to a new account.
8. Deactivation, reactivation, and deletion events are recorded in the audit log (per SR-023) with: acting administrator's identity, affected account's email and type, operation performed, and timestamp.

## Origin Requirement

Derived from: User Need UN-012 "User account creation and lifecycle management by authorized personnel", Non-Functional Requirement NFR-004 "GDPR compliance", and Non-Functional Requirement NFR-007 "Cybersecurity".

## Risk Analysis

### Rationale

Failure to revoke access promptly when a user leaves is a leading cause of unauthorized PHI exposure. GDPR Article 17 (right to erasure) also requires that personal data be deleted on request under certain conditions. Providing deactivation as a lighter-weight alternative to deletion allows organizations to suspend access quickly (e.g., during an HR investigation) without destroying data that may be needed for audit or clinical purposes.

### Potential Risks

- **Security:** Accounts that are not deactivated when a user leaves remain active credentials that can be exploited, particularly if the user retains their password.
- **Compliance (GDPR):** Inability to permanently delete a user's personal data prevents satisfaction of lawful erasure requests under GDPR Article 17.
- **Safety:** Immediate session termination (criterion 2) is critical — a deactivated but still-authenticated session could be used to access PHI in the window before the session expires naturally.
- **Data integrity:** Deletion of clinical records (as opposed to anonymization) could destroy information needed for ongoing patient care.

### Control Measures

- Immediate session invalidation (criterion 2) closes the window between deactivation decision and access revocation; the 30-second bound accommodates distributed session stores with propagation delay.
- Self-deactivation is blocked (criterion 1) to prevent administrators from accidentally locking themselves out or being socially engineered into doing so.
- Permanent deletion anonymizes rather than erases clinical records (criterion 5), preserving clinical integrity while removing personal identifying information as required by GDPR.
- Explicit confirmation step (criterion 6) prevents accidental irreversible deletions.
- Audit logging (criterion 8) provides a complete chain of custody for all lifecycle events, supporting both security forensics and regulatory audit.
