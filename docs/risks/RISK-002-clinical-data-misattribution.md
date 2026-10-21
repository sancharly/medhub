---
id: "RISK-002"
type: risk
title: "Clinical information attributed to the wrong patient or author"
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
  - target: "SOUP-016"
    relation: relates_to
tags: ["hazard:data-integrity", "class:B"]
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

| Severity | Probability (P2) | Risk level (per ADD-003) |
|---|---|---|
| 4 — Serious (can contribute to a wrong clinical decision) | 3 — Occasional | 12 — ALARP (12) |

P1 (probability of the software fault itself) is taken as 1 per ADD-003: the fault is assumed to occur.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Unique account identity and immutable record identifiers | Design | SR-003, SR-004 | TS (Review stage) |
| Required fields and server-side validation on clinical entry creation | Design | SR-012 | TS (Review stage) |
| FHIR-aligned model with explicit subject/author references | Design | SR-021 | TS (Review stage) |
| Attachments listed from the authoritative endpoint, not client cache | Design | SR-013, TASK-066 | TS (Review stage) |
| Erasure re-keys clinical data into the anonymized dataset instead of dropping or mis-linking it | Protective | SR-024, TASK-116 | TS (Review stage) |
| Real-database integration tests over repositories, not mock-only | Protective | TASK-110 | TS (Review stage) |

## Residual risk

| Severity | Probability (P2) | Risk level | Acceptable? | Decided by / date |
|---|---|---|---|---|
| 4 — Serious (can contribute to a wrong clinical decision) | 2 — Remote | 8 — ALARP (8) | **pending human decision** | — |

Residual stays ALARP: severity cannot be reduced by software controls, so the record needs explicit human acceptance with the benefit/risk argument. TASK-116 (clinical data re-keying) is still `draft` and is the main open contributor.

## Risks introduced by controls

Stricter referential constraints can reject a legitimate write and delay documentation — covered by RISK-007 (availability).
