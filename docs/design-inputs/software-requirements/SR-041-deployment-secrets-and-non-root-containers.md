---
id: "SR-041"
type: software-requirement
title: "Deployment secrets and non-root runtime containers"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-31"
approval_note: self-approved at the ship-feature spec gate (sancharly/medhub#27)
links:
  - target: "RR-003"
    relation: satisfies
  - target: "NFR-007"
    relation: derives_from
  - target: "RISK-001"
    relation: mitigates
  - target: "RISK-005"
    relation: mitigates
  - target: "RISK-011"
    relation: mitigates
tags: ["control:design", "control:protective", "issue:sancharly/medhub#27"]
---

## Summary

The deployment shall start only with operator-supplied, non-default secrets, shall keep the field-encryption key separate from the object-store encryption key, and shall run every container image MedHub builds as a non-root user.

## Description

This requirement extends to the whole deployment what SR-040 requires of the object store's credentials. A deployment that boots with a known value (`changeme`, a `change-me-…` placeholder) runs with a credential any reader of the repository knows, and a process that runs as root turns a container escape into control of the host and of all PHI it can reach (PRB-007). The deployment includes the Compose topology, the environment template, the deployment guide and the images MedHub builds (backend, worker, frontend).

A **secret setting** is any setting listed as a secret in the deployment guide. At minimum: the database password (`POSTGRES_PASSWORD` and the password inside `DATABASE_URL`), `SMTP_PASSWORD` when SMTP authentication is configured, `AT_REST_ENCRYPTION_KEY`, the object-store SSE key, and the object-store access and secret keys (already covered by SR-040 AC 2).

§5.2.2 categories: e (security), h (installation), j (IT-network aspects).

## Acceptance Criteria

1. Every container image MedHub builds runs its main process as a user other than root (UID ≠ 0). It is checked on the built image configuration and on the running process of a started stack.
2. The deployment definition supplies no default value for any secret setting. Bring-up fails with a message naming the setting when a secret setting is unset or empty.
3. The backend and the worker refuse to start when a secret setting equals a known placeholder value, ignoring case: `changeme`, `change-me`, any value that starts with `change-me-to-`, or any value the environment template has ever shipped. `AT_REST_ENCRYPTION_KEY` is also refused when it does not decode to exactly 32 bytes. The error names the setting and never prints the value.
4. The environment template contains no value for any secret setting, and the deployment guide states how to generate each one.
5. The field-level encryption key and the object-store SSE key are separate settings. The deployment refuses to start when the two hold the same value. Attachments stored before the separation remain readable after it.
6. AC 1 to AC 5 are verified against the deployment definition, the built images and a started stack, not against documentation alone.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-007 "Cybersecurity". Satisfies RR-003 "Security of processing: encryption and access control" (credential and key material managed so that its compromise does not expose stored data).

## Risk Analysis

### Rationale

Known default credentials and root processes are the security misconfigurations the 2026-07 audit found (PRB-007). RR-003 requires that credential and key material be managed so that compromising one does not expose stored data. A shared key does the opposite: a single key unlocks both the encrypted fields and the stored attachments, and losing it makes both unreadable (CR-002 D-6, SOUP-036 F-4, RISK-011).

### Potential Risks

- A deployment boots with a known credential: unauthorized disclosure or modification of PHI (RISK-001), or account takeover through the database or mail relay (RISK-005).
- A container escape from a root process gives an attacker the host (RISK-001).
- A shared key widens what a compromise or a loss of that key reaches (RISK-011). Migrating attachments to a new SSE key incorrectly makes them unreadable (RISK-007, considered by RISK-011).

### Control Measures

- Required settings with no default, a start-up refusal of placeholder values, and an empty environment template (AC 2 to AC 4).
- A non-root `USER` in every image MedHub builds (AC 1).
- Separate keys, with a rehearsed migration of existing attachments, so that no stored object becomes unreadable (AC 5).
- Verification on a started stack (AC 6). The TS is written at the Build stage.

## Version history

- 1.0 (2026-10-31) — Initial creation (CR-004, GitHub sancharly/medhub#27). Covers what PRB-007 leaves open after CR-002: root containers, the other default secrets, and separating the field-encryption key from the object-store SSE key.
