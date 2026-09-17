---
id: "RISK-001"
type: risk
title: "Clinical data disclosed to a user without authorization or consent"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links: []
tags: ["hazard:privacy", "class:B"]
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

| Severity | Probability (P2) | Risk level (per ADD-003) |
|---|---|---|
| 2 — Minor (privacy harm, no physical harm) | 4 — Probable | 8 — ALARP (8) |

P1 (probability of the software fault itself) is taken as 1 per ADD-003: the fault is assumed to occur.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Deny-by-default authorization on every protected endpoint | Design | SR-005, SR-009 | TS (Review stage) |
| Consent-scoped access for doctors and patients, revocation effective immediately | Design | SR-006, SR-007, SR-008, SR-036 | TS (Review stage) |
| Audit every authorization decision so a wrong disclosure is detectable | Protective | SR-023 | TS (Review stage) |
| Negative-case tests for every role and consent combination | Protective | TASK-113, TASK-142 | TS (Review stage) |

## Residual risk

| Severity | Probability (P2) | Risk level | Acceptable? | Decided by / date |
|---|---|---|---|---|
| 2 — Minor (privacy harm, no physical harm) | 2 — Remote | 4 — Acceptable (4) | **pending human decision** | — |

Residual estimate assumes the deny-by-default control and its negative tests are in place and verified. Open items that keep the current probability higher than the residual estimate: PRB-003 (CSRF
exemptions matched by prefix), PRB-014 (no route-level role guards) and PRB-026/PRB-027
(authorization decisions taken outside `AuthorizationService`). The admin-projection finding from
the audit is closed by TASK-120.

## Risks introduced by controls

Deny-by-default can wrongly deny a legitimate clinician access — that is RISK-004, assessed separately.
