---
id: RISK-004
type: risk
title: Legitimate clinical access wrongly denied or delayed
status: approved
version: "1.7"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-14"
hazard: A clinician with a legitimate care relationship cannot reach the patient's clinical data when needed.
cause: An over-restrictive or mis-scoped consent evaluation (a declined appointment revoking a grant from another source, a per-source union computed wrongly, a module guard denying an enabled module) → the API denies the request → the clinician proceeds without the available history.
harm: Care based on incomplete information, or delayed care while access is sorted out; recoverable in most workflows.
severity_initial: 3
probability_initial: 3
severity_residual: 3
probability_residual: 2
acceptability: alarp
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-14"
approved_digest: 52935e44fb0a49440efb1a1137c95f2c3ae29595b6820b01f9148708734a11d2
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
| Decision-table characterisation tests, written before the authorization checks are moved into `AuthorizationService` and unchanged after it, so no legitimate access is newly denied (CR-004) | Protective | SR-005, SR-023 AC 7; TASK-187, TASK-188, TASK-189 | TS-002 TC-002.7, TS-003 TC-003.6 (characterisation tables written before each move, same cases after it) |
| A module enablement change reaches every affected user's UI within 60 seconds or the next navigation (poll about every 50 s with a stale time no larger, so the bound holds with the round trip and one retry; refetch on focus; the poll does not extend the server session, CR-006 D-32); a failed refetch keeps the last known value rather than hiding an enabled module; the server guard stays the authority (CR-006 D-4, PRB-015) | Design | SR-015 AC 5, AC 3; TASK-221 | none yet (planned: Vitest refetch and failed-refetch cases; TS-005 at system level) |
| `groups_of` rewritten without the per-membership query only after a characterisation test of its results, unchanged after the rewrite, so no enabled module is newly denied (CR-006, PRB-024) | Protective | SR-026 AC 6, SR-014 AC 4; TASK-220 | none yet (planned: characterisation and query-count tests, TS-005) |

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

**Change analysis (CR-006, Risk stage, 2026-11-13).** A cause the estimate did not name: the
client's module list is never invalidated (PRB-015), so a user whose group gains the DICOM viewer
does not see it until a reload, which delays access. CR-006 adds the refresh control (SR-015
AC 5). The `groups_of` rewrite (PRB-024) could deny an enabled module if it returns too few
groups; the characterisation control holds that. **Expected residual: 3 × 2 → alarp, unchanged**;
the ALARP justification below still holds. Re-scored from the evidence at the CR-006 verification
checkpoint.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

A denial is visible and recoverable — the clinician knows the data is withheld and can obtain it through the treating institution — and MedHub is not the only route to the information. Probability is reduced to Remote by per-source consent grants combined as a union and by audited denials. Loosening the policy further would raise RISK-001 (unauthorized disclosure), which is the larger harm; the deny-by-default trade-off is deliberate.

## Risks introduced by controls

Loosening consent scope to avoid denials would raise RISK-001; the balance is held by the per-source union model.

CR-004 (2026-10-31): the module-access refusal and the single-appointment refusal are now
audited, so a wrong denial leaves an `AUTHZ_DENIED` row with the actor and the target. The
client route guard (TASK-142) can, if its role table is wrong, hide a view; the server
response is unchanged, and a test ties the guard to the navigation table.

CR-006 (2026-11-13, D-32 2026-11-14): the module-list refetch adds requests on focus, on navigation
and every 50 s or so while the tab is visible. A stale "enabled" state can show a link that the server then
refuses (no disclosure, RISK-001 unaffected). The poll checks the session without extending it, so it does
not keep an unattended session alive (RISK-005).

CR-006 D-33 (2026-11-14): the client session deadline now comes only from `me` and extend responses
(PRB-087), and the client timeout logs out on the server (PRB-089). A clinician who reads without making
requests is warned at 13 minutes and must press Extend. One who works through requests that do not refresh
`me` can be warned before the server would end the session. Ignoring the warning signs them out at the client
deadline. The access is delayed by a sign-in and any unsaved form input is lost. Extend and the sign-in
recover it, and the scores do not change.

## Version history

- 1.2 (2026-10-31) — CR-004 Risk stage, §7.4 change analysis (Software Architect role). Control rows added for the CR-004 controls with their planned verification; expected residual stated in "Residual risk"; "Risks introduced by controls" extended. Scores not changed: they are re-scored from the evidence at verification (TASK-202). Content change, so the approval record is cleared and the record returns to review.
- 1.3 (2026-11-08) — CR-004 Checkpoint F (TASK-202): planned verification replaced by the tests that ran; residual proposed from the evidence, 3 × 2 → alarp, unchanged. Content change, so `in_review` and the approval record cleared.
- 1.4 (2026-11-13) — CR-006 Risk stage, §7.4 change analysis (Software Architect role). Two control rows added (module-list refresh, SR-015 AC 5; `groups_of` characterisation, SR-026 AC 6), TASKs left to the Plan stage; expected residual stated; "Risks introduced by controls" extended. Scores unchanged (3 × 2 → alarp). Content change, so the approval record (approved 2026-11-10 in chat) is cleared and the record returns to review.
- 1.5 (2026-11-13) — CR-006 Plan gate (D-22): the module-refresh row names TASK-221 (split from TASK-144) and the `groups_of` row names TASK-220. Scores unchanged. Content change, so the approval record is cleared and the record returns to review.
- 1.6 (2026-11-14) — CR-006 D-32 (TASK-221 QA round 1 HIGH 1, MEDIUM 2): the module-refresh row and "Risks introduced by controls" name the ~50 s poll (stale time no larger) and the non-sliding session check. Scores unchanged (3 × 2 → alarp). Content change, so the approval record (approved 2026-11-13) is cleared and the record returns to review.
- 1.7 (2026-11-14) — CR-006 D-33: one "Risks introduced by controls" line for the server-driven client deadline and the logout at the client timeout (availability: an earlier warning, a sign-in). Control rows and scores unchanged (3 × 2 → alarp). Content change; the record stays `in_review` with no approval record.
