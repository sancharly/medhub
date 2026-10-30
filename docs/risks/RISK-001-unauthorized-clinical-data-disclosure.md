---
id: RISK-001
type: risk
title: Clinical data disclosed to a user without authorization or consent
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-30"
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
| Negative-case tests for every role and consent combination | Protective | TASK-113, TASK-142 | none yet |
| Object store reachable only by the backend (and its one-shot initialiser), no console, non-default credentials, so attachments cannot be read around the authorization layer (CR-002) | Design | SR-040; TASK-174 (credential preflight), TASK-177 (internal network). Also TASK-176: no console, loopback-only ports; traced to RISK-001 via SR-040 AC 1; the task mitigates RISK-012 | TS-014: TC-014.1..3 (weak or default keys stop start-up), TC-014.5 (no console or admin listener; only 8333 and 18333 off loopback), TC-014.6 (from the proxy, frontend, postgres, redis and worker the store does not resolve and its IP times out, including 18333; no host port). QA reruns in TASK-174, TASK-176, TASK-177 |

## Residual risk

Severity 2 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **acceptable**, derived from `risk_matrix`. Residual estimate assumes the deny-by-default control and its negative tests are in place and verified. Open items that keep the current probability higher than the residual estimate: PRB-003 (CSRF
exemptions matched by prefix), PRB-014 (no route-level role guards) and PRB-026/PRB-027
(authorization decisions taken outside `AuthorizationService`). The admin-projection finding from
the audit is closed by TASK-120.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

Deny-by-default can wrongly deny a legitimate clinician access — that is RISK-004, assessed separately.

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
