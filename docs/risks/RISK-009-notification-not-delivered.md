---
id: "RISK-009"
type: risk
title: "Appointment or activation notification not delivered"
status: in_review
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
hazard: "A patient never learns about an appointment, or cannot activate their account, because a notification was not delivered."
cause: "A dead broker, a swallowed enqueue exception, an email provider rejection, or an expired activation token with no resend → no notification reaches the patient → they miss the appointment or cannot access their data."
harm: "Missed or delayed care; frustration and extra administrative work. No direct physical harm."
severity_initial: 2
probability_initial: 3
severity_residual: 2
probability_residual: 2
acceptability: acceptable
links:
  - target: "SOUP-014"
    relation: relates_to
  - target: "SOUP-021"
    relation: relates_to
tags: ["hazard:denial-of-care", "class:B"]
---

# RISK-009 — Appointment or activation notification not delivered

## Hazard

A patient never learns about an appointment, or cannot activate their account, because a notification was not delivered.

## Sequence of events

A dead broker, a swallowed enqueue exception, an email provider rejection, or an expired activation token with no resend → no notification reaches the patient → they miss the appointment or cannot access their data.

## Hazardous situation

A patient is unaware of a scheduled appointment or is locked out of their own records.

## Harm

Missed or delayed care; frustration and extra administrative work. No direct physical harm.

## Software items involved

SI-WORKER (`U-WRK-Email`), SI-APPT, SI-IDENTITY (activation).

## Initial risk

Severity 2 — Minor (missed appointment, delay) — × probability 3 (Occasional) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Dual-channel notification: in-app plus email | Design | SR-035 | TR-001, TS-006 |
| Celery retries with backoff, and enqueue failures logged rather than swallowed | Protective | TASK-141 | none yet |
| Administrator-initiated resend of activation | Protective | SR-033 | TR-001, TS-003 |
| Appointment visible in the patient's own view regardless of email | Design | SR-011, SR-035 | TR-001, TS-002, TS-006 |

## Residual risk

Severity 2 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **acceptable**, derived from `risk_matrix`. Delivery is best effort by design (no proof of delivery at MVP — arc42 §11); the in-app channel is what keeps the residual acceptable.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

None identified.
