---
id: "RISK-009"
type: risk
title: "Appointment or activation notification not delivered"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
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

| Severity | Probability (P2) | Risk level (per ADD-003) |
|---|---|---|
| 2 — Minor (missed appointment, delay) | 3 — Occasional | 6 — ALARP (6) |

P1 (probability of the software fault itself) is taken as 1 per ADD-003: the fault is assumed to occur.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Dual-channel notification: in-app plus email | Design | SR-035 | TS (Review stage) |
| Celery retries with backoff, and enqueue failures logged rather than swallowed | Protective | TASK-141 | TS (Review stage) |
| Administrator-initiated resend of activation | Protective | SR-033 | TS (Review stage) |
| Appointment visible in the patient's own view regardless of email | Design | SR-011, SR-035 | TS (Review stage) |

## Residual risk

| Severity | Probability (P2) | Risk level | Acceptable? | Decided by / date |
|---|---|---|---|---|
| 2 — Minor (missed appointment, delay) | 2 — Remote | 4 — Acceptable (4) | **pending human decision** | — |

Delivery is best effort by design (no proof of delivery at MVP — arc42 §11); the in-app channel is what keeps the residual acceptable.

## Risks introduced by controls

None identified.
