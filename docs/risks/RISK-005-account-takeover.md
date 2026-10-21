---
id: RISK-005
type: risk
title: Account takeover leading to disclosure or falsified clinical records
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
hazard: "An attacker acting as a legitimate user: reading PHI, or writing clinical entries as a clinician."
cause: Credential stuffing, brute force, a stolen session token, or a CSRF-able mutating endpoint → the attacker authenticates or rides an authenticated session → they read or write clinical data under someone else's identity.
harm: Wrong clinical decisions from falsified data, plus privacy harm. Recoverable if detected via the audit trail.
severity_initial: 3
probability_initial: 2
severity_residual: 3
probability_residual: 1
acceptability: acceptable
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 90c61d56ba38af469a3311448b8c97945aa5f45dc174b1495fa4a699efbca1d3
approval_note: self-approved
links:
  - target: SOUP-012
    relation: relates_to
  - target: SOUP-021
    relation: relates_to
  - target: SOUP-013
    relation: relates_to
  - target: SOUP-003
    relation: relates_to
  - target: SOUP-024
    relation: relates_to
tags:
  - hazard:security
  - class:B
---

# RISK-005 — Account takeover leading to disclosure or falsified clinical records

## Hazard

An attacker acting as a legitimate user: reading PHI, or writing clinical entries as a clinician.

## Sequence of events

Credential stuffing, brute force, a stolen session token, or a CSRF-able mutating endpoint → the attacker authenticates or rides an authenticated session → they read or write clinical data under someone else's identity.

## Hazardous situation

Clinical records contain entries not made by their apparent author, or PHI has been exfiltrated.

## Harm

Wrong clinical decisions from falsified data, plus privacy harm. Recoverable if detected via the audit trail.

## Software items involved

SI-AUTH (`U-AUTH-Login`, session store), SI-API (CSRF, security headers), SI-FE-AUTH.

## Initial risk

Severity 3 — Moderate (wrong data or disclosure) — × probability 2 (Remote) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Argon2id hashing with timing parity, and a password complexity policy | Design | SR-025 | TR-001, TS-001 |
| Account lockout after failed attempts, wired into the login path | Protective | SR-029, TASK-118, TASK-140 | TR-001, TS-001 |
| Opaque server-side sessions with absolute and idle expiry, revocable | Design | SR-030 | TR-001, TS-001 |
| CSRF enforcement on every mutating route, security headers, TLS/HSTS | Design | SR-031, SR-001 | TR-001, TS-008, TS-011 |
| Audit trail of security-relevant events for detection | Protective | SR-023 | TS-009 |

## Residual risk

Severity 3 (unchanged — controls reduce probability, not severity) × probability 1
(Improbable) → **acceptable**, derived from `risk_matrix`. App-wide CSRF enforcement and the lockout wiring are in place (TASK-128, TASK-118). Residual still
depends on PRB-003 (exemptions matched by prefix), PRB-018 (lockout parameter made required) and
PRB-023 (non-atomic session-cap eviction) being closed.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

Aggressive lockout enables a denial-of-service against a known account — RISK-007; mitigated by administrator-initiated unlock.
