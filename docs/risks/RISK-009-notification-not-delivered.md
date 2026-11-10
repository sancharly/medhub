---
id: RISK-009
type: risk
title: Appointment or activation notification not delivered
status: approved
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-10"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-10"
approval_note: approved by the human in chat at the close of CR-004
hazard: A patient never learns about an appointment, or cannot activate their account, because a notification was not delivered.
cause: A dead broker, a swallowed enqueue exception, an email provider rejection, or an expired activation token with no resend → no notification reaches the patient → they miss the appointment or cannot access their data. The e-mailed activation link does not reach the activation page (PRB-070). The API process dispatches tasks to the wrong broker, so no e-mail is sent (PRB-071).
harm: Missed or delayed care; frustration and extra administrative work. No direct physical harm.
severity_initial: 2
probability_initial: 3
severity_residual: 2
probability_residual: 2
acceptability: acceptable
links:
  - target: SOUP-014
    relation: relates_to
  - target: SOUP-021
    relation: relates_to
tags:
  - hazard:denial-of-care
  - class:B
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
| Activation link built in the route's form (`/activation/<token>`) and tied to the SPA route by a test (CR-004, PRB-070) | Design | SR-033; TASK-206 | TS-003 TC-003.3 |
| The API process sets the configured Celery app as the process default at start-up, so every `.delay()` goes to the Redis broker; a test starts the lifespan and checks the broker from a worker thread (CR-004, PRB-071) | Design | SR-033, SR-034 AC 2; TASK-206 | TS-003 TC-003.3 |
| Appointment visible in the patient's own view regardless of email | Design | SR-011, SR-035 | TR-001, TS-002, TS-006 |

## Residual risk

Severity 2 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **acceptable**, derived from `risk_matrix`. Delivery is best effort by design (no proof of delivery at MVP — arc42 §11); the in-app channel is what keeps the residual acceptable.

**Verification and proposed residual (CR-004 Checkpoint F, TASK-202, 2026-11-08).** Checkpoint F evidence (TASK-202, 2026-11-08, HEAD 579aaaa plus TASK-202's small edits): backend 1547 passed, 6 skipped, coverage 94.51% (floor 85%); DICOM module 25 passed; frontend 315 passed; infra 110 passed; started stack (project `task202`, empty template, generated secrets): `infra/smoke-test.sh` 78 passed, 0 failed; `infra/log-secrets-check.sh` 38 passed, 0 failed. On the started stack the real activation e-mail flow ran: an administrator created a patient account, the Celery worker sent one message through an SMTP sink, the message was addressed to the new account and held the link in the route's form (`/activation/<token>`), the token opened the activation, the account signed in, and a second use of the token answered 401. TC-003.3 and TC-003.7 pass. **Proposed residual: severity 2 × probability 2 → acceptable** (derived from `risk_matrix`; unchanged). PRB-013 (enqueue failures swallowed) is still `open` for the paths CR-004 did not touch.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

None identified.

## Version history

- 1.2 (2026-11-07) — TASK-206 (PRB-070): new cause, the e-mailed link does not reach the activation page; one control row. Approval cleared (`in_review`). Residual unchanged. 
- 1.3 (2026-11-07) — TASK-206 (PRB-071, CR-004 D-17): cause "the API process dispatches tasks to the wrong broker" and its control row. Still `in_review`. Residual unchanged.
- 1.4 (2026-11-08) — CR-004 Checkpoint F (TASK-202): started-stack activation e-mail flow recorded; residual proposed from the evidence, 2 × 2 → acceptable, unchanged. Still `in_review`.
