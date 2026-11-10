---
id: "SR-023"
type: software-requirement
title: "Audit logging of security-relevant events"
status: approved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-10-31"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-31"
approval_note: self-approved at the ship-feature spec gate (sancharly/medhub#27)
links:
  - target: "RR-004"
    relation: satisfies
  - target: "RISK-001"
    relation: mitigates
  - target: "RISK-004"
    relation: mitigates
  - target: "RISK-005"
    relation: mitigates
  - target: "RISK-006"
    relation: mitigates
  - target: "NFR-004"
    relation: derives_from
  - target: "NFR-007"
    relation: derives_from
  - target: "NFR-005"
    relation: derives_from
tags: ["control:design", "control:protective"]
---

## Summary

The system shall record an audit log of security-relevant events, including authentication, access to clinical data, consent changes, and administrative actions.

## Description

This requirement implements auditability shared by GDPR, cybersecurity, and medical-device traceability. The system records, for each security-relevant event, the actor, action, target, timestamp, outcome and source address (RR-004). The log supports accountability and breach investigation. Logs are append-only, protected by the database against modification by the application itself, and do not contain plaintext credentials, secrets or unnecessary clinical content. §5.2.2 category e (audit trail).

## Acceptance Criteria

1. Authentication attempts (success and failure) are recorded with actor and timestamp.
2. Access to a patient's clinical data is recorded with actor, target patient, and timestamp.
3. Consent grant/revoke actions are recorded with actor, target, and timestamp.
4. Administrative actions (user-type change, group/module management) are recorded.
5. Audit log entries cannot be modified by ordinary users and do not contain plaintext credentials.
6. An audit entry for an event caused by an HTTP request records the originating client address of that request, determined as defined in SR-042. An entry for an event with no request (background or scheduled job) records no address and is still written.
7. Every authorization decision, allowed or denied, on clinical data, personal data, modules or account-lifecycle operations (SR-005, SR-032, SR-034) produces an audit entry with actor, action, target, outcome, timestamp and source address. No allowed or denied access is decided without such an entry.
8. The database role the application connects with cannot update or delete rows of the audit table: an `UPDATE` or `DELETE` on it issued with that role fails with a permission error.
9. A value the application issued or received as a credential or secret (password, session token, activation or password-reset token, anonymized-data retrieval code, encryption or access key) is not stored in plaintext in any audit entry, whatever field name the caller passes it under.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-004 "GDPR compliance", NFR-007 "Cybersecurity", and NFR-005 "Medical device regulatory compliance (MDR and FDA)".

## Risk Analysis

### Rationale

Audit trails are required for GDPR accountability, security incident investigation, and medical-device records.

### Potential Risks

- Compliance risk: absence of audit logs undermines accountability obligations.
- Security risk: tamperable logs cannot be trusted during investigation.

### Control Measures

- Centralize logging of the listed events; protect log integrity; exclude sensitive plaintext.
- Events are produced by SR-002, SR-005/SR-006, SR-008, SR-014/SR-015.
- AC 6 to AC 9 realize the RR-004 acceptance criteria (source address, no update or delete by the application role, no secret in any record) that AC 1 to AC 5 left implicit (PRB-005, PRB-010, PRB-026, PRB-027; RISK-006).

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-001, RISK-004, RISK-005, RISK-006 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.2 (2026-09-17) — Added `satisfies` link to RR-004 (regulatory requirements
  extracted from the NFRs with clause citations). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.3 (2026-10-21) — Tagged `control:design`, `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.4 (2026-10-31) — Content change, so the record returns to review (CR-004, GitHub sancharly/medhub#27). Added AC 6 (originating client address, per SR-042), AC 7 (every authorization decision audited), AC 8 (append-only enforced by the database for the application role) and AC 9 (no secret value under any field name). Description updated to match. Reason: RR-004 requires the source address, append-only records and no secret in any record, and the review found them missing or enforced only by convention (PRB-005, PRB-010, PRB-026, PRB-027).
