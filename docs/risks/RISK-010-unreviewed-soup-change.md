---
id: "RISK-010"
type: risk
title: "Unreviewed SOUP change weakens a verified risk control"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
links:
  - target: "SOUP-001"
    relation: relates_to
  - target: "SOUP-002"
    relation: relates_to
  - target: "SOUP-003"
    relation: relates_to
  - target: "SOUP-004"
    relation: relates_to
  - target: "SOUP-005"
    relation: relates_to
  - target: "SOUP-006"
    relation: relates_to
  - target: "SOUP-007"
    relation: relates_to
  - target: "SOUP-008"
    relation: relates_to
  - target: "SOUP-009"
    relation: relates_to
  - target: "SOUP-010"
    relation: relates_to
  - target: "SOUP-011"
    relation: relates_to
  - target: "SOUP-012"
    relation: relates_to
  - target: "SOUP-013"
    relation: relates_to
  - target: "SOUP-014"
    relation: relates_to
  - target: "SOUP-015"
    relation: relates_to
  - target: "SOUP-016"
    relation: relates_to
  - target: "SOUP-017"
    relation: relates_to
  - target: "SOUP-018"
    relation: relates_to
  - target: "SOUP-019"
    relation: relates_to
  - target: "SOUP-020"
    relation: relates_to
  - target: "SOUP-021"
    relation: relates_to
  - target: "SOUP-022"
    relation: relates_to
  - target: "SOUP-023"
    relation: relates_to
  - target: "SOUP-024"
    relation: relates_to
  - target: "SOUP-025"
    relation: relates_to
  - target: "SOUP-026"
    relation: relates_to
  - target: "SOUP-027"
    relation: relates_to
  - target: "SOUP-028"
    relation: relates_to
  - target: "SOUP-029"
    relation: relates_to
  - target: "SOUP-030"
    relation: relates_to
  - target: "SOUP-031"
    relation: relates_to
  - target: "SOUP-032"
    relation: relates_to
  - target: "SOUP-033"
    relation: relates_to
  - target: "SOUP-034"
    relation: relates_to
  - target: "SOUP-035"
    relation: relates_to
tags: ["hazard:soup", "class:B"]
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

All items; specifically nginx, MinIO, cryptography, argon2-cffi, SQLAlchemy, Redis, pydicom (see ADD-004).

## Initial risk

| Severity | Probability (P2) | Risk level (per ADD-003) |
|---|---|---|
| 3 — Moderate (a control silently stops working) | 2 — Remote | 6 — ALARP (6) |

P1 (probability of the software fault itself) is taken as 1 per ADD-003: the fault is assumed to occur.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| SOUP list with exact versions, required functions and required HW/SW | Design | SR-028, ADD-004 | TR (Release stage) |
| Every image and dependency pinned to an immutable version | Design | PRB-001 resolution | TR (Release stage) |
| Anomaly and advisory review per version, at least yearly and before release | Protective | TASK-154 | TR (Release stage) |
| Tests asserting the security headers, encryption and hashing behaviour | Protective | SR-001, SR-022, SR-025 | TS (Review stage) |

## Residual risk

| Severity | Probability (P2) | Risk level | Acceptable? | Decided by / date |
|---|---|---|---|---|
| 3 — Moderate (a control silently stops working) | 1 — Improbable | 3 — Acceptable (3) | **pending human decision** | — |

Residual assumes PRB-001 is closed and TASK-154 has been run at least once. Neither is true today, so the current probability is the initial one.

## Risks introduced by controls

Pinning delays security patches; the monitoring cadence in ADD-004 is the counterweight.
