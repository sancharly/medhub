---
id: "RISK-008"
type: risk
title: "Personal data retained, copied or erased contrary to its lawful basis"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
links:
  - target: "SOUP-014"
    relation: relates_to
tags: ["hazard:privacy", "class:B"]
---

# RISK-008 — Personal data retained, copied or erased contrary to its lawful basis

## Hazard

PHI or PII living outside the controlled lifecycle: retained past its basis, copied into logs, or erased while still clinically or legally needed.

## Sequence of events

Worker logs write email addresses as structured fields, a retention sweep fails silently, or an erasure drops clinical data instead of anonymizing it → personal data exists in an uncontrolled copy, or required data is gone → the obligation in SR-024 and the GDPR requirement cannot be met.

## Hazardous situation

Personal data is processed outside the erasure and retention machinery.

## Harm

Privacy harm to the patient and a regulatory breach; in the erase-too-much direction, loss of clinical history.

## Software items involved

SI-WORKER (retention, erasure, notifications), SI-IDENTITY (`U-ID-Erasure`), SI-AUDIT, log pipeline.

## Initial risk

| Severity | Probability (P2) | Risk level (per ADD-003) |
|---|---|---|
| 2 — Minor (privacy harm) | 3 — Occasional | 6 — ALARP (6) |

P1 (probability of the software fault itself) is taken as 1 per ADD-003: the fault is assumed to occur.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Erasure and retention implemented as auditable, retriable jobs | Design | SR-024, TASK-036, TASK-141 | TS (Review stage) |
| Clinical data anonymized and re-keyed rather than dropped | Design | SR-024, TASK-116 | TS (Review stage) |
| PII scrubbing for worker and notification logs | Protective | TASK-138 | TS (Review stage) |
| Encryption at rest so residual copies are unreadable without keys | Protective | SR-022 | TS (Review stage) |

## Residual risk

| Severity | Probability (P2) | Risk level | Acceptable? | Decided by / date |
|---|---|---|---|---|
| 2 — Minor (privacy harm) | 2 — Remote | 4 — Acceptable (4) | **pending human decision** | — |

TASK-116, TASK-138 and TASK-141 are all still `draft`; until they land the log-side copy of PII is real, not theoretical.

## Risks introduced by controls

Scrubbing can remove context needed to diagnose an incident — balanced against RISK-006.
