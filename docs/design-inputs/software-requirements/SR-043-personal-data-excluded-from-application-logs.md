---
id: "SR-043"
type: software-requirement
title: "Personal data excluded from application logs"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-31"
approval_note: self-approved at the ship-feature spec gate (sancharly/medhub#27)
links:
  - target: "RR-001"
    relation: satisfies
  - target: "RR-002"
    relation: satisfies
  - target: "NFR-004"
    relation: derives_from
  - target: "RISK-008"
    relation: mitigates
tags: ["control:design", "control:protective", "issue:sancharly/medhub#27"]
---

## Summary

The system shall not write personal identifying data or clinical content to its operational logs; it shall refer to accounts and patients by their identifiers.

## Description

Operational logs (the JSON log stream of the backend, the worker and the scheduler) go to whatever log sink the operator collects them in. That sink is outside the retention and erasure machinery of SR-024, so any personal data written there is a copy that cannot be erased and that has no lawful basis (PRB-011). The audit log is out of scope here; SR-023 governs it.

§5.2.2 categories: e (security: sensitive-information compromise), g (data definition).

## Acceptance Criteria

1. No record written to the operational log stream contains an email address, first name, surname or date of birth of an account holder or patient, or the free text of a clinical entry. Accounts and patients are referred to by their identifiers.
2. Every application logger applies a redaction filter that replaces email-shaped values in the message and in every structured field, under any field name, before the record is emitted.
3. Tests run the email worker task's success path and its failure path with a known recipient address, and assert that the captured log output does not contain that address. A test passes an email address through a structured field with an arbitrary name and asserts that the emitted record does not contain it.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-004 "GDPR compliance". Satisfies RR-001 "Lawful basis and data minimization for processing health data" and RR-002 "Right to erasure of personal data".

## Risk Analysis

### Rationale

GDPR data minimization (RR-001) and the right to erasure (RR-002) can only hold if personal data stays inside the stores the application controls. A log copy defeats both.

### Potential Risks

- Personal data persists in log archives after an erasure request, or reaches people with access to the logs but not to the application (RISK-008).

### Control Measures

- Identifiers instead of personal data at the source (AC 1); a redaction filter as a safety net (AC 2); tests that fail if an address reaches the log (AC 3).
- The TS is written at the Build stage.

## Version history

- 1.0 (2026-10-31) — Initial creation (CR-004, GitHub sancharly/medhub#27), from PRB-011.
