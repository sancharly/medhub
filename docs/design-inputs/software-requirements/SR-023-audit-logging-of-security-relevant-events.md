---
id: "SR-023"
type: software-requirement
title: "Audit logging of security-relevant events"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-09-17"
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
tags: []
---

## Summary

The system shall record an audit log of security-relevant events, including authentication, access to clinical data, consent changes, and administrative actions.

## Description

This requirement implements auditability shared by GDPR, cybersecurity, and medical-device traceability. The system records, for each security-relevant event, the actor, action, target, timestamp, and outcome. The log supports accountability and breach investigation. Logs are protected against unauthorized modification and do not contain plaintext credentials or unnecessary clinical content.

## Acceptance Criteria

1. Authentication attempts (success and failure) are recorded with actor and timestamp.
2. Access to a patient's clinical data is recorded with actor, target patient, and timestamp.
3. Consent grant/revoke actions are recorded with actor, target, and timestamp.
4. Administrative actions (user-type change, group/module management) are recorded.
5. Audit log entries cannot be modified by ordinary users and do not contain plaintext credentials.

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

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-001, RISK-004, RISK-005, RISK-006 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.2 (2026-09-17) — Added `satisfies` link to RR-004 (regulatory requirements
  extracted from the NFRs with clause citations). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
