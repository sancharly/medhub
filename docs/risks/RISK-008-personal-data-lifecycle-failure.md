---
id: RISK-008
type: risk
title: Personal data retained, copied or erased contrary to its lawful basis
status: approved
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-10"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-10"
approval_note: approved by the human in chat at the close of CR-004
hazard: "PHI or PII living outside the controlled lifecycle: retained past its basis, copied into logs, or erased while still clinically or legally needed."
cause: Worker logs write email addresses as structured fields, a retention sweep fails silently, or an erasure drops clinical data instead of anonymizing it → personal data exists in an uncontrolled copy, or required data is gone → the obligation in SR-024 and the GDPR requirement cannot be met.
harm: Privacy harm to the patient and a regulatory breach; in the erase-too-much direction, loss of clinical history.
severity_initial: 2
probability_initial: 3
severity_residual: 2
probability_residual: 2
acceptability: acceptable
links:
  - target: SOUP-014
    relation: relates_to
tags:
  - hazard:privacy
  - class:B
---

# RISK-008 — Personal data retained, copied or erased contrary to its lawful basis

## Hazard

PHI or PII living outside the controlled lifecycle: retained past its basis, copied into logs, or erased while still clinically or legally needed.

## Sequence of events

Worker logs write email addresses as structured fields, a retention sweep fails silently, or an erasure drops clinical data instead of anonymizing it → personal data exists in an uncontrolled copy, or required data is gone → the obligation in SR-024 and the GDPR requirement cannot be met.

## Hazardous situation

Personal data is processed outside the erasure and retention machinery.

## Harm

Privacy harm to the patient and a regulatory breach; in the erase-too-much direction, loss of clinical history.

## Software items involved

SI-WORKER (retention, erasure, notifications), SI-IDENTITY (`U-ID-Erasure`), SI-AUDIT, log pipeline.

## Initial risk

Severity 2 — Minor (privacy harm) — × probability 3 (Occasional) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Erasure and retention implemented as auditable, retriable jobs | Design | SR-024, TASK-036, TASK-141 | TR-001, TS-004 |
| Clinical data anonymized and re-keyed rather than dropped | Design | SR-024, TASK-116 | TR-001, TS-004 |
| PII scrubbing for worker and notification logs | Protective | TASK-138 | none yet |
| Encryption at rest so residual copies are unreadable without keys | Protective | SR-022 | TR-001, TS-008 |
| Identifiers instead of personal data at every log call; one redaction filter on every handler of the API, worker and scheduler; log-capture tests of both worker paths and of an arbitrary structured field (CR-004) | Design | SR-043; TASK-138 | TS-017 TC-017.1..3, TC-017.5, TC-017.6; started stack: `infra/log-secrets-check.sh` found no password, token, retrieval code or `infra/.env` secret in six service logs |
| Retrieval of anonymized data limited per originating client address, atomically, so a retrieval code cannot be guessed by many attempts from one address (CR-004, PRB-029) | Protective | SR-042 AC 4, AC 5; TASK-185, TASK-186 | TS-016 TC-016.4, TC-016.5 |
| The retention sweep is scheduled and runs in the deployed stack: the Celery worker and beat run as their own commands (CR-004, PRB-061) | Design | TASK-191 | Started stack (TASK-191 QA and TASK-202): the worker answers `inspect ping`, beat logs `beat: Starting`, the retention sweep is in the beat schedule (smoke test, sections 11 and 12, 78 passed, 0 failed). The sweep itself was not triggered by TASK-202 |

## Residual risk

Severity 2 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **acceptable**, derived from `risk_matrix`. TASK-138 is approved and verified (TS-017); TASK-116 and TASK-141 are still `draft`, and they carry the retention and retriable-job causes that CR-004 does not touch.

**Change analysis (CR-004, Risk stage, 2026-10-31).** The log-side copy is the cause CR-004
addresses (PRB-011). The investigation found that the formatters in use today drop the two
`extra` fields, so the copy is one formatter change away rather than on stdout now, and that the
worker had no logging configuration at all; the failure path is unverified. **Expected residual:
2 × 2 → acceptable, unchanged.** Not lowered, because the retention and erasure causes (PRB-012,
TASK-116, TASK-141) are outside CR-004. Confirmed at verification (TASK-202).

**Verification and proposed residual (CR-004 Checkpoint F, TASK-202, 2026-11-08).** Checkpoint F evidence (TASK-202, 2026-11-08, HEAD 579aaaa plus TASK-202's small edits): backend 1547 passed, 6 skipped, coverage 94.51% (floor 85%); DICOM module 25 passed; frontend 315 passed; infra 110 passed; started stack (project `task202`, empty template, generated secrets): `infra/smoke-test.sh` 78 passed, 0 failed; `infra/log-secrets-check.sh` 38 passed, 0 failed. The log-side copy is closed for the paths tested: logging tests of both worker paths and of an arbitrary structured field pass (TC-017.1..3), and on the started stack the log check found nothing. **Proposed residual: severity 2 × probability 2 → acceptable** (derived from `risk_matrix`; unchanged). Not lowered, as the change analysis said: PRB-012 and TASK-116 are outside CR-004. **For the human:** PRB-074 (an erased user's e-mail address and retrieval codes sit in plaintext as Celery task arguments in Redis, in the append-only file as well, `major`, open, accepted as a known anomaly outside CR-004 by D-18) is a retention failure against erasure and a cause of this hazard that the log controls do not reach. The 2 × 2 does not rest on it being absent; if you judge it raises the probability, the record is 2 × 3 → alarp.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

Scrubbing can remove context needed to diagnose an incident — balanced against RISK-006.

CR-004 (2026-10-31): the redaction filter replaces email-shaped values, which can hide a
non-personal value of that shape from an operator; accounts are named by identifier, which the
audit trail resolves (balanced against RISK-006 as above).

## Version history

- 1.2 (2026-10-31) — CR-004 Risk stage, §7.4 change analysis (Software Architect role). Control rows added for the CR-004 controls with their planned verification; expected residual stated in "Residual risk"; "Risks introduced by controls" extended. Scores not changed: they are re-scored from the evidence at verification (TASK-202). Content change, so the approval record is cleared and the record returns to review.
- 1.3 (2026-11-08) — CR-004 Checkpoint F (TASK-202): planned verification replaced by the tests that ran; control rows added for the retrieval rate limit (TASK-186) and for the retention sweep running in the deployed stack (PRB-061); stale `draft` text corrected; PRB-074 raised; residual proposed from the evidence, 2 × 2 → acceptable, unchanged. Content change, so `in_review` and the approval record cleared.
- (2026-11-10) — Human decision (CR-004 D-21): the residual is accepted unchanged; PRB-074 is accepted as a known anomaly while only development data exists, to be re-evaluated before the first release.
