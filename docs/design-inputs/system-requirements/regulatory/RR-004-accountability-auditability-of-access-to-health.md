---
id: "RR-004"
type: regulatory-requirement
title: "Accountability: auditability of access to health data"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links:
  - target: "UN-005"
    relation: derives_from
tags: ["gdpr", "security"]
---

# RR-004 — Accountability: auditability of access to health data

## Summary

The controller must be able to demonstrate, after the fact, who accessed or changed which health data and when.

## Source

GDPR Art. 5(2) accountability and Art. 33 breach notification; IEC 62304 §5.2.2 e (audit trail); NFR-004.

## Obligation

The software shall record an append-only audit entry for every authentication, authorization decision and clinical-data access or modification, sufficient to reconstruct the event, and shall not record credentials or plaintext secrets.

## Acceptance criteria

- An audit entry exists for each security-relevant action, with actor, action, target, outcome, timestamp and source address.
- Audit records cannot be updated or deleted by the application role.
- No credential or secret value appears in any audit or log record.

## Realized by

SR-023. Problem reports: PRB-005, PRB-010. Risk: RISK-006.
