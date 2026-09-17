---
id: "RISK-007"
type: risk
title: "Clinical information unavailable when needed"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["hazard:availability", "class:B"]
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

| Severity | Probability (P2) | Risk level (per ADD-003) |
|---|---|---|
| 3 — Moderate (care delayed) | 2 — Remote | 6 — ALARP (6) |

P1 (probability of the software fault itself) is taken as 1 per ADD-003: the fault is assumed to occur.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Documented backup, monitoring and deployment procedure | Protective | SR-028, TASK-115 | TR (Release stage) |
| Performance budgets so routine operations stay usable | Design | SR-026 | TS (Release stage) |
| Worker retries with backoff and no silent enqueue failures | Protective | TASK-141 | TS (Review stage) |
| Object storage dependency declared and verified at startup | Design | PRB-002 resolution | TS (Review stage) |
| Key identifier in the ciphertext envelope so rotation cannot orphan rows | Design | SR-022, PRB-004 resolution | TS (Review stage) |

## Residual risk

| Severity | Probability (P2) | Risk level | Acceptable? | Decided by / date |
|---|---|---|---|---|
| 3 — Moderate (care delayed) | 2 — Remote | 6 — ALARP (6) | **pending human decision** | — |

Single-host Compose with no high availability is a deliberate MVP decision (arc42 §11, ADR-0010); the residual therefore stays ALARP and needs an explicit human acceptance for each release, with the argument that MedHub is not the only route to the information.

## Risks introduced by controls

None identified.
