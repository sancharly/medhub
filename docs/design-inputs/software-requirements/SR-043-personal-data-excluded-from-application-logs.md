---
id: "SR-043"
type: software-requirement
title: "Personal data and credentials excluded from operational logs"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-07"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-07"
approval_note: approved by the human in chat (CR-004, AC 4 for credentials in logs)
links:
  - target: "RR-001"
    relation: satisfies
  - target: "RR-002"
    relation: satisfies
  - target: "NFR-004"
    relation: derives_from
  - target: "NFR-007"
    relation: derives_from
  - target: "RR-003"
    relation: satisfies
  - target: "RISK-008"
    relation: mitigates
  - target: "RISK-005"
    relation: mitigates
  - target: "SR-033"
    relation: relates_to
  - target: "SR-023"
    relation: relates_to
tags: ["control:design", "control:protective", "issue:sancharly/medhub#27"]
---

## Summary

The system shall not write personal identifying data or clinical content to its operational logs; it shall refer to accounts and patients by their identifiers. No credential or secret shall appear in any operational or proxy log.

## Description

Operational logs (the JSON log stream of the backend, the worker and the scheduler) go to whatever log sink the operator collects them in. That sink is outside the retention and erasure machinery of SR-024, so any personal data written there is a copy that cannot be erased and that has no lawful basis (PRB-011). The audit log is out of scope here; SR-023 governs it. Credentials and secrets are also kept out of these logs and out of the reverse-proxy and frontend-container logs, which record request URLs and Referers: a credential copied there can be replayed by anyone who reads the logs (PRB-068: the activation token of SR-033).

§5.2.2 categories: e (security: sensitive-information compromise), g (data definition).

## Acceptance Criteria

1. No record written to the operational log stream contains an email address, first name, surname or date of birth of an account holder or patient, or the free text of a clinical entry. Accounts and patients are referred to by their identifiers.
2. Every application logger applies a redaction filter that replaces email-shaped values in the message and in every structured field, under any field name, before the record is emitted.
3. Tests run the email worker task's success path and its failure path with a known recipient address, and assert that the captured log output does not contain that address. A test passes an email address through a structured field with an arbitrary name and asserts that the emitted record does not contain it.
4. No credential or secret appears verbatim in any operational or proxy log, on success paths and on error paths (an unhandled exception in the application, an upstream error at the reverse proxy). Credentials and secrets are: activation tokens, anonymized-data retrieval codes, session tokens, CSRF tokens, passwords, API keys (including the object-store access and secret keys) and the encryption keys (the at-rest encryption key, its retired keys and the object-store server-side encryption key). Operational and proxy logs are: the application, worker and scheduler logs; the access and error logs of the reverse proxy; the access and error logs of the frontend container; and every URL, path, query string and Referer value recorded in any of them. The criterion is met when, after the activation flow is exercised with a known activation token through the API path, the page path and the e-mail link's query string, including one request that ends in an unhandled exception and one that ends in a reverse-proxy upstream error, and authenticated requests are made with a known session token and CSRF token, none of those known values appears in any of the logs listed above.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-004 "GDPR compliance" and NFR-007 "Cybersecurity". Satisfies RR-001 "Lawful basis and data minimization for processing health data", RR-002 "Right to erasure of personal data" and RR-003 "Security of processing: encryption and access control". Related: SR-033 (account activation, which issues the activation token) and SR-023 AC 9 (credentials and secrets in the audit trail).

## Risk Analysis

### Rationale

GDPR data minimization (RR-001) and the right to erasure (RR-002) can only hold if personal data stays inside the stores the application controls. A log copy defeats both. A credential in a log is a replayable copy outside its controlled store (RR-003, NFR-007).

### Potential Risks

- Personal data persists in log archives after an erasure request, or reaches people with access to the logs but not to the application (RISK-008).
- A log reader replays an activation token from a log and takes over a pending account, then reads PHI or writes clinical entries in its owner's name (RISK-005, PRB-068).

### Control Measures

- Identifiers instead of personal data at the source (AC 1); a redaction filter as a safety net (AC 2); tests that fail if an address reaches the log (AC 3); no credential or secret in any operational or proxy log, checked with known values on success and error paths (AC 4, implemented by TASK-206).
- The TS is written at the Build stage.

## Version history

- 1.0 (2026-10-31) — Initial creation (CR-004, GitHub sancharly/medhub#27), from PRB-011.
- 1.1 (2026-11-07) — Added AC 4: no credential or secret, including the activation token, appears in any operational or proxy log (human decision in chat, 2026-11-07; from PRB-068, CR-004). Title, Summary, Description and Risk Analysis extended to match; added links `derives_from` NFR-007, `satisfies` RR-003, `mitigates` RISK-005, `relates_to` SR-033 and SR-023. Returned to `in_review`; the 1.0 approval no longer applies.
