---
id: RISK-006
type: risk
title: Audit trail incomplete, so a wrong disclosure or entry goes undetected
status: in_review
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-30"
hazard: Security-relevant or clinical-data events not recorded, or recorded without the information needed to reconstruct them.
cause: A code path bypasses `AuditService`, an audit row is rolled back with the failed request that recorded it, the client IP is not captured, the scrub drops needed context, or the log store is writable → an incident cannot be reconstructed → a wrong disclosure or falsified entry is never noticed or corrected.
harm: "Indirect: the harms of RISK-001/002/005 persist uncorrected, and the legal obligation to notify cannot be met."
severity_initial: 2
probability_initial: 3
severity_residual: 2
probability_residual: 2
acceptability: acceptable
links:
  - target: SOUP-008
    relation: relates_to
  - target: SOUP-020
    relation: relates_to
tags:
  - hazard:detectability
  - class:B
---

# RISK-006 — Audit trail incomplete, so a wrong disclosure or entry goes undetected

## Hazard

Security-relevant or clinical-data events not recorded, or recorded without the information needed to reconstruct them.

## Sequence of events

A code path bypasses `AuditService`, an audit row is rolled back with the failed request that recorded it, the client IP is not captured, the scrub drops needed context, or the log store is writable → an incident cannot be reconstructed → a wrong disclosure or falsified entry is never noticed or corrected.

The rollback cause was found by PRB-052 (2026-10-30). `get_db` rolls the request session back on
any exception, so every event that records a failure or a refusal, and is followed by an error
response, is lost: `AUTHZ_DENIED`, `LOGIN_FAILURE`, `ACCOUNT_LOCKOUT`, `ACTIVATION_FAILED` and the
`DICOM_STUDY_READ` FAILURE. Evidence of brute-force attempts and access denials is then missing.
The existing control "Tests asserting an audit row" did not catch it, because those tests mock the
repository and never check that the row is committed.

## Hazardous situation

A patient's data has been wrongly disclosed or altered and nobody can establish what happened.

## Harm

Indirect: the harms of RISK-001/002/005 persist uncorrected, and the legal obligation to notify cannot be met.

## Software items involved

SI-AUDIT (`AuditService`), SI-API, SI-PERSIST.

## Initial risk

Severity 2 — Minor (indirect: delays correction) — × probability 3 (Occasional) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Audit every authentication, authorization and clinical-data event | Design | SR-023 | TS-009 |
| Append-only storage with credential scrubbing | Design | SR-023, SR-022 | TR-001, TS-008, TS-009 |
| Capture the client IP in authz and consent audit events | Protective | TASK-137 | none yet |
| Tests asserting an audit row for every security-relevant action | Protective | TASK-113 | none yet |
| Failure and refusal events committed on their own transaction, independent of the request outcome (ADR-0016); real-database tests per affected path | Design | SR-023, TASK-183 (CR-002) | TS-009 TC-009.4..8, TS-007 TC-007.6 (planned, TASK-183) |

## Residual risk

Severity 2 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **acceptable**, derived from `risk_matrix`. Append-only is enforced by convention rather than by the database today (PRB-005), the source IP is
missing from authorization events (PRB-010, TASK-137, still `draft`), and log correlation is
unavailable (PRB-032).

**Pending verification (CR-002, PRB-052, 2026-10-30).** The 2 × 2 above assumed that recorded
events persist. PRB-052 shows that this does not hold for failure events. Until TASK-183 is
approved, the failure-evidence path is effectively 2 × 3, which the `risk_matrix` makes **alarp**.
That is tolerable only because no release exists (CR-002 A-1) and the access controls themselves
still work (PRB-052, safety evaluation). The scores are **not** changed now. TASK-183's tests are
the evidence. Once QA approves TASK-183, the expected residual is 2 × 2 → acceptable, unchanged.
Severity stays 2: the control reduces probability only.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

Richer audit content increases the PHI footprint of the logs — RISK-008 covers log-side PII, tracked by TASK-138.

The independent transaction (TASK-183) takes a second pooled connection for each failure event. A
login burst could exhaust the pool. Then the request fails with an error, and the row is not
silently dropped. The Redis lockout limits the burst. No new hazard. A failure row is no longer
atomic with its request, which is correct: the failure did happen (ADR-0016).

## Version history

- 1.2 (2026-10-30) — CR-002 amendment for PRB-052: new cause (audit rows rolled back with the
  failed request), new design control (TASK-183, ADR-0016) with its planned verification, and the
  residual marked pending verification. Scores unchanged. Approval record cleared, `in_review`.
