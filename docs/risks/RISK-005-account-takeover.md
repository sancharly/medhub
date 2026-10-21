---
id: "RISK-005"
type: risk
title: "Account takeover leading to disclosure or falsified clinical records"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
links:
  - target: "SOUP-012"
    relation: relates_to
  - target: "SOUP-021"
    relation: relates_to
  - target: "SOUP-013"
    relation: relates_to
  - target: "SOUP-003"
    relation: relates_to
  - target: "SOUP-024"
    relation: relates_to
tags: ["hazard:security", "class:B"]
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

| Severity | Probability (P2) | Risk level (per ADD-003) |
|---|---|---|
| 3 — Moderate (wrong data or disclosure) | 2 — Remote | 6 — ALARP (6) |

P1 (probability of the software fault itself) is taken as 1 per ADD-003: the fault is assumed to occur.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Argon2id hashing with timing parity, and a password complexity policy | Design | SR-025 | TS (Review stage) |
| Account lockout after failed attempts, wired into the login path | Protective | SR-029, TASK-118, TASK-140 | TS (Review stage) |
| Opaque server-side sessions with absolute and idle expiry, revocable | Design | SR-030 | TS (Review stage) |
| CSRF enforcement on every mutating route, security headers, TLS/HSTS | Design | SR-031, SR-001 | TS (Review stage) |
| Audit trail of security-relevant events for detection | Protective | SR-023 | TS (Review stage) |

## Residual risk

| Severity | Probability (P2) | Risk level | Acceptable? | Decided by / date |
|---|---|---|---|---|
| 3 — Moderate (wrong data or disclosure) | 1 — Improbable | 3 — Acceptable (3) | **pending human decision** | — |

App-wide CSRF enforcement and the lockout wiring are in place (TASK-128, TASK-118). Residual still
depends on PRB-003 (exemptions matched by prefix), PRB-018 (lockout parameter made required) and
PRB-023 (non-atomic session-cap eviction) being closed.

## Risks introduced by controls

Aggressive lockout enables a denial-of-service against a known account — RISK-007; mitigated by administrator-initiated unlock.
