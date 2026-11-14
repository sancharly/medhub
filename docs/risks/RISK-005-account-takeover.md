---
id: RISK-005
type: risk
title: Account takeover leading to disclosure or falsified clinical records
status: approved
version: "1.11"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-14"
hazard: "An attacker acting as a legitimate user: reading PHI, or writing clinical entries as a clinician."
cause: Credential stuffing, brute force, a stolen session token (including one brought back after logout, eviction or a password change by a racing session refresh, PRB-064), or a CSRF-able mutating endpoint → the attacker authenticates or rides an authenticated session → they read or write clinical data under someone else's identity.
harm: Wrong clinical decisions from falsified data, plus privacy harm. Recoverable if detected via the audit trail.
severity_initial: 3
probability_initial: 2
severity_residual: 3
probability_residual: 1
acceptability: acceptable
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-14"
approved_digest: 0a6cddbcd0f1b91e4dfbd66745eef67ee1f7c25c9ba97ad6ad98d3dbe86f97b1
approval_note: self-approved
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
| The client's inactivity deadline and countdown follow the session expiry reported by the server (remaining time taken relative to the response, not the client clock); one source for the session query; an expired or invalid session gives one redirect to sign-in; the upload goes through the shared request helper, so a 401 there ends the session like any other request; the deadline is re-armed only by a `me` or extend response, never by mouse, keyboard or scroll activity, which has no listener (CR-006, PRB-016, PRB-019, PRB-025; D-33, PRB-087). Server enforcement of SR-030 AC 1 to AC 3 is unchanged, except that `GET /me/modules` checks the session without extending it (next row, CR-006 D-32) | Design | SR-030 AC 8, AC 4; SR-026 AC 8; TASK-143, TASK-144, TASK-222 (unit tests: TASK-146) | TASK-222 part: TS-001 TC-001.13, `frontend/src/auth/useIdleTimer.test.ts` ("activity events do not move the deadline", "no listeners registered for activity events", "a new deadline re-arms both timers", "schedules nothing until a deadline is known", "treats a deadline already in the past as expired") and "reading without requests is warned at 13 min and signed out at 15 min" (`SessionActivityProvider.test.tsx`); passed 2026-11-14, TASK-222 QA round 2. TASK-146 part (PRB-017), passed 2026-11-14, TASK-146 QA round 1: fake timers, `SessionActivityProvider.test.tsx` ("timeout logs out, clears the cache and redirects once", "Extend re-arms from expiresInSeconds", "a refreshed me re-arms", "clock jump with the warning open: one logout, an empty cache and one redirect"); upload 401, `client.test.ts` ("raises AuthError on a 401 unauthenticated problem"), `AttachmentUpload.test.tsx` ("shows the server's detail when the session has ended (401)") and "a mutation's AuthError redirects once and clears the cache (the upload included)"; `api/csrf.ts`, TS-011 TC-011.8 `frontend/src/api/csrf.test.ts` (12 tests); generated-types drift, TS-011 TC-011.9 `frontend/src/api/generated/openapiDrift.test.ts` (2 tests). Still planned: TS-001 system level (TASK-226) |
| The client timeout ends the session: when the client deadline passes, `handleExpired` clears the query cache, logs out on the server (best effort; a failure is ignored and still redirects) and redirects once, so neither going Back nor a session the server still holds gives the next person access. The warning dialog does not redirect on its own: at the end of its countdown, and on an extend answered 401, it calls the same `handleExpired`, which ends the session once (`sessionEnded` guard) (CR-006 D-33, PRB-089; D-34, PRB-090) | Design | SR-030 AC 1, AC 2, AC 5, AC 8; TASK-222 | TS-001 TC-001.13, `frontend/src/auth/SessionActivityProvider.test.tsx` (12 tests incl. "timeout logs out, clears the cache and redirects once", "redirects without waiting for logout to answer", "clock jump with the warning open: one logout, an empty cache and one redirect", "the dialog's tick and the expiry timer firing in one pass log out once", "extend 401 then Back shows no clinical data", "Back after a timeout shows no clinical data") and `IdleWarningDialog.test.tsx` ("extend 401 reports the ended session through onExpired", "the countdown reaching zero reports the ended session through onExpired once"); passed 2026-11-14, TASK-222 QA round 2. TC-001.14 (session cookie refused after a client timeout, system level) pending (TASK-226) |
| Background polls do not extend the session: `GET /me/modules`, polled about every 50 s by `useMyModules`, resolves the session through its own non-sliding dependency (`SessionService.resolve(..., slide=False)` behind a `get_current_user` variant that keeps the absolute-lifetime, ended-session and active-account checks); every other route keeps the sliding check, so idle expiry counts only user-driven requests (CR-006 D-32, TASK-221 QA HIGH 1) | Design | SR-030 AC 1, AC 2; TASK-221 | TS-001 TC-001.12, `backend/tests/auth/test_session_no_slide.py` (10 tests, incl. `test_polling_my_modules_does_not_extend_the_session`, `test_other_routes_still_slide_the_session`, `test_my_modules_with_an_ended_session_is_401`, `test_my_modules_for_an_inactive_account_is_401`, `test_resolve_without_slide_enforces_absolute_expiry`); passed 2026-11-14, TASK-221 QA round 2 |

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

