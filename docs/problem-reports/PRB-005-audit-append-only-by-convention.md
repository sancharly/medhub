---
id: "PRB-005"
type: problem-report
title: "Audit log is append-only by convention rather than by the database, and its scrub is pattern-limited"
status: open
criticality: major
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["security", "hazard:detectability"]
---

# PRB-005 — Audit log is append-only by convention rather than by the database, and its scrub is pattern-limited

## Observed

`app/audit/service.py` relies on callers never updating or deleting audit rows — no database grant or trigger enforces it — and the credential scrub is a regex/pattern list, so an unexpected field name can carry a secret into the log.

## Impact

SR-023 (audit logging of security-relevant events) can be defeated by any future code path, which undermines the evidence needed to detect a wrong disclosure.

## Safety evaluation

Contributes to RISK-006 (incomplete audit trail). No tampering observed.

## Resolution

Not yet tracked by a task. Proposed: `REVOKE UPDATE, DELETE` on the audit table for the application role, document the caller contract, and add a denylist test for secret-shaped values. Needs a task and a CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Medium.
