---
id: "RISK-006"
type: risk
title: "Audit trail incomplete, so a wrong disclosure or entry goes undetected"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
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

| Severity | Probability (P2) | Risk level (per ADD-003) |
|---|---|---|
| 2 — Minor (indirect: delays correction) | 3 — Occasional | 6 — ALARP (6) |

P1 (probability of the software fault itself) is taken as 1 per ADD-003: the fault is assumed to occur.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Audit every authentication, authorization and clinical-data event | Design | SR-023 | TS (Review stage) |
| Append-only storage with credential scrubbing | Design | SR-023, SR-022 | TS (Review stage) |
| Capture the client IP in authz and consent audit events | Protective | TASK-137 | TS (Review stage) |
| Tests asserting an audit row for every security-relevant action | Protective | TASK-113 | TS (Review stage) |

## Residual risk

| Severity | Probability (P2) | Risk level | Acceptable? | Decided by / date |
|---|---|---|---|---|
| 2 — Minor (indirect: delays correction) | 2 — Remote | 4 — Acceptable (4) | **pending human decision** | — |

Append-only is enforced by convention rather than by the database today (PRB-005), the source IP is
missing from authorization events (PRB-010, TASK-137, still `draft`), and log correlation is
unavailable (PRB-032).

## Risks introduced by controls

Richer audit content increases the PHI footprint of the logs — RISK-008 covers log-side PII, tracked by TASK-138.