**Change analysis (CR-006, Risk stage, 2026-11-13).** CR-006 changes only the client side of the
session controls: the client countdown came from a hard-coded 15 minutes (PRB-016), the upload
path had no 401 handling (PRB-019) and the idle timer re-armed on every event (PRB-025). A client
timer that runs late leaves a session open on screen while the server has ended it (the next
request is refused), or warns a user too late to extend it; the server-side expiry and revocation,
which the residual rests on, are unchanged. The PRB-009 move of `get_current_user` off the event
loop must not change the session decision: TS-001 runs unchanged. **Expected residual: 3 × 1 →
acceptable, unchanged.** Re-scored from the evidence at the CR-006 verification checkpoint.

**Change analysis (CR-006 D-32, 2026-11-14).** TASK-221 QA round 1 found that the 60 s poll of
`GET /me/modules` slid the server session on every request, so an unattended workstation with an attachment
view open kept its session alive indefinitely. That defeats the idle-expiry control on which this residual
rests. Found before merge. D-32 makes that route check the session without extending it (new control row), so
the server is again the authority for SR-030 AC 1 and AC 2. The non-sliding check can only end a session
earlier, never keep it longer. **Expected residual: 3 × 1 → acceptable, unchanged.** The pre-existing gap that
the client timeout neither logs out nor clears the cache is raised to the human as CR-006 P-18.

**Change analysis (CR-006 D-33, 2026-11-14).** The client deadline is now set only from `me` and extend
responses (PRB-087). Each of those is itself a sliding request, so the client deadline is never later than
the server's. The warning therefore always appears at least 2 minutes before the server would end the
session (SR-030 AC 4). The client deadline is earlier than the server's when the user made other requests
after the last `me` response. Without PRB-089's fix, going Back after the client redirect would then give
the next person a live session, and any request they made would slide it further. With the fix, the client
timeout logs out and clears the cache, so the earlier of the two deadlines applies. The server's own idle
and absolute expiry stay the backstop when the logout cannot reach it. Both fixes land together in TASK-222.
**Expected residual: 3 × 1 → acceptable, unchanged.** Both defects predate CR-006, and the residual rests on
the server expiry, which is unchanged.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## Risks introduced by controls

Aggressive lockout enables a denial-of-service against a known account — RISK-007; mitigated by administrator-initiated unlock.

CR-004 (2026-10-31): the optimistic Redis transaction retries on contention; after its bounded
retries the login is answered 503 with `Retry-After: 1` rather than exceeding the cap (an availability effect
on one login, RISK-007; TASK-205). The start-up refusal of placeholder secrets is a deployment-time
availability effect by design, with a message naming the setting.

CR-006 (2026-11-13): the debounce lets the client deadline run up to 1 s late (SR-026 AC 8); the
server enforces the real expiry. *Superseded by D-33 (2026-11-14): no activity tracking remains.*

CR-006 D-32 (2026-11-14): a route wrongly given the non-sliding check would end a working user's session
early (availability, RISK-007), never extend one. Only `GET /me/modules` uses it, and the test pins both sides.

CR-006 D-33 (2026-11-14): a user who works through requests that do not refresh `me` gets the warning
although the server would keep the session, and is signed out (now also on the server) if they ignore it.
That is an availability effect (RISK-004, RISK-007), recovered by Extend or a sign-in. A logout that fails at
the timeout leaves the session to the server's own idle expiry. The cache is cleared and the redirect happens
anyway.

## Version history

