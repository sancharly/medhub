---
id: RISK-001
type: risk
title: Clinical data disclosed to a user without authorization or consent
status: approved
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-10"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-10"
approval_note: approved by the human in chat at the close of CR-004
hazard: Protected health information reaching a person who has neither a role-based right nor the patient's consent to see it.
cause: A defect or misconfiguration in the authorization or consent evaluation (a route missing the `AuthorizationService` dependency, a wrong consent union, an admin projection not applied) → the API returns clinical data or PII to the caller → the caller reads information about a patient who never granted access.
harm: "Privacy harm: loss of confidentiality of health data, loss of trust, potential social or employment consequences for the patient; a reportable GDPR breach. No direct physical injury."
severity_initial: 2
probability_initial: 4
severity_residual: 2
probability_residual: 2
acceptability: acceptable
links:
  - target: SOUP-002
    relation: relates_to
  - target: SOUP-003
    relation: relates_to
tags:
  - hazard:privacy
  - class:B
---

# RISK-001 — Clinical data disclosed to a user without authorization or consent

## Hazard

Protected health information reaching a person who has neither a role-based right nor the patient's consent to see it.

## Sequence of events

A defect or misconfiguration in the authorization or consent evaluation (a route missing the `AuthorizationService` dependency, a wrong consent union, an admin projection not applied) → the API returns clinical data or PII to the caller → the caller reads information about a patient who never granted access.

## Hazardous situation

A doctor outside the patient's care relationship, or administrative personnel, sees clinical data or full account PII.

## Harm

Privacy harm: loss of confidentiality of health data, loss of trust, potential social or employment consequences for the patient; a reportable GDPR breach. No direct physical injury.

## Software items involved

SI-AUTHZ (`U-AUTHZ-Policy`, `U-AUTHZ-Consent`, `U-AUTHZ-AdminProjection`), SI-API, SI-CLINICAL, SI-ATTACH. See [ADD-005](../design-outputs/architecture/) once per-item records exist.

## Initial risk

Severity 2 — Minor (privacy harm, no physical harm) — × probability 4 (Probable) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Deny-by-default authorization on every protected endpoint | Design | SR-005, SR-009 | TR-001, TS-002 |
| Consent-scoped access for doctors and patients, revocation effective immediately | Design | SR-006, SR-007, SR-008, SR-036 | TR-001, TS-002 |
| Audit every authorization decision so a wrong disclosure is detectable | Protective | SR-023 | TS-009 |
| Negative-case tests for every role and consent combination | Protective | TASK-113 (still `draft`), TASK-142 | TS-002 TC-002.1, TC-002.7, TC-002.8 (decision tables, router rules), TC-002.9 (client route guard) |
| Object store reachable only by the backend (and its one-shot initialiser), no console, non-default credentials, so attachments cannot be read around the authorization layer (CR-002) | Design | SR-040; TASK-174 (credential preflight), TASK-177 (internal network). Also TASK-176: no console, loopback-only ports; traced to RISK-001 via SR-040 AC 1; the task mitigates RISK-012 | TS-014: TC-014.1..3 (weak or default keys stop start-up), TC-014.5 (no console or admin listener; only 8333 and 18333 off loopback), TC-014.6 (from the proxy, frontend, postgres, redis and worker the store does not resolve and its IP times out, including 18333; no host port). QA reruns in TASK-174, TASK-176, TASK-177 |
| Single decision point: every access decision on clinical data, personal data, modules and account lifecycle taken and audited by `AuthorizationService` (ADR-0006); a static check fails on a role comparison that decides access elsewhere (CR-004) | Design | SR-005, SR-023 AC 7, SR-032, SR-034; TASK-187, TASK-188, TASK-189 | TS-002 TC-002.7, TC-002.8; TS-003 TC-003.6; TS-009 TC-009.10 |
| CSRF exemptions as an exact path set with a route-inventory test (CR-004) | Design | SR-031 AC 3; TASK-139 | TS-011 TC-011.6, including the login-CSRF defence (a non-JSON login body is refused with 400 before `LoginService.login` runs; a cross-origin JSON post meets no CORS and gets 405 on the preflight) and the module-router assertion (TASK-202) |
| Route-level role guard in the client, driven by the navigation's role table: defence in depth only, the server stays the control (CR-004 Q-4) | Protective | SR-005; TASK-142 | TS-002 TC-002.9 |
| No known or placeholder credential in the deployment; no root process in an image MedHub builds; the application connects with a non-superuser runtime role (CR-004) | Design | SR-041 AC 1 to AC 4, SR-023 AC 8; TASK-197, TASK-203, TASK-198, TASK-190, TASK-191 | TS-015 TC-015.1..4; TS-009 TC-009.11 (started stack: the runtime role is refused `UPDATE audit_log`, smoke test) |

