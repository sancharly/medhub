---
id: "RISK-006"
type: risk
title: "Audit trail incomplete, so a wrong disclosure or entry goes undetected"
status: in_review
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
hazard: "Security-relevant or clinical-data events not recorded, or recorded without the information needed to reconstruct them."
cause: "A code path bypasses `AuditService`, the client IP is not captured, the scrub drops needed context, or the log store is writable → an incident cannot be reconstructed → a wrong disclosure or falsified entry is never noticed or corrected."
harm: "Indirect: the harms of RISK-001/002/005 persist uncorrected, and the legal obligation to notify cannot be met."
severity_initial: 2
probability_initial: 3
severity_residual: 2
probability_residual: 2
acceptability: acceptable
links:
  - target: "SOUP-008"
    relation: relates_to
  - target: "SOUP-020"
    relation: relates_to
tags: ["hazard:detectability", "class:B"]
---

# RISK-006 — Audit trail incomplete, so a wrong disclosure or entry goes undetected

## Hazard

Security-relevant or clinical-data events not recorded, or recorded without the information needed to reconstruct them.

## Sequence of events

A code path bypasses `AuditService`, the client IP is not captured, the scrub drops needed context, or the log store is writable → an incident cannot be reconstructed → a wrong disclosure or falsified entry is never noticed or corrected.

## Hazardous situation

A patient's data has been wrongly disclosed or altered and nobody can establish what happened.

## Harm

Indirect: the harms of RISK-001/002/005 persist uncorrected, and the legal obligation to notify cannot be met.

## Software items involved

SI-AUDIT (`AuditService`), SI-API, SI-PERSIST.

## Initial risk

Severity 2 — Minor (indirect: delays correction) — × probability 3 (Occasional) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Audit every authentication, authorization and clinical-data event | Design | SR-023 | TS-009 |
| Append-only storage with credential scrubbing | Design | SR-023, SR-022 | TR-001, TS-008, TS-009 |
| Capture the client IP in authz and consent audit events | Protective | TASK-137 | none yet |
| Tests asserting an audit row for every security-relevant action | Protective | TASK-113 | none yet |

## Residual risk

Severity 2 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **acceptable**, derived from `risk_matrix`. Append-only is enforced by convention rather than by the database today (PRB-005), the source IP is
missing from authorization events (PRB-010, TASK-137, still `draft`), and log correlation is
unavailable (PRB-032).

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

Richer audit content increases the PHI footprint of the logs — RISK-008 covers log-side PII, tracked by TASK-138.
