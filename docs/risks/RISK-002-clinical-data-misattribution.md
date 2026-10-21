---
id: RISK-002
type: risk
title: Clinical information attributed to the wrong patient or author
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
hazard: A clinical entry, attachment or image associated with the wrong patient or the wrong author.
cause: An identifier handling defect (a wrong foreign key after erasure re-keying, an attachment listed from a stale cache instead of the server, `authorName` populated from the viewer rather than the author) → the UI presents the entry under a patient or author it does not belong to → a clinician reads it as that patient's history.
harm: Wrong or delayed treatment based on incorrect history; in the worst case a harmful intervention. Serious injury is conceivable but not a direct consequence of the software alone.
severity_initial: 4
probability_initial: 3
severity_residual: 4
probability_residual: 2
acceptability: alarp
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 06371b7d07335afed4262aa306fd695ff10f7e5aeff569ba91b2e6b6ef1d5d13
approval_note: self-approved
links:
  - target: SOUP-008
    relation: relates_to
  - target: SOUP-020
    relation: relates_to
  - target: SOUP-016
    relation: relates_to
tags:
  - hazard:data-integrity
  - class:B
---

# RISK-002 — Clinical information attributed to the wrong patient or author

## Hazard

A clinical entry, attachment or image associated with the wrong patient or the wrong author.

## Sequence of events

An identifier handling defect (a wrong foreign key after erasure re-keying, an attachment listed from a stale cache instead of the server, `authorName` populated from the viewer rather than the author) → the UI presents the entry under a patient or author it does not belong to → a clinician reads it as that patient's history.

## Hazardous situation

A clinician makes a care decision using another patient's clinical information, or attributes a finding to the wrong colleague.

## Harm

Wrong or delayed treatment based on incorrect history; in the worst case a harmful intervention. Serious injury is conceivable but not a direct consequence of the software alone.

## Software items involved

SI-PERSIST (`U-PER-Models`, `U-PER-Migrations`), SI-CLINICAL (`U-CLIN-EntryCrud`), SI-ATTACH, SI-IDENTITY (erasure re-keying), SI-FE-CORE (cache).

## Initial risk

Severity 4 — Serious (can contribute to a wrong clinical decision) — × probability 3 (Occasional) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Unique account identity and immutable record identifiers | Design | SR-003, SR-004 | TS-003 |
| Required fields and server-side validation on clinical entry creation | Design | SR-012 | TR-001, TS-007 |
| FHIR-aligned model with explicit subject/author references | Design | SR-021 | TS-008 |
| Attachments listed from the authoritative endpoint, not client cache | Design | SR-013, TASK-066 | TR-001, TS-007 |
| Erasure re-keys clinical data into the anonymized dataset instead of dropping or mis-linking it | Protective | SR-024, TASK-116 | TR-001, TS-004 |
| Real-database integration tests over repositories, not mock-only | Protective | TASK-110 | none yet |

## Residual risk

Severity 4 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **alarp**, derived from `risk_matrix`. Residual stays ALARP: severity cannot be reduced by software controls, so the record needs explicit human acceptance with the benefit/risk argument. TASK-116 (clinical data re-keying) is still `draft` and is the main open contributor.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

Software controls cannot lower the severity: a misattributed entry can always reach a clinical decision, and the clinician remains the last safeguard. Probability is already reduced to Remote by server-assigned identities, author taken from the session, and attachments read from the authoritative endpoint; reducing it further would need an independent second check of patient identity on every read, which the clinical workflow cannot carry. The benefit — one consistent, attributed record instead of fragmented paper and e-mail — outweighs the residual risk. Open contributor: TASK-116 (re-keying on erasure).

## Risks introduced by controls

Stricter referential constraints can reject a legitimate write and delay documentation — covered by RISK-007 (availability).