## Residual risk

Severity 2 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **acceptable**, derived from `risk_matrix`. Residual estimate assumes the deny-by-default control and its negative tests are in place and verified. Open items that keep the current probability higher than the residual estimate: PRB-003 (CSRF
exemptions matched by prefix), PRB-014 (no route-level role guards) and PRB-026/PRB-027
(authorization decisions taken outside `AuthorizationService`). The admin-projection finding from
the audit is closed by TASK-120.

**Change analysis (CR-004, Risk stage, 2026-10-31).** The residual above assumed the
deny-by-default control and its negative tests "in place and verified", and named PRB-003, PRB-014
and PRB-026/027 as the open items that kept the actual probability above it. CR-004 closes all
four and adds the deployment controls of SR-041 (PRB-007). **Expected residual: severity 2 ×
probability 2 → acceptable**, unchanged, but then realised instead of assumed. It is not lowered to
probability 1: a policy rule that is itself wrong is still possible, and the single decision point
makes such a rule apply everywhere at once. Confirmed at verification (TASK-202) from the TS above.
Scores are not changed now.

**Verification and proposed residual (CR-004 Checkpoint F, TASK-202, 2026-11-08).** Checkpoint F evidence (TASK-202, 2026-11-08, HEAD 579aaaa plus TASK-202's small edits): backend 1547 passed, 6 skipped, coverage 94.51% (floor 85%); DICOM module 25 passed; frontend 315 passed; infra 110 passed; started stack (project `task202`, empty template, generated secrets): `infra/smoke-test.sh` 78 passed, 0 failed; `infra/log-secrets-check.sh` 38 passed, 0 failed. Every CR-004 control row above now has a test that ran: the decision tables (TC-002.7, TC-002.8, TC-003.6) and the static role check (TC-002.8), the exact CSRF set and route inventory (TC-011.6), the client guard (TC-002.9), the secret and non-root checks (TC-015.1..4) and the runtime-role refusal (TC-009.11). The open items that kept the actual probability above the residual (PRB-003, PRB-014, PRB-026, PRB-027) are all `resolved`. **Proposed residual: severity 2 × probability 2 → acceptable** (derived from `risk_matrix`; unchanged). Not 2 × 1: a policy rule that is itself wrong is still possible, and the single decision point applies it everywhere at once. PRB-075 and PRB-072 are availability problems (RISK-007), not disclosure. TASK-113's own security review (SR-031 AC 6) is still `draft`; this proposal does not rest on it.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

Deny-by-default can wrongly deny a legitimate clinician access — that is RISK-004, assessed separately.

CR-004 (2026-10-31): moving every decision into `AuthorizationService` can change a decision
while moving it. Wrongly allowed is this record's hazard; wrongly denied is RISK-004. Control: a
decision-table test of the current behaviour of every moved check (role × action × ownership)
is written **before** each move and must pass unchanged after it (TASK-187..189). The client
route guard can hide a view from a role that should see it; that is a usability effect only,
because the server decides.

## Version history

- 1.1 (2026-10-21) — Approved (self-approved, 2026-10-21).
- 1.2 (2026-10-30) — CR-002 TASK-181, §7.4 change analysis (CR-002 AC-14), by the Software
  Architect role. Content change, so the approval record is cleared and the record returns to
  review.
  - New control row: the object store is reachable only by the backend and its initialiser, with
    no console and non-default credentials (SR-040; TASK-174, TASK-177; TASK-176 traced via SR-040
    AC 1; TS-014). It closes
    a path to attachments that bypassed `AuthorizationService` (PRB-043).
  - Not re-scored: severity 2 × probability 2 → `acceptable`, derived from `risk_matrix`. The
    residual is set by the authorization and consent controls and their open PRBs, which CR-002
    does not change. Acceptance is the human's, through approval of this version.
- 1.3 (2026-10-31) — CR-004 Risk stage, §7.4 change analysis (Software Architect role). Control rows added for the CR-004 controls with their planned verification; expected residual stated in "Residual risk"; "Risks introduced by controls" extended. Scores not changed: they are re-scored from the evidence at verification (TASK-202). Content change, so the approval record is cleared and the record returns to review.
- 1.4 (2026-11-08) — CR-004 Checkpoint F (TASK-202): planned verification replaced by the tests that ran; residual proposed from the evidence, 2 × 2 → acceptable, unchanged. Content change, so `in_review` and the approval record cleared; the owner's acceptance is the approval of this version.
