---
id: "RISK-004"
type: risk
title: "Legitimate clinical access wrongly denied or delayed"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["hazard:denial-of-care", "class:B"]
---

# RISK-004 — Legitimate clinical access wrongly denied or delayed

## Hazard

A clinician with a legitimate care relationship cannot reach the patient's clinical data when needed.

## Sequence of events

An over-restrictive or mis-scoped consent evaluation (a declined appointment revoking a grant from another source, a per-source union computed wrongly, a module guard denying an enabled module) → the API denies the request → the clinician proceeds without the available history.

## Hazardous situation

A clinician decides without information that exists in the system.

## Harm

Care based on incomplete information, or delayed care while access is sorted out; recoverable in most workflows.

## Software items involved

SI-AUTHZ (`U-AUTHZ-Consent`, `U-AUTHZ-ApptVisibility`, `U-AUTHZ-ModuleGuard`), SI-APPT, SI-GROUPS.

## Initial risk

| Severity | Probability (P2) | Risk level (per ADD-003) |
|---|---|---|
| 3 — Moderate (care delayed) | 3 — Occasional | 9 — ALARP (9) |

P1 (probability of the software fault itself) is taken as 1 per ADD-003: the fault is assumed to occur.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Grants modelled per source and combined as a union, so one revocation cannot strip another grant | Design | SR-008, SR-036 | TS (Review stage) |
| Explicit tests for the documented consent cases A/B/C | Protective | SR-036, TASK-113 | TS (Review stage) |
| Denials are audited with the reason, so a wrong denial is diagnosable | Protective | SR-023 | TS (Review stage) |
| Patient-facing consent UI shows exactly who has access | Information for safety | SR-008 | TS (Review stage) |

## Residual risk

| Severity | Probability (P2) | Risk level | Acceptable? | Decided by / date |
|---|---|---|---|---|
| 3 — Moderate (care delayed) | 2 — Remote | 6 — ALARP (6) | **pending human decision** | — |

Residual ALARP. MedHub is not the only route to clinical information (the treating institution's own records remain), which is what keeps probability and severity from being higher.

## Risks introduced by controls

Loosening consent scope to avoid denials would raise RISK-001; the balance is held by the per-source union model.
