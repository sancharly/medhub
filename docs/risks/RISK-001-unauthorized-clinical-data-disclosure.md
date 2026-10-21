---
id: RISK-001
type: risk
title: Clinical data disclosed to a user without authorization or consent
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
hazard: Protected health information reaching a person who has neither a role-based right nor the patient's consent to see it.
cause: A defect or misconfiguration in the authorization or consent evaluation (a route missing the `AuthorizationService` dependency, a wrong consent union, an admin projection not applied) → the API returns clinical data or PII to the caller → the caller reads information about a patient who never granted access.
harm: "Privacy harm: loss of confidentiality of health data, loss of trust, potential social or employment consequences for the patient; a reportable GDPR breach. No direct physical injury."
severity_initial: 2
probability_initial: 4
severity_residual: 2
probability_residual: 2
acceptability: acceptable
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 0771e308f61e06f46e0be506395f419db4d3818fa8cb519577a95fedb9eb86fc
approval_note: self-approved
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

## Residual risk

Severity 2 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **acceptable**, derived from `risk_matrix`. Residual estimate assumes the deny-by-default control and its negative tests are in place and verified. Open items that keep the current probability higher than the residual estimate: PRB-003 (CSRF
exemptions matched by prefix), PRB-014 (no route-level role guards) and PRB-026/PRB-027
(authorization decisions taken outside `AuthorizationService`). The admin-projection finding from
the audit is closed by TASK-120.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

Deny-by-default can wrongly deny a legitimate clinician access — that is RISK-004, assessed separately.
