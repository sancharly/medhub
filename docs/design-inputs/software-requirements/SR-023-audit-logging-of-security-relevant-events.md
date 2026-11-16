---
id: SR-023
type: software-requirement
title: Audit logging of security-relevant events
status: approved
version: "1.5"
author: Carlos Santiago Liceras
created: "2026-07-07"
updated: "2026-11-13"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-13"
approved_digest: f478cdd5f6fc988804365b19bb56dd5e46910bd18787f141871f65975952759e
approval_note: self-approved
links:
  - target: RR-004
    relation: satisfies
  - target: RISK-001
    relation: mitigates
  - target: RISK-004
    relation: mitigates
  - target: RISK-005
    relation: mitigates
  - target: RISK-006
    relation: mitigates
  - target: NFR-004
    relation: derives_from
  - target: NFR-007
    relation: derives_from
  - target: NFR-005
    relation: derives_from
tags:
  - control:design
  - control:protective
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
10. An audit entry with outcome SUCCESS for an event caused by an HTTP request, including an access to clinical data (AC 2) and an attachment download, is committed before the response is sent and before the first byte of any content; when it cannot be committed, no content is served and the client receives a 5xx error response. A FAILURE recorded after content has started (an aborted download, SR-013 AC 5) is an additional entry committed on its own transaction. (CR-006 D-27, PRB-080, ADR-0023.)

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
- AC 10 orders the audit entry before the disclosure it records (PRB-080; RISK-006; ADR-0023).

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-001, RISK-004, RISK-005, RISK-006 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.2 (2026-09-17) — Added `satisfies` link to RR-004 (regulatory requirements
  extracted from the NFRs with clause citations). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.3 (2026-10-21) — Tagged `control:design`, `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.4 (2026-10-31) — Content change, so the record returns to review (CR-004, GitHub sancharly/medhub#27). Added AC 6 (originating client address, per SR-042), AC 7 (every authorization decision audited), AC 8 (append-only enforced by the database for the application role) and AC 9 (no secret value under any field name). Description updated to match. Reason: RR-004 requires the source address, append-only records and no secret in any record, and the review found them missing or enforced only by convention (PRB-005, PRB-010, PRB-026, PRB-027).
- 1.5 (2026-11-13) — Content change, so the record returns to review and the approval record is cleared (CR-006 D-27, PRB-080; Software Architect role at the human's direction). Added AC 10: a SUCCESS audit entry is committed before the response and before any content; an aborted download adds a FAILURE entry. Reason: the request transaction, which holds the SUCCESS rows, committed after the response was sent, so content could be disclosed before its audit entry existed.