- 1.2 (2026-10-31) — CR-004 Risk stage, §7.4 change analysis (Software Architect role). Control rows added for the CR-004 controls with their planned verification; expected residual stated in "Residual risk"; "Risks introduced by controls" extended. Scores not changed: they are re-scored from the evidence at verification (TASK-202). Content change, so the approval record is cleared and the record returns to review.
- 1.3 (2026-11-06) — TASK-205 (CR-004 D-11): new cause (an ended session brought back by a racing refresh, PRB-064), one control row (conditional refresh, expired members pruned from the cap), TC-001.8 and TC-001.9 as verification, contention effect now 503. Scores unchanged. Content change, so the 1.2 approval record is cleared and the record returns to review.
- 1.4 (2026-11-07) — TASK-206 (CR-004 D-14, D-16): one control row, no credential or secret in operational and proxy logs (SR-043 AC 4, TS-017 TC-017.4). Residual unchanged (3 x 1, acceptable).
- 1.5 (2026-11-07) — TASK-207 (TASK-206 QA findings 2, 6): the log control row names TASK-207 (case-insensitive activation matching; widened started-stack check). Residual unchanged (3 x 1, acceptable). A hand-crafted Referer or a token in another path's query string that reaches the proxy error log is a residual accepted against SR-043 AC 4 (CR-004 D-19), not a change of the scores.
- 1.6 (2026-11-08) — CR-004 Checkpoint F (TASK-202): planned verification replaced by the tests that ran; residual proposed from the evidence, 3 × 1 → acceptable, unchanged; PRB-074 raised to the human as the one open cause. Content change, so `in_review` and the approval record (none) stays cleared.
- (2026-11-10) — Human decision (CR-004 D-21): the residual is accepted unchanged; PRB-074 is accepted as a known anomaly while only development data exists, to be re-evaluated before the first release.
- 1.7 (2026-11-13) — CR-006 Risk stage, §7.4 change analysis (Software Architect role). One control row added (client session timers from the server's expiry, upload through the request helper, debounced tracking; SR-030 AC 8, SR-026 AC 8), TASKs left to the Plan stage; expected residual stated; "Risks introduced by controls" extended. Scores unchanged (3 × 1 → acceptable). Content change, so the approval record (approved 2026-11-10 in chat) is cleared and the record returns to review.
- 1.8 (2026-11-13) — CR-006 Plan gate (D-22): the client-session row names TASK-143, TASK-144 and TASK-222, with TASK-146 for its unit tests. Scores unchanged. Content change, so the approval record is cleared and the record returns to review.
- 1.9 (2026-11-14) — CR-006 D-32 (TASK-221 QA round 1 HIGH 1), §7.4 change analysis (Software Architect role). One control row added (background polls do not extend the session: non-sliding check on `GET /me/modules`; verification planned in TASK-221). The client-session row's "Server enforcement … unchanged" names that exception. Scores unchanged (3 × 1 → acceptable). Content change, so the approval record (approved 2026-11-13) is cleared and the record returns to review.
- 1.9 (2026-11-14, same version, still `in_review`) — Verification cell of the background-poll row filled with the TASK-221 tests (TS-001 TC-001.12) after QA round 2 approved them.
- 1.10 (2026-11-14) — CR-006 D-33 (PRB-087 "Server responses only"; PRB-089 `major`), §7.4 change analysis (Software Architect role). The client-session row now says the deadline is re-armed only by `me` and extend responses, with no activity listener. New row: the client timeout ends the session (logout, cache cleared, one redirect; TASK-222, verification planned). The debounce line is superseded, and one introduced-risk line is added. Scores unchanged (3 × 1 → acceptable). Content change; the record stays `in_review` with no approval record.
- 1.11 (2026-11-14) — CR-006 D-34 (PRB-090, `major`): the "client timeout ends the session" row names the warning dialog route (countdown at 0, extend 401) through `handleExpired`, and the planned verification covers it. Same hazard as PRB-089; scores unchanged (3 × 1 → acceptable). Stays `in_review`.
- 1.11 (2026-11-14, same version, still `in_review`) — Verification cells of the client-session and "client timeout ends the session" rows filled with the TASK-222 tests (TS-001 TC-001.13) after QA round 2 approved them.
- 1.11 (2026-11-14, same version, still `in_review`) — Client-session row: the PRB-017 items (fake timers, upload 401, `csrf.ts`, generated-types drift) filled with the TASK-146 tests after QA approved them.
