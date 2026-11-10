---
id: RISK-004
type: risk
title: Legitimate clinical access wrongly denied or delayed
status: approved
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-10"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-10"
approval_note: approved by the human in chat at the close of CR-004
hazard: A clinician with a legitimate care relationship cannot reach the patient's clinical data when needed.
cause: An over-restrictive or mis-scoped consent evaluation (a declined appointment revoking a grant from another source, a per-source union computed wrongly, a module guard denying an enabled module) → the API denies the request → the clinician proceeds without the available history.
harm: Care based on incomplete information, or delayed care while access is sorted out; recoverable in most workflows.
severity_initial: 3
probability_initial: 3
severity_residual: 3
probability_residual: 2
acceptability: alarp
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
| Decision-table characterisation tests, written before the authorization checks are moved into `AuthorizationService` and unchanged after it, so no legitimate access is newly denied (CR-004) | Protective | SR-005, SR-023 AC 7; TASK-187, TASK-188, TASK-189 | TS-002 TC-002.7, TS-003 TC-003.6 (characterisation tables written before each move, same cases after it) |

## Residual risk

Severity 3 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **alarp**, derived from `risk_matrix`. Residual ALARP. MedHub is not the only route to clinical information (the treating institution's own records remain), which is what keeps probability and severity from being higher.

**Change analysis (CR-004, Risk stage, 2026-10-31).** CR-004 moves the appointment
scoping, the appointment visibility rule, the module-access decision and the identity and router
role checks into `AuthorizationService` (PRB-026, PRB-027). A mistake in the move can deny a
clinician an appointment list or an enabled module. The new characterisation control keeps the
probability where it is. **Expected residual: 3 × 2 → alarp, unchanged**; the ALARP justification
below still holds. Every denial is now audited, which makes a wrong one easier to diagnose.
Confirmed at verification (TASK-202).

**Verification and proposed residual (CR-004 Checkpoint F, TASK-202, 2026-11-08).** Checkpoint F evidence (TASK-202, 2026-11-08, HEAD 579aaaa plus TASK-202's small edits): backend 1547 passed, 6 skipped, coverage 94.51% (floor 85%); DICOM module 25 passed; frontend 315 passed; infra 110 passed; started stack (project `task202`, empty template, generated secrets): `infra/smoke-test.sh` 78 passed, 0 failed; `infra/log-secrets-check.sh` 38 passed, 0 failed. The characterisation tables pass unchanged after the moves (TASK-187..189), and denials are audited (TC-009.10), so a wrong denial leaves a row. The client route guard is tied to the navigation table (TC-002.9). **Proposed residual: severity 3 × probability 2 → alarp** (derived from `risk_matrix`; unchanged), with the ALARP justification below unchanged. The availability problems PRB-072 and PRB-075 are RISK-007's; they deny access to everyone, not by a consent mistake.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

A denial is visible and recoverable — the clinician knows the data is withheld and can obtain it through the treating institution — and MedHub is not the only route to the information. Probability is reduced to Remote by per-source consent grants combined as a union and by audited denials. Loosening the policy further would raise RISK-001 (unauthorized disclosure), which is the larger harm; the deny-by-default trade-off is deliberate.

## Risks introduced by controls

Loosening consent scope to avoid denials would raise RISK-001; the balance is held by the per-source union model.

CR-004 (2026-10-31): the module-access refusal and the single-appointment refusal are now
audited, so a wrong denial leaves an `AUTHZ_DENIED` row with the actor and the target. The
client route guard (TASK-142) can, if its role table is wrong, hide a view; the server
response is unchanged, and a test ties the guard to the navigation table.

## Version history

- 1.2 (2026-10-31) — CR-004 Risk stage, §7.4 change analysis (Software Architect role). Control rows added for the CR-004 controls with their planned verification; expected residual stated in "Residual risk"; "Risks introduced by controls" extended. Scores not changed: they are re-scored from the evidence at verification (TASK-202). Content change, so the approval record is cleared and the record returns to review.
- 1.3 (2026-11-08) — CR-004 Checkpoint F (TASK-202): planned verification replaced by the tests that ran; residual proposed from the evidence, 3 × 2 → alarp, unchanged. Content change, so `in_review` and the approval record cleared.
