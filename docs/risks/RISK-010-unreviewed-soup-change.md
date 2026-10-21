---
id: RISK-010
type: risk
title: Unreviewed SOUP change weakens a verified risk control
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
hazard: A third-party component changing behaviour in a way that disables or weakens a control that a risk record depends on.
cause: A floating image tag (`nginx:alpine`, `minio/minio:latest`) or an unreviewed library upgrade pulls a new version → TLS/HSTS headers, server-side encryption, password hashing or query parameterization behave differently → a control that a RISK record claims is verified no longer holds, with no test failing.
harm: "Indirect: re-enables the harms of RISK-001, RISK-005 or RISK-008."
severity_initial: 3
probability_initial: 2
severity_residual: 3
probability_residual: 1
acceptability: acceptable
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 7a753189ff00f569b395ab3bcffde793272f70b3a032d5bf4b6ed91d73912dad
approval_note: self-approved
links:
  - target: SOUP-001
    relation: relates_to
  - target: SOUP-002
    relation: relates_to
  - target: SOUP-003
    relation: relates_to
  - target: SOUP-004
    relation: relates_to
  - target: SOUP-005
    relation: relates_to
  - target: SOUP-006
    relation: relates_to
  - target: SOUP-007
    relation: relates_to
  - target: SOUP-008
    relation: relates_to
  - target: SOUP-009
    relation: relates_to
  - target: SOUP-010
    relation: relates_to
  - target: SOUP-011
    relation: relates_to
  - target: SOUP-012
    relation: relates_to
  - target: SOUP-013
    relation: relates_to
  - target: SOUP-014
    relation: relates_to
  - target: SOUP-015
    relation: relates_to
  - target: SOUP-016
    relation: relates_to
  - target: SOUP-017
    relation: relates_to
  - target: SOUP-018
    relation: relates_to
  - target: SOUP-019
    relation: relates_to
  - target: SOUP-020
    relation: relates_to
  - target: SOUP-021
    relation: relates_to
  - target: SOUP-022
    relation: relates_to
  - target: SOUP-023
    relation: relates_to
  - target: SOUP-024
    relation: relates_to
  - target: SOUP-025
    relation: relates_to
  - target: SOUP-026
    relation: relates_to
  - target: SOUP-027
    relation: relates_to
  - target: SOUP-028
    relation: relates_to
  - target: SOUP-029
    relation: relates_to
  - target: SOUP-030
    relation: relates_to
  - target: SOUP-031
    relation: relates_to
  - target: SOUP-032
    relation: relates_to
  - target: SOUP-033
    relation: relates_to
  - target: SOUP-034
    relation: relates_to
  - target: SOUP-035
    relation: relates_to
tags:
  - hazard:soup
  - class:B
---

# RISK-010 — Unreviewed SOUP change weakens a verified risk control

## Hazard

A third-party component changing behaviour in a way that disables or weakens a control that a risk record depends on.

## Sequence of events

A floating image tag (`nginx:alpine`, `minio/minio:latest`) or an unreviewed library upgrade pulls a new version → TLS/HSTS headers, server-side encryption, password hashing or query parameterization behave differently → a control that a RISK record claims is verified no longer holds, with no test failing.

## Hazardous situation

A risk control believed to be in place is not, and nobody knows.

## Harm

Indirect: re-enables the harms of RISK-001, RISK-005 or RISK-008.

## Software items involved

All items; specifically nginx, MinIO, cryptography, argon2-cffi, SQLAlchemy, Redis, pydicom (SOUP-001..035).

## Initial risk

Severity 3 — Moderate (a control silently stops working) — × probability 2 (Remote) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| SOUP list with exact versions, required functions and required HW/SW | Design | RR-011, SOUP-001..035 | none yet — release gate (TASK-154) |
| Every image and dependency pinned to an immutable version | Design | PRB-001 resolution | none yet |
| Anomaly and advisory review per version, at least yearly and before release | Protective | TASK-154 | none yet |
| Tests asserting the security headers, encryption and hashing behaviour | Protective | SR-001, SR-022, SR-025 | TR-001, TS-001, TS-008, TS-011 |

## Residual risk

Severity 3 (unchanged — controls reduce probability, not severity) × probability 1
(Improbable) → **acceptable**, derived from `risk_matrix`. Residual assumes PRB-001 is closed and TASK-154 has been run at least once. Neither is true today, so the current probability is the initial one.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

Pinning delays security patches; the monitoring cadence in PLAN-002 is the counterweight.
