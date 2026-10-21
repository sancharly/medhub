---
id: RISK-008
type: risk
title: Personal data retained, copied or erased contrary to its lawful basis
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
hazard: "PHI or PII living outside the controlled lifecycle: retained past its basis, copied into logs, or erased while still clinically or legally needed."
cause: Worker logs write email addresses as structured fields, a retention sweep fails silently, or an erasure drops clinical data instead of anonymizing it → personal data exists in an uncontrolled copy, or required data is gone → the obligation in SR-024 and the GDPR requirement cannot be met.
harm: Privacy harm to the patient and a regulatory breach; in the erase-too-much direction, loss of clinical history.
severity_initial: 2
probability_initial: 3
severity_residual: 2
probability_residual: 2
acceptability: acceptable
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 7846d5df679855e214f9ab11c073b018a274038d6f918f46762986707c5af895
approval_note: self-approved
links:
  - target: SOUP-014
    relation: relates_to
tags:
  - hazard:privacy
  - class:B
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

Severity 2 — Minor (privacy harm) — × probability 3 (Occasional) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Erasure and retention implemented as auditable, retriable jobs | Design | SR-024, TASK-036, TASK-141 | TR-001, TS-004 |
| Clinical data anonymized and re-keyed rather than dropped | Design | SR-024, TASK-116 | TR-001, TS-004 |
| PII scrubbing for worker and notification logs | Protective | TASK-138 | none yet |
| Encryption at rest so residual copies are unreadable without keys | Protective | SR-022 | TR-001, TS-008 |

## Residual risk

Severity 2 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **acceptable**, derived from `risk_matrix`. TASK-116, TASK-138 and TASK-141 are all still `draft`; until they land the log-side copy of PII is real, not theoretical.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

Scrubbing can remove context needed to diagnose an incident — balanced against RISK-006.
