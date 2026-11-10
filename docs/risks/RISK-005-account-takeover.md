---
id: RISK-005
type: risk
title: Account takeover leading to disclosure or falsified clinical records
status: approved
version: "1.6"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-10"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-10"
approval_note: approved by the human in chat at the close of CR-004
hazard: "An attacker acting as a legitimate user: reading PHI, or writing clinical entries as a clinician."
cause: Credential stuffing, brute force, a stolen session token (including one brought back after logout, eviction or a password change by a racing session refresh, PRB-064), or a CSRF-able mutating endpoint → the attacker authenticates or rides an authenticated session → they read or write clinical data under someone else's identity.
harm: Wrong clinical decisions from falsified data, plus privacy harm. Recoverable if detected via the audit trail.
severity_initial: 3
probability_initial: 2
severity_residual: 3
probability_residual: 1
acceptability: acceptable
links:
  - target: SOUP-012
    relation: relates_to
  - target: SOUP-021
    relation: relates_to
  - target: SOUP-013
    relation: relates_to
  - target: SOUP-003
    relation: relates_to
  - target: SOUP-024
    relation: relates_to
tags:
  - hazard:security
  - class:B
---

# RISK-005 — Account takeover leading to disclosure or falsified clinical records

## Hazard

An attacker acting as a legitimate user: reading PHI, or writing clinical entries as a clinician.

## Sequence of events

Credential stuffing, brute force, a stolen session token (including one brought back after logout, eviction or a password change by a racing session refresh, PRB-064), or a CSRF-able mutating endpoint → the attacker authenticates or rides an authenticated session → they read or write clinical data under someone else's identity.

## Hazardous situation

Clinical records contain entries not made by their apparent author, or PHI has been exfiltrated.

## Harm

Wrong clinical decisions from falsified data, plus privacy harm. Recoverable if detected via the audit trail.

## Software items involved

SI-AUTH (`U-AUTH-Login`, `U-AUTH-Session`), SI-API (CSRF), SI-AUDIT, SI-DEPLOY (ADD-026), SI-FE-AUTH.

## Initial risk

Severity 3 — Moderate (wrong data or disclosure) — × probability 2 (Remote) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| Argon2id hashing with timing parity, and a password complexity policy | Design | SR-025 | TR-001, TS-001 |
| Account lockout after failed attempts, wired into the login path | Protective | SR-029, TASK-118, TASK-140 | TR-001, TS-001 |
| Opaque server-side sessions with absolute and idle expiry, revocable | Design | SR-030 | TR-001, TS-001 |
| CSRF enforcement on every mutating route, security headers, TLS/HSTS | Design | SR-031, SR-001 | TR-001, TS-008, TS-011 |
| Audit trail of security-relevant events for detection | Protective | SR-023 | TS-009 |
| Concurrency cap enforced atomically: cap check, eviction and insertion in one Redis transaction, tested with concurrent logins against a real Redis (CR-004, PRB-023) | Design | SR-030 AC 7; TASK-199 | TS-001 TC-001.6 |
| Session refresh is a conditional write (`SET … EX … XX`), so logout, eviction and the password-change session kill cannot be undone by a concurrent request; expired sessions are pruned from the cap and not counted (CR-004, PRB-064, PRB-065) | Design | SR-030 AC 5, AC 7; TASK-205 | TS-001 TC-001.8, TC-001.9 |
| Lockout service a required dependency of the login flow; the unused signing-key setting removed (CR-004, PRB-018) | Design | SR-029 AC 1, SR-030; TASK-140 | TS-001 TC-001.7 |
| No default or placeholder credential for the database, the mail relay or the keys; start-up refused otherwise (CR-004, PRB-007) | Design | SR-041 AC 2 to AC 4; TASK-197, TASK-203 | TS-015 TC-015.2..4; started stack: the stack was generated from the empty template and started only with generated secrets |
| The session token is no longer stored in the audit trail (logout event), and no audit field can hold a secret (CR-004, PRB-005) | Design | SR-023 AC 9; TASK-192 | TS-009 TC-009.12 |
| No credential or secret in operational or proxy logs: route templates in the backend error log; allow-listed proxy log format with no request line, query string or header; activation locations' error log at `crit` and `Referrer-Policy: no-referrer`; no access log in the frontend container; task arguments redacted at `--loglevel=debug` (CR-004, PRB-068) | Design | SR-043 AC 4, SR-033; TASK-206, TASK-207 (every case variant of the activation paths matched with `~*`; secrets of `infra/.env` added to the started-stack check) | TS-017 TC-017.4 |

## Residual risk

Severity 3 (unchanged — controls reduce probability, not severity) × probability 1
(Improbable) → **acceptable**, derived from `risk_matrix`. App-wide CSRF enforcement and the lockout wiring are in place (TASK-128, TASK-118). Residual still
depends on PRB-003 (exemptions matched by prefix), PRB-018 (lockout parameter made required) and
PRB-023 (non-atomic session-cap eviction) being closed.

