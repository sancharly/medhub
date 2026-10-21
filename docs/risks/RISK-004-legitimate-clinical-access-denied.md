---
id: RISK-004
type: risk
title: Legitimate clinical access wrongly denied or delayed
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
hazard: A clinician with a legitimate care relationship cannot reach the patient's clinical data when needed.
cause: An over-restrictive or mis-scoped consent evaluation (a declined appointment revoking a grant from another source, a per-source union computed wrongly, a module guard denying an enabled module) → the API denies the request → the clinician proceeds without the available history.
harm: Care based on incomplete information, or delayed care while access is sorted out; recoverable in most workflows.
severity_initial: 3
probability_initial: 3
severity_residual: 3
probability_residual: 2
acceptability: alarp
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 161eec8d4b01d48eb0572564e8aa490dd878c6fcc3f393eee5eb2416fdf768b6
approval_note: self-approved
links: []
tags:
  - hazard:denial-of-care
  - class:B
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

Severity 3 — Moderate (care delayed) — × probability 3 (Occasional) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Grants modelled per source and combined as a union, so one revocation cannot strip another grant | Design | SR-008, SR-036 | TR-001, TS-002 |
| Explicit tests for the documented consent cases A/B/C | Protective | SR-036, TASK-113 | TR-001, TS-002 |
| Denials are audited with the reason, so a wrong denial is diagnosable | Protective | SR-023 | TS-009 |
| Patient-facing consent UI shows exactly who has access | Information for safety | SR-008 | TR-001, TS-002 |

## Residual risk

Severity 3 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **alarp**, derived from `risk_matrix`. Residual ALARP. MedHub is not the only route to clinical information (the treating institution's own records remain), which is what keeps probability and severity from being higher.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

A denial is visible and recoverable — the clinician knows the data is withheld and can obtain it through the treating institution — and MedHub is not the only route to the information. Probability is reduced to Remote by per-source consent grants combined as a union and by audited denials. Loosening the policy further would raise RISK-001 (unauthorized disclosure), which is the larger harm; the deny-by-default trade-off is deliberate.

## Risks introduced by controls

Loosening consent scope to avoid denials would raise RISK-001; the balance is held by the per-source union model.
