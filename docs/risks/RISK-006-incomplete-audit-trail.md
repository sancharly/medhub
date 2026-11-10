---
id: RISK-006
type: risk
title: Audit trail incomplete, so a wrong disclosure or entry goes undetected
status: approved
version: "1.5"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-10"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-10"
approval_note: approved by the human in chat at the close of CR-004
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
| Capture the client IP in authz and consent audit events | Protective | TASK-137, TASK-185 | TS-009 TC-009.9 (real-DB `test_audit_client_address.py`; no-request case `test_no_request_context_records_no_address`) |
| Tests asserting an audit row for every security-relevant action | Protective | TASK-113 (still `draft`) | TS-009 TC-009.1, TC-009.10 |
| Failure and refusal events committed on their own transaction, independent of the request outcome (ADR-0016); real-database tests per affected path | Design | SR-023, TASK-183 (CR-002) | TS-009 TC-009.4..8, TS-007 TC-007.6 |
| Originating client address from one trusted-proxy rule, recorded on every request-caused audit row (CR-004, ADR-0019) | Protective | SR-042 AC 1 to AC 3, SR-023 AC 6; TASK-185, TASK-137 | TS-016 TC-016.1..3, TS-009 TC-009.9; started stack: no audit row carries the proxy's address (172.28.77.2; the table held at least 133 rows), and 61 of 62 `AUTHZ_ALLOWED` rows carry an address (the one without is a background `account:delete` decision made by `infra/log-secrets-check.sh` through `compose exec`, with no HTTP request, so an empty `ip` is correct) |
| Every authorization decision, allowed or denied, audited by the single decision point (CR-004) | Design | SR-023 AC 7; TASK-187, TASK-188, TASK-189 | TS-009 TC-009.10 |
| Append-only enforced by privilege: the runtime role cannot `UPDATE`, `DELETE` or `TRUNCATE` `audit_log`; the silent rules dropped (CR-004, ADR-0017) | Design | SR-023 AC 8; TASK-190, TASK-191 | TS-009 TC-009.11; started stack: `UPDATE audit_log` is refused for the runtime role (smoke test) |
| Typed audit fields: no field can hold a credential or secret, whatever the caller passes (CR-004) | Design | SR-023 AC 9; TASK-192 | TS-009 TC-009.12 |

## Residual risk

Severity 2 (unchanged — controls reduce probability, not severity) × probability 2
(Remote) → **acceptable**, derived from `risk_matrix`. Append-only is now enforced by privilege (PRB-005 resolved, TASK-190, TASK-191), the source IP is
recorded on request-caused rows (PRB-010 resolved, TASK-137, TASK-185), and log correlation is
still unavailable (PRB-032, open).

**Pending verification (CR-002, PRB-052, 2026-10-30).** The 2 × 2 above assumed that recorded
events persist. PRB-052 shows that this does not hold for failure events. Until TASK-183 is
approved, the failure-evidence path is effectively 2 × 3, which the `risk_matrix` makes **alarp**.
That is tolerable only because no release exists (CR-002 A-1) and the access controls themselves
still work (PRB-052, safety evaluation). The scores are **not** changed now. TASK-183's tests are
the evidence. Once QA approves TASK-183, the expected residual is 2 × 2 → acceptable, unchanged.
Severity stays 2: the control reduces probability only.

**Change analysis (CR-004, Risk stage, 2026-10-31).** CR-004 removes three of the causes
named above: the missing source address (PRB-010), the decisions taken outside the audited path
(PRB-026, PRB-027), and append-only by convention (PRB-005, which also showed that the rules of
migration 0006 turn tampering into a silent success and that the application connects as a
superuser). **Expected residual: 2 × 2 → acceptable, unchanged.** It is not lowered to
probability 1 because two causes stay open outside CR-004: PRB-058 (a failure row lost on pool
exhaustion) and PRB-032 (no log correlation). Confirmed at verification (TASK-202, see below); the
"pending verification" note above for TASK-183 is now met: its tests are TC-009.4..8 and they pass.

