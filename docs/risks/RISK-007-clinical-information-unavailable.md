---
id: RISK-007
type: risk
title: Clinical information unavailable when needed
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
hazard: The application, its database, its object storage or its workers unavailable, or attachments unreadable.
cause: Single-host outage, database or MinIO failure, exhausted connection pool from a session leak, a missing storage SDK (PRB-002), or an encryption key rotation that makes old rows unreadable → the clinician cannot open the record → they proceed without it or wait.
harm: Delayed care; decisions made without available history. No direct physical harm from the software itself.
severity_initial: 3
probability_initial: 2
severity_residual: 3
probability_residual: 2
acceptability: alarp
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: a04f251d018f44c499956c9da605935fc87df23748f4baed0bb1b46698ac90db
approval_note: self-approved
links:
  - target: SOUP-020
    relation: relates_to
  - target: SOUP-022
    relation: relates_to
  - target: SOUP-019
    relation: relates_to
  - target: SOUP-014
    relation: relates_to
  - target: SOUP-021
    relation: relates_to
tags:
  - hazard:availability
  - class:B
---

# RISK-007 — Clinical information unavailable when needed

## Hazard

The application, its database, its object storage or its workers unavailable, or attachments unreadable.

## Sequence of events

Single-host outage, database or MinIO failure, exhausted connection pool from a session leak, a missing storage SDK (PRB-002), or an encryption key rotation that makes old rows unreadable → the clinician cannot open the record → they proceed without it or wait.

## Hazardous situation

A clinician needs clinical information that the system cannot deliver.

## Harm

Delayed care; decisions made without available history. No direct physical harm from the software itself.

## Software items involved

SI-API, SI-PERSIST, SI-ATTACH, SI-WORKER, infrastructure (single-host Compose, ADR-0010).

## Initial risk

Severity 3 — Moderate (care delayed) — × probability 2 (Remote) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Documented backup, monitoring and deployment procedure | Protective | RR-011, TASK-115 | none yet — release gate |
| Performance budgets so routine operations stay usable | Design | SR-026 | none yet |
| Worker retries with backoff and no silent enqueue failures | Protective | TASK-141 | none yet |
| Object storage dependency declared and verified at startup | Design | PRB-002 resolution | none yet |
| Key identifier in the ciphertext envelope so rotation cannot orphan rows | Design | SR-022, PRB-004 resolution | TR-001, TS-008 |

## Residual risk

Severity 3 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **alarp**, derived from `risk_matrix`. Single-host Compose with no high availability is a deliberate MVP decision (arc42 §11, ADR-0010); the residual therefore stays ALARP and needs an explicit human acceptance for each release, with the argument that MedHub is not the only route to the information.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

Single-host deployment without high availability is a documented MVP decision (ADR-0010, arc42 §11): the product is containerized so HA can be added without redesign. Unavailability delays access but does not corrupt or misattribute information, and the institution's own systems remain available. The benefit of shipping the MVP outweighs this residual for the initial deployment scale; it must be re-accepted at every release.

## Risks introduced by controls

None identified.