**Change analysis (CR-004, Risk stage, 2026-10-31).** The residual above depended on PRB-003,
PRB-018 and PRB-023 being closed; CR-004 closes all three and PRB-007's credential part, and
TASK-192 removes the session token that the logout event stored (found by the PRB-005
investigation; the token was already revoked, so it was not usable). **Expected residual: 3 × 1
→ acceptable, unchanged**, now without open dependencies. Confirmed at verification (TASK-202).

**Change analysis (CR-004 D-11, TASK-205, 2026-11-06).** PRB-064 (a refresh can bring back an
ended session) was a cause the residual estimate did not cover: the estimate assumed that logout,
eviction and the password-change kill revoke a session. The conditional refresh makes that
assumption true. **Residual unchanged: 3 × 1 → acceptable.**

**Verification and proposed residual (CR-004 Checkpoint F, TASK-202, 2026-11-08).** Checkpoint F evidence (TASK-202, 2026-11-08, HEAD 579aaaa plus TASK-202's small edits): backend 1547 passed, 6 skipped, coverage 94.51% (floor 85%); DICOM module 25 passed; frontend 315 passed; infra 110 passed; started stack (project `task202`, empty template, generated secrets): `infra/smoke-test.sh` 78 passed, 0 failed; `infra/log-secrets-check.sh` 38 passed, 0 failed. The session controls ran against a real Redis (TC-001.6, TC-001.8..10), the lockout wiring and the audit scrub are tested (TC-001.7, TC-009.12), and no known value appeared in any of six service logs on the started stack (activation token, session token, CSRF token, passwords, retrieval code and the `infra/.env` secrets, 0 matches each). The real activation e-mail flow worked end to end (the worker sent one message; the link opened the activation, the account signed in, a second use of the token answered 401). **Proposed residual: severity 3 × probability 1 → acceptable** (derived from `risk_matrix`; unchanged). **For the human:** PRB-074 (activation tokens, retrieval codes and an erased user's e-mail in plaintext as Celery task arguments in Redis, `major`, accepted as a known anomaly outside CR-004 by D-18) is a cause of this hazard that needs access to the internal network, the host or a volume copy. This proposal keeps 3 × 1 because that access is required; if you read it as a probability 2, the record is 3 × 2 → alarp and needs an ALARP justification. PRB-013 (enqueue failures swallowed) is covered for the paths CR-004 touched by TC-017.6 and TC-003.7.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

Aggressive lockout enables a denial-of-service against a known account — RISK-007; mitigated by administrator-initiated unlock.

CR-004 (2026-10-31): the optimistic Redis transaction retries on contention; after its bounded
retries the login is answered 503 with `Retry-After: 1` rather than exceeding the cap (an availability effect
on one login, RISK-007; TASK-205). The start-up refusal of placeholder secrets is a deployment-time
availability effect by design, with a message naming the setting.

## Version history

- 1.2 (2026-10-31) — CR-004 Risk stage, §7.4 change analysis (Software Architect role). Control rows added for the CR-004 controls with their planned verification; expected residual stated in "Residual risk"; "Risks introduced by controls" extended. Scores not changed: they are re-scored from the evidence at verification (TASK-202). Content change, so the approval record is cleared and the record returns to review.
- 1.3 (2026-11-06) — TASK-205 (CR-004 D-11): new cause (an ended session brought back by a racing refresh, PRB-064), one control row (conditional refresh, expired members pruned from the cap), TC-001.8 and TC-001.9 as verification, contention effect now 503. Scores unchanged. Content change, so the 1.2 approval record is cleared and the record returns to review.
- 1.4 (2026-11-07) — TASK-206 (CR-004 D-14, D-16): one control row, no credential or secret in operational and proxy logs (SR-043 AC 4, TS-017 TC-017.4). Residual unchanged (3 x 1, acceptable).
- 1.5 (2026-11-07) — TASK-207 (TASK-206 QA findings 2, 6): the log control row names TASK-207 (case-insensitive activation matching; widened started-stack check). Residual unchanged (3 x 1, acceptable). A hand-crafted Referer or a token in another path's query string that reaches the proxy error log is a residual accepted against SR-043 AC 4 (CR-004 D-19), not a change of the scores.
- 1.6 (2026-11-08) — CR-004 Checkpoint F (TASK-202): planned verification replaced by the tests that ran; residual proposed from the evidence, 3 × 1 → acceptable, unchanged; PRB-074 raised to the human as the one open cause. Content change, so `in_review` and the approval record (none) stays cleared.
- (2026-11-10) — Human decision (CR-004 D-21): the residual is accepted unchanged; PRB-074 is accepted as a known anomaly while only development data exists, to be re-evaluated before the first release.