**Verification and proposed residual (CR-004 Checkpoint F, TASK-202, 2026-11-08).** Checkpoint F evidence (TASK-202, 2026-11-08, HEAD 579aaaa plus TASK-202's small edits): backend 1547 passed, 6 skipped, coverage 94.51% (floor 85%); DICOM module 25 passed; frontend 315 passed; infra 110 passed; started stack (project `task202`, empty template, generated secrets): `infra/smoke-test.sh` 78 passed, 0 failed; `infra/log-secrets-check.sh` 38 passed, 0 failed. Failure rows persist (TC-009.4..8, real database), the address is the client's and never the proxy's on the started stack, every allowed and denied decision writes a row (TC-009.10), the runtime role cannot alter `audit_log` (TC-009.11), and no audit field holds a secret (TC-009.12). **Proposed residual: severity 2 × probability 2 → acceptable** (derived from `risk_matrix`; unchanged). Not 2 × 1, for the reasons already given: PRB-058 (failure row lost on pool exhaustion, `minor`, open), PRB-060 (below) and PRB-032 stay open, and PRB-072 shows that a modest burst already collapses the API, a load of the kind that would also exhaust the connection pool behind PRB-058 (not measured).

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

Richer audit content increases the PHI footprint of the logs — RISK-008 covers log-side PII, tracked by TASK-138.

The independent transaction (TASK-183) takes a second connection from the shared pool for each
failure event, while the request still holds its first one (`add_independent`,
`backend/app/db/repositories/audit_repo.py:23-32`). When a burst of failing requests exhausts the
pool (default 5 + 10), the request fails with a generic `500` after `pool_timeout` (30 s by
default). The failure row is then **lost**, and only the server log records the exception. QA
reproduced this with `pool_size=1, max_overflow=0, pool_timeout=2` on the `AUTHZ_DENIED` path:
`500` after 2.1 s, and no row. The burst is not bounded: the per-account lockout does not limit a
spray of distinct unknown emails, and login has no rate limit. This is recorded as
[PRB-058](../problem-reports/PRB-058-independent-audit-write-lost-on-pool-exhaustion.md) (minor).
No new hazard: it is the same RISK-006 hazard, through this record's rollback cause, under
abnormal load only. A failure row is no longer atomic with its request, which is correct: the
failure did happen (ADR-0016).

**Does the residual still hold?** Yes for now, at 2 × 2 → acceptable, for development use only.
TASK-183 removes the rollback cause under normal load, which is the probability the 2 × 2 rests on.
The pool-exhaustion path needs a burst of concurrent failing requests that no development
installation sees. No release exists (CR-002 A-1), so no installation relies on the trail. Severity
stays 2. This does **not** carry over to a release: PRB-058 must be resolved, or evaluated as a
residual anomaly (§5.8.2–5.8.3) and this residual re-confirmed, before the first release.

CR-004 (2026-10-31):

- Auditing every allowed decision raises the number of rows per request (list endpoints, module
  checks). No new hazard; it is a volume and performance effect (SR-026). Measured by TASK-202: on a started
  stack 62 `AUTHZ_ALLOWED` rows were written alongside 9 sign-ins, 5 clinical entries and 10 uploads, plus the log check's own requests (one row per decision,
  one insert in the request's own transaction); across the 218 tests whose duration is reported both before CR-004 (4d57094)
  and now, the summed time is 45.7 s before and 41.1 s now, so no suite slowdown shows. The measure is coarse: SR-026 has no
  performance test (AC 4 unverified, older than CR-004), so the real-database list latency with this volume has not been timed.
- PRB-060 (`minor`, open, accepted by the human on 2026-10-31 for now, to be fixed with PRB-058): an `AUTHZ_ALLOWED` row is written in the
  request's transaction, so it is rolled back when the request then fails, and the allowed decision leaves no row. The denied and
  failure rows are on their own transaction and are not affected. This leaves the allowed-decision trail incomplete for failing
  requests only; the failed request itself changed nothing, so the disclosure question the trail answers does not arise.
- A wrong `TRUSTED_PROXIES` fails silently: every address is the proxy's again (this record's
  cause). A started-stack check that an audit row's address is not the proxy's is part of TS-016.
- The typed fields refuse a value they do not recognise, so a caller bug now fails the request
  instead of writing a row; the refusal is logged without the value. This trades a lost row for
  a visible error, which is the safer direction for this hazard.
- Privilege-based append-only cannot stop the owner role; the owner credential is given only to
  `db-migrate` (ADR-0017, SR-041).

## Version history

- 1.2 (2026-10-30) — CR-002 amendment for PRB-052: new cause (audit rows rolled back with the
  failed request), new design control (TASK-183, ADR-0016) with its planned verification, and the
  residual marked pending verification. Scores unchanged. Approval record cleared, `in_review`.
  - Corrected by the QA review of TASK-183 (2026-10-30). "Risks introduced by controls" said the
    row was not silently dropped and that the Redis lockout limited the burst; both were false. On
    pool exhaustion the request fails with a `500` and the row is lost. A spray of unknown emails
    is not bounded. PRB-058 is raised. The residual is restated as holding for development only.
    Scores and status unchanged.
- 1.3 (2026-10-31) — CR-004 Risk stage, §7.4 change analysis (Software Architect role). Control rows added for the CR-004 controls with their planned verification; expected residual stated in "Residual risk"; "Risks introduced by controls" extended. Scores not changed: they are re-scored from the evidence at verification (TASK-202). Content change, so the approval record is cleared and the record returns to review.
- 1.4 (2026-11-08) — CR-004 Checkpoint F (TASK-202): planned verification replaced by the tests that ran; stale text corrected (append-only, source address, TASK-137 `draft`, "none yet" rows, TASK-183 note); PRB-060 and the measured audit volume recorded; residual proposed from the evidence, 2 × 2 → acceptable, unchanged. Content change, so `in_review` and the approval record cleared.
- 1.5 (2026-11-08) — TASK-202 round 2 (QA finding 4): the address-less `AUTHZ_ALLOWED` row explained. Scores unchanged.
