---
id: RISK-008
type: risk
title: Personal data retained, copied or erased contrary to its lawful basis
status: approved
version: "1.8"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-16"
hazard: "PHI or PII living outside the controlled lifecycle: retained past its basis, copied into logs, or erased while still clinically or legally needed."
cause: Worker logs write email addresses as structured fields, a retention sweep fails silently, or an erasure drops clinical data instead of anonymizing it → personal data exists in an uncontrolled copy, or required data is gone → the obligation in SR-024 and the GDPR requirement cannot be met.
harm: Privacy harm to the patient and a regulatory breach; in the erase-too-much direction, loss of clinical history.
severity_initial: 2
probability_initial: 3
severity_residual: 2
probability_residual: 2
acceptability: acceptable
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-16"
approved_digest: b607508409b6888a1691bef1b3c37e87ac458f21eab8663a35fb156a0468726a
approval_note: self-approved
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
| PII scrubbing for worker and notification logs | Protective | TASK-138 | TS-017 TC-017.1 to TC-017.3 (the same tests as the row below); passed 2026-11-15 on the branch head, TASK-226 regression |
| Encryption at rest so residual copies are unreadable without keys | Protective | SR-022 | TR-001, TS-008 |
| Identifiers instead of personal data at every log call; one redaction filter on every handler of the API, worker and scheduler; log-capture tests of both worker paths and of an arbitrary structured field (CR-004) | Design | SR-043; TASK-138 | TS-017 TC-017.1..3, TC-017.5, TC-017.6; started stack: `infra/log-secrets-check.sh` found no password, token, retrieval code or `infra/.env` secret in six service logs |
| Retrieval of anonymized data limited per originating client address, atomically, so a retrieval code cannot be guessed by many attempts from one address (CR-004, PRB-029) | Protective | SR-042 AC 4, AC 5; TASK-185, TASK-186 | TS-016 TC-016.4, TC-016.5 |
| The retention sweep is scheduled and runs in the deployed stack: the Celery worker and beat run as their own commands (CR-004, PRB-061) | Design | TASK-191 | Started stack (TASK-191 QA and TASK-202): the worker answers `inspect ping`, beat logs `beat: Starting`, the retention sweep is in the beat schedule (smoke test, sections 11 and 12, 78 passed, 0 failed). The sweep itself was not triggered by TASK-202 |
| The retention sweep isolates a failure to its dataset, releases every session it opens and retries a transient failure at most 3 times; a retry is idempotent per dataset and deletes only datasets past their deadline; the failed count is logged without personal data (CR-006, PRB-012) | Protective | SR-024 AC 5, SR-043; TASK-141 (at Plan stage) | TS-004 TC-004.5 (`backend/tests/workers/test_retention_tasks.py`): `test_sweep_failing_dataset_closes_every_session`, `test_sweep_retries_at_most_three_times_then_logs_count`, `test_sweep_dataset_failing_once_then_succeeding_is_erased`, `test_sweep_never_deletes_before_deadline_across_retries`; TS-004 TC-004.7 (`backend/tests/workers/test_retention_lock.py`, real PostgreSQL): `test_second_sweep_waits_and_writes_no_audit_row`, `test_second_sweep_erases_after_the_first_rolls_back`, `test_locked_select_rechecks_the_deadline`; TS-017 TC-017.8 (failed-count log line) |
| An erasure whose retrieval-code e-mail cannot be queued fails with a retryable error and is rolled back as a whole (the enqueue is inside the request's transaction), so an erasure never completes with a lost retrieval code (CR-006 D-5, PRB-013) | Protective | SR-024 AC 6 (added by CR-006 D-11), AC 1; TASK-141 (at Plan stage) | TS-004 TC-004.4: `backend/tests/api/test_erasure_rollback.py::test_erasure_enqueue_failure_rolls_back_and_returns_503` (control `test_erasure_with_a_working_broker_commits_before_the_response`) and `backend/tests/identity/test_erasure.py::test_erasure_enqueue_failure_raises_retryable_problem_and_keeps_sessions`; TS-017 TC-017.7 `test_erasure_enqueue_failure_logs_warning_without_personal_data` |
| The retrieval-code e-mail ("your account has been erased") is sent only once the erasure is committed: the worker sends it only when the erasure's `anonymized_dataset` row is visible, re-checks for about 10 minutes, drops it on a positive "never committed" and sends it when the check cannot be made (CR-006 D-30, PRB-083) | Design | SR-024 AC 6; TASK-228 | TS-004 TC-004.6: `test_sends_when_the_dataset_is_committed`, `test_rechecks_until_the_dataset_is_committed`, `test_drops_the_e_mail_when_the_erasure_never_commits`, `test_sends_when_the_commit_cannot_be_confirmed`, `test_smtp_retry_budget_unchanged_after_commit_checks`, `test_gate_does_not_see_an_uncommitted_erasure` (real PostgreSQL); TS-017 TC-017.9 `test_erasure_e_mail_drop_and_unconfirmed_logs_hold_no_personal_data` (TASK-228) |

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

**Change analysis (CR-006, Risk stage, 2026-11-13).** CR-006 addresses the two causes CR-004
left: the retention sweep that fails silently and never retries (PRB-012, SR-024 AC 5), and an
erasure that completes while its retrieval-code e-mail is lost (PRB-013, D-5), after which the
subject cannot retrieve the anonymized data (`retrieve_anonymized` has no recovery path). Both
controls bring causes of their own: a retry must not erase too much (idempotent, deadline-bound),
and failing the request must roll back the whole erasure rather than commit it with a lost code.
**Expected residual: 2 × 2 → acceptable, unchanged.** Not lowered: PRB-074 (accepted known anomaly,
CR-004 D-18, D-21) and TASK-116 remain. Re-scored from the evidence at the CR-006 verification
checkpoint (TASK-226, 2026-11-15): TS-004 TC-004.4 to TC-004.7 and TS-017 TC-017.7 to TC-017.9 passed on the branch head (backend 1743 passed, 10 skipped; the real-PostgreSQL cases of TC-004.6 and TC-004.7 included), so the sweep isolation, the rolled-back erasure and the commit-gated e-mail hold as controls; **2 × 2 → acceptable, unchanged**.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

Scrubbing can remove context needed to diagnose an incident — balanced against RISK-006.

CR-004 (2026-10-31): the redaction filter replaces email-shaped values, which can hide a
non-personal value of that shape from an operator; accounts are named by identifier, which the
audit trail resolves (balanced against RISK-006 as above).

CR-006 (2026-11-13): failing an erasure when the broker is down delays the erasure until the
operator retries (the subject's data stays in place meanwhile, RISK-007 availability effect on the
operator). If the enqueue succeeds and the commit then fails, the subject receives a code that
matches no dataset and is told the account was erased when it was not: misleading, no data loss
(corrected 2026-11-14, PRB-083; it was called harmless here). Sweep retries add load on a failing
dependency; bounded at 3.

CR-006 D-30 (2026-11-14, TASK-228): the commit-gated e-mail introduces two causes of a lost code for a
committed erasure, the hazard SR-024 AC 6 controls. (a) The erasure commits more than about 10 minutes after
the enqueue (a request hung between enqueue and commit; no timeout bounds the transaction, the Redis client
has no socket timeout): the last check finds no row and the e-mail is dropped. The window is more than twenty
times the Gunicorn worker timeout; not observed. (b) The worker cannot reach PostgreSQL: handled by sending
when the commit cannot be confirmed, so this cause gives at worst the misleading e-mail of PRB-083, not a lost
code. The raw code stays in the broker during the re-checks (PRB-074, accepted anomaly), longer only for an
erasure that did not commit, whose code matches no dataset. Probability judged unchanged.

## Version history

- 1.2 (2026-10-31) — CR-004 Risk stage, §7.4 change analysis (Software Architect role). Control rows added for the CR-004 controls with their planned verification; expected residual stated in "Residual risk"; "Risks introduced by controls" extended. Scores not changed: they are re-scored from the evidence at verification (TASK-202). Content change, so the approval record is cleared and the record returns to review.
- 1.3 (2026-11-08) — CR-004 Checkpoint F (TASK-202): planned verification replaced by the tests that ran; control rows added for the retrieval rate limit (TASK-186) and for the retention sweep running in the deployed stack (PRB-061); stale `draft` text corrected; PRB-074 raised; residual proposed from the evidence, 2 × 2 → acceptable, unchanged. Content change, so `in_review` and the approval record cleared.
- (2026-11-10) — Human decision (CR-004 D-21): the residual is accepted unchanged; PRB-074 is accepted as a known anomaly while only development data exists, to be re-evaluated before the first release.
- 1.4 (2026-11-13) — CR-006 Risk stage, §7.4 change analysis (Software Architect role). Two control rows added (retention sweep isolation and retries, SR-024 AC 5; erasure rolled back when its code e-mail cannot be queued, D-5), with planned verification and TASKs left to the Plan stage; expected residual stated; "Risks introduced by controls" extended. Scores unchanged (2 × 2 → acceptable). Content change, so the approval record is cleared and the record returns to review. At the Risk gate the D-5 row was re-based on SR-024 AC 6 (CR-006 D-11).
- 1.5 (2026-11-14) — CR-006 D-30, §7.4 change analysis (Software Architect role): control row added for the commit-gated erasure e-mail (PRB-083, TASK-228) with planned verification; the "harmless" converse case corrected; "Risks introduced by controls" extended with the false-drop and unreachable-database causes. Scores unchanged (2 × 2 → acceptable). Content change, so the approval record is cleared and the record returns to review.
- 1.6 (2026-11-14) — TASK-228 verification: planned verification of the commit-gated erasure e-mail row replaced by the tests that ran. Scores unchanged (2 × 2 → acceptable). Content change, so the approval record is cleared and the record returns to review.
- 1.7 (2026-11-14) — TASK-225 (Document Writer): the Verify column of the two TASK-141 rows (sweep isolation and retries; erasure rolled back when the e-mail cannot be queued) replaced "none yet (planned …)" by the tests that ran, read from the test files and from TS-004 and TS-017. Scores unchanged (2 × 2 → acceptable). Content change on an approved record, so the 1.6 approval record is cleared and the record returns to review.
- 1.8 (2026-11-15) — TASK-226 (CR-006 verification): the log-scrubbing row ("none yet") names TS-017 TC-017.1 to TC-017.3; the executed tests of the CR-006 rows dated; re-scored from that evidence, 2 × 2 → acceptable, unchanged. Content change, so the record stays `in_review` for the owner's acceptance.
