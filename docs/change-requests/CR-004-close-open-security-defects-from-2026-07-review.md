---
id: CR-004
type: change-request
title: Close the open security defects from the 2026-07 review and audit
status: closed
version: "1.22"
author: Carlos Santiago Liceras
created: "2026-10-31"
updated: "2026-11-10"
branch: fix/review-2026-07-security
risk_impact: affects_controls
links:
  - target: PRB-003
    relation: resolves
  - target: PRB-004
    relation: resolves
  - target: PRB-005
    relation: resolves
  - target: PRB-007
    relation: resolves
  - target: PRB-010
    relation: resolves
  - target: PRB-011
    relation: resolves
  - target: PRB-014
    relation: resolves
  - target: PRB-018
    relation: resolves
  - target: PRB-023
    relation: resolves
  - target: PRB-026
    relation: resolves
  - target: PRB-027
    relation: resolves
  - target: PRB-028
    relation: resolves
  - target: PRB-029
    relation: resolves
  - target: PRB-061
    relation: resolves
  - target: PRB-063
    relation: resolves
  - target: PRB-056
    relation: resolves
  - target: PRB-062
    relation: resolves
  - target: PRB-064
    relation: resolves
  - target: PRB-065
    relation: resolves
  - target: PRB-066
    relation: resolves
  - target: PRB-067
    relation: resolves
  - target: PRB-068
    relation: resolves
  - target: PRB-069
    relation: resolves
  - target: PRB-070
    relation: resolves
  - target: PRB-071
    relation: resolves
  - target: PRB-076
    relation: resolves
  - target: PRB-077
    relation: resolves
  - target: SR-005
    relation: relates_to
  - target: SR-009
    relation: relates_to
  - target: SR-016
    relation: relates_to
  - target: SR-022
    relation: relates_to
  - target: SR-023
    relation: relates_to
  - target: SR-024
    relation: relates_to
  - target: SR-029
    relation: relates_to
  - target: SR-030
    relation: relates_to
  - target: SR-031
    relation: relates_to
  - target: SR-032
    relation: relates_to
  - target: SR-034
    relation: relates_to
  - target: SR-041
    relation: relates_to
  - target: SR-042
    relation: relates_to
  - target: SR-043
    relation: relates_to
  - target: RR-001
    relation: relates_to
  - target: RR-002
    relation: relates_to
  - target: RR-003
    relation: relates_to
  - target: RR-004
    relation: relates_to
  - target: NFR-004
    relation: relates_to
  - target: NFR-007
    relation: relates_to
  - target: RISK-001
    relation: relates_to
  - target: RISK-005
    relation: relates_to
  - target: RISK-006
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: RISK-008
    relation: relates_to
  - target: RISK-011
    relation: relates_to
  - target: TASK-137
    relation: relates_to
  - target: TASK-138
    relation: relates_to
  - target: TASK-139
    relation: relates_to
  - target: TASK-140
    relation: relates_to
  - target: TASK-142
    relation: relates_to
  - target: CR-002
    relation: relates_to
  - target: RISK-004
    relation: relates_to
  - target: TASK-185
    relation: relates_to
  - target: TASK-186
    relation: relates_to
  - target: TASK-187
    relation: relates_to
  - target: TASK-188
    relation: relates_to
  - target: TASK-189
    relation: relates_to
  - target: TASK-190
    relation: relates_to
  - target: TASK-191
    relation: relates_to
  - target: TASK-192
    relation: relates_to
  - target: TASK-193
    relation: relates_to
  - target: TASK-194
    relation: relates_to
  - target: TASK-195
    relation: relates_to
  - target: TASK-196
    relation: relates_to
  - target: TASK-197
    relation: relates_to
  - target: TASK-198
    relation: relates_to
  - target: TASK-199
    relation: relates_to
  - target: TASK-200
    relation: relates_to
  - target: TASK-201
    relation: relates_to
  - target: TASK-202
    relation: relates_to
  - target: TASK-203
    relation: relates_to
  - target: TASK-204
    relation: relates_to
  - target: TASK-205
    relation: relates_to
  - target: TASK-206
    relation: relates_to
  - target: TASK-207
    relation: relates_to
  - target: TASK-208
    relation: relates_to
  - target: ADD-005
    relation: relates_to
  - target: ADD-006
    relation: relates_to
  - target: ADD-007
    relation: relates_to
  - target: ADD-013
    relation: relates_to
  - target: ADD-016
    relation: relates_to
  - target: ADD-017
    relation: relates_to
  - target: ADD-018
    relation: relates_to
  - target: ADD-025
    relation: relates_to
  - target: ADD-026
    relation: relates_to
tags:
  - security
  - privacy
  - class:B
  - issue:sancharly/medhub#27
---

# CR-004 — Close the open security defects from the 2026-07 review and audit

## Reason

The 2026-07 code review (`docs/reports/CODE-REVIEW-2026-07.md`) and the audit
(`docs/implementation-plan/AUDIT-FINDINGS.md`) left thirteen security and privacy problem reports
open. None is `critical` and none is a live breach today. Each one weakens a risk control that
RISK-001, RISK-005, RISK-006, RISK-007, RISK-008 or RISK-011 relies on, or leaves the control
enforced only by convention:

- **Audit trail (RISK-006):** audit rows can be updated or deleted by the application, the secret
  scrub is pattern-limited (PRB-005), authorization and consent rows carry no source address
  (PRB-010), and two code paths decide access outside the authorization service without auditing
  the decision (PRB-026, PRB-027).
- **Access control and account takeover (RISK-001, RISK-005):** CSRF exemptions match by prefix
  (PRB-003), the frontend mounts every route for every role (PRB-014), the lockout service is an
  optional parameter and an unused secret implies signed sessions (PRB-018), the session cap is
  not atomic (PRB-023), and the deployment ships known default secrets (PRB-007).
- **Keys and encryption (RISK-011, RISK-007):** the ciphertext names no key, so a key cannot be
  rotated (PRB-004), and one key protects both the encrypted fields and the attachments (PRB-007,
  carried over by CR-002 D-6).
- **Personal data (RISK-008):** worker logs carry email addresses outside the erasure machinery
  (PRB-011).
- **Other:** the retrieval rate limit is keyed on the proxy, so all callers share one bucket
  (PRB-029, RISK-007), and the module version expression accepts trailing garbage (PRB-028, no
  hazard).

One CR bundles them because they come from the same review, share the same records (SR-023,
RISK-001/005/006/011) and one verification run (backend and frontend suites, a started stack,
TASK-113's security review and `traceability-check`). Several of them also share code: PRB-010
and PRB-029 need the same client address rule (SR-042), and PRB-026 and PRB-027 share one fix
pattern.

Source: GitHub issue sancharly/medhub#27.

## Scope

### In scope

Each PRB, the requirement its fix restores and its TASKs (created or updated at the Plan stage;
order and dependencies in "Plan").

| PRB | Crit. | Requirement restored (AC) | TASK |
|---|---|---|---|
| PRB-003 CSRF exemption prefix matching | major | SR-031 AC 3 | TASK-139 |
| PRB-004 Ciphertext envelope without key id | major | SR-022 AC 3, **AC 6 to AC 8 (new in 1.5)**; RR-003 | TASK-193, 194, 195 |
| PRB-005 Audit append-only by convention; pattern-limited scrub | major | SR-023 AC 5, **AC 8, AC 9 (new in 1.4)**; RR-004 | TASK-190, 191, 192 |
| PRB-007 Root container and insecure default secrets (remainder after CR-002) | major | **SR-041 AC 1 to AC 6 (new)**; SR-040 AC 2 (already met) | TASK-197, 203, 198, 191, 196 (and 140) |
| PRB-010 Authz and consent audit without source IP | major | SR-023 **AC 6 (new)**, SR-042 AC 1 to AC 3 | TASK-185, TASK-137 |
| PRB-011 Worker logs emit email addresses | major | **SR-043 AC 1 to AC 3 (new)**; SR-024 | TASK-138 |
| PRB-014 Frontend mounts every route for any role | major | SR-005 AC 1, AC 4; SR-009 AC 2, AC 3 (defence in depth, see Q-4) | TASK-142 |
| PRB-018 Unused signing secret; optional lockout service | minor | SR-029 AC 1; SR-030 (opaque tokens, AC 5) | TASK-140 |
| PRB-023 Non-atomic session-cap eviction | major | SR-030 AC 7 | TASK-199 |
| PRB-026 Authorization embedded in the repository | major | SR-005 AC 1, AC 3; SR-023 **AC 7 (new)**; design constraint ADR-0006 | TASK-187 |
| PRB-027 Direct role comparisons in identity services | major | SR-032 AC 1, AC 4, AC 5; SR-034 AC 1; SR-023 **AC 7 (new)**; ADR-0006 | TASK-188, 189 |
| PRB-028 Module version regex accepts trailing garbage | minor | SR-016 AC 1 (module contract) | TASK-200 |
| PRB-029 Rate limit keyed on the proxy address | minor | **SR-042 AC 1 to AC 5 (new)**; SR-024 retrieval path, ADR-0013 | TASK-185, 186 |
| PRB-056 Empty `CORS_ORIGINS` in the template breaks start-up (added in 1.4) | minor | SR-041 AC 4 (the template starts the stack) | TASK-193 |
| PRB-061 The celery-worker container runs gunicorn, not Celery (found in TASK-203; added in 1.2) | major | SR-023, SR-024, SR-030, SR-041 AC 3 (worker start-up refusal, effective in the started stack) | TASK-191 |
| PRB-063 Attachment download fails for file names outside Latin-1 (found in TASK-196; added in 1.7) | major | SR-013 AC 3 (download of any stored file name); SR-023 AC 2 (a failed download is audited, ADR-0016); RISK-007, RISK-006 | TASK-204 |
| PRB-064 Session refresh can re-create an ended session (found in the TASK-199 review; added in 1.10) | major | SR-030 AC 5, AC 1 to AC 3, AC 7; RISK-005 | TASK-205 |
| PRB-065 Expired session ids count toward the session cap (found in the TASK-199 review; added in 1.10) | minor | SR-030 AC 7 (oldest active); RISK-005 | TASK-205 |
| PRB-066 Login never reports an evicted session (found in the TASK-199 review; added in 1.10) | minor | SR-030 AC 7 (notification); RISK-005 | TASK-205 |
| PRB-067 A failing /me request is re-requested in a tight loop (found in the TASK-142 review; added in 1.11) | major | availability; not an SR criterion (SR-005 and SR-009 guard unchanged) | TASK-142 |
| PRB-068 The activation token is written to the backend error log and the proxy access log (found in the TASK-138 review; added in 1.13) | major | SR-043 AC 4 (new in SR-043 1.1, approved 2026-11-07) and AC 2 (logs), SR-033 (single-use activation link); RISK-005 | TASK-206 |
| PRB-069 Attachment file names have no length limit, so a long name makes the proxy answer 502 (found in the TASK-204 review; added in 1.13) | minor | SR-013 AC 1, AC 3; SR-023 AC 2; RISK-007, RISK-006 | TASK-206 |
| PRB-070 The e-mailed activation link does not match the app's activation route (found while planning TASK-206; added in 1.14) | major | SR-033 AC 1, AC 3, AC 7; RISK-009 | TASK-206 |
| PRB-071 The API process cannot enqueue Celery tasks, so no e-mail is sent and no session kill is propagated by the worker (found on the TASK-206 started stack; added in 1.16) | critical | SR-033 AC 1, AC 3, AC 7 (activation e-mail), SR-034 AC 2 (session-kill propagation), SR-024 (erasure code e-mail), SR-035 (appointment notification); RISK-009, RISK-005 | TASK-206 |
| PRB-076 The stack can fail to start because the fixed `medhub` subnet overlaps a network Docker picks for another Compose network (found in the TASK-202 QA review; added in 1.20) | major | SR-042 AC 3 (the fixed proxy address); RISK-007 | TASK-202 (round 2) |
| PRB-077 The object store cannot start on current Docker Compose because its volume name renders empty (found by the first hosted CI run; added in 1.22) | major | SR-041; RISK-007 | TASK-208 |

Existing TASKs whose links will need updating at the Plan stage: TASK-137 (add `implements`
SR-042), TASK-138 (add `implements` SR-043).

### Requirements decision

Where an existing requirement already states the expected behaviour, the fix restores it and no
requirement changes: SR-005, SR-009, SR-016, SR-029, SR-030, SR-031, SR-032, SR-034.

Where no requirement stated it, the Product Owner wrote or amended one (all `in_review`, for the
human to approve):

- **SR-022 1.5** (amended): key identifier in every field-level ciphertext, no existing value made
  unreadable, a documented and rehearsed rotation. Driven by RR-003 ("documented key lifecycle").
- **SR-023 1.4** (amended): source address, every authorization decision audited, append-only
  enforced by the database, no secret under any field name. These were RR-004's acceptance
  criteria that SR-023 did not carry down.
- **SR-041 1.0** (new): non-root containers, no default or placeholder secret, separate
  field-encryption and object-store SSE keys. Extends SR-040 from the object store to the whole
  deployment.
- **SR-042 1.0** (new): one trusted-proxy rule for the originating client address; the
  retrieval rate limit keyed on it.
- **SR-043 1.0** (new): no personal data in operational logs.

No RR was added: RR-001, RR-002, RR-003 and RR-004 already cite the clauses that drive these.

### Out of scope

- The other PRBs from the same review that are not security defects (PRB-006, PRB-008, PRB-009,
  PRB-012, PRB-013, PRB-015 to PRB-017, PRB-019 to PRB-022, PRB-024, PRB-025, PRB-030 onwards).
- Choosing which further database columns are encrypted at field level (Q-2). This CR makes
  rotation possible for the columns that exist.
- A change to the session token format. Sessions stay opaque random tokens (SR-030).
- Moving from trusted modules to sandboxed modules (ADR-0005). PRB-028 only tightens validation.
- Changing a PRB to `resolved` or `closed`, or a record to `approved`. Only the human approves.

### Boundaries

- **Ask first:** any change that can make stored values or attachments unreadable (the key
  identifier migration, the key separation of SR-041 AC 5); any database grant change applied to
  an existing database (SR-023 AC 8); a new runtime dependency.
- **Never:** put a secret value in the repository, a log or an error message; set a record
  `approved`; edit an `approved` record without bumping its version and clearing its approval.

### Risk impact (§7.4)

Preliminary classification: **`affects_controls`**. Every change strengthens or restores an
existing control of RISK-001, RISK-005, RISK-006, RISK-007, RISK-008 or RISK-011. No new hazard
is expected and class B is unchanged. Two changes need a fail-safe because they can reach
RISK-007 (information unavailable) if they go wrong: the key-identifier migration and rotation
(SR-022 AC 7, AC 8) and the key separation for stored attachments (SR-041 AC 5). The
`REVOKE` of SR-023 AC 8 can break a code path that updates audit rows today, if one exists.

The Risk stage confirms or revises this, and revisits the residual scores of RISK-001 (2 × 2),
RISK-005 (3 × 1), RISK-006 (2 × 2) and RISK-011 (3 × 2, alarp), as the issue asks. RISK-007 and
RISK-008 are also touched.

## Verification approach

IEC 62304 §8.2.1 (change approval), §8.2.3 (verification of changes) and §7.4.3 (verification of
risk-control measures after a change).

- **Audit trail (SR-023 AC 6 to AC 9; PRB-005, PRB-010, PRB-026, PRB-027):** real-database tests
  (testcontainers PostgreSQL, the application's own role): an `UPDATE` and a `DELETE` on
  `audit_log` fail with a permission error; an authorization-denied request records the client
  address; each formerly repository- or service-local decision produces an audit entry; issued
  secrets passed under arbitrary field names are absent from the stored row. A static check that
  no role comparison remains outside the authorization service. Recorded in TS-009 or a new TS.
- **Client address and rate limit (SR-042; PRB-029):** API tests with a trusted and an untrusted
  peer, a forged `X-Forwarded-For`, and two clients through one proxy. One check on a started
  stack that the audit address is not the proxy's.
- **Encryption keys (SR-022 AC 6 to AC 8; PRB-004):** unit tests for the envelope (current key,
  retired key, unknown key refused), a test against a database populated in the old format, and a
  rotation rehearsal against a backup copy, recorded in the next TR.
- **Deployment (SR-041; PRB-007):** tests that parse the Compose file and the environment template
  for defaults; negative start-up tests per secret setting and placeholder; image and running-
  process UID checks on a started stack; a read-back of attachments stored before the key
  separation. `infra/tests/` and the smoke test are the existing homes.
- **Logs (SR-043; PRB-011):** log-capture tests of the email worker task's success and failure
  paths and of the redaction filter.
- **CSRF, lockout, session cap, module version (PRB-003, PRB-018, PRB-023, PRB-028):** the
  regression tests named in TASK-139 and TASK-140; a concurrency test that runs simultaneous
  logins against a real Redis and asserts at most 3 sessions remain; discovery rejecting a
  version with trailing characters.
- **Frontend guards (PRB-014):** Vitest tests of the route guard for allowed, denied and unknown
  roles, and a test that a role-scoped route in the navigation config without a guard fails.
- **Negative control:** for each new test, a mutation or removal of the fix makes it fail.
- **Records:** `traceability-check` with no errors on this CR's records; human approval of the
  amended and new SRs and of the Risk-stage results.
- **Regression:** the full CI pipeline on the branch head.

Results go into the next test report (TR) for the release.

## Assumptions

- **A-1:** No release exists (`docs/releases/` is absent), so no released version in use is
  affected and no notification is needed (§9.3).
- **A-2:** This CR's `status` is `open`. The issue's hand-off asked for `draft`, but `draft` is
  not in the change-request status set (`open`, `in_progress`, `closed`, `rejected`). The human's
  approval of the Specify gate is recorded as a decision in this record, as in CR-001 to CR-003.
- **A-3:** `audit_log.actor_id` is not a foreign key (`backend/app/db/models/audit.py`), so no
  cascade updates audit rows when an account is deleted. The architect confirms that no code path
  updates or deletes audit rows before the `REVOKE` (SR-023 AC 8). **Confirmed at the Plan stage
  (D-2)**; the `REVOKE` needs a non-superuser runtime role (ADR-0017).
- **A-4:** The current rate-limit values (5 attempts per 3600 s, ADR-0013) stay. Only the key
  changes.
- **A-5:** Parts of PRB-007 and PRB-004 look stale against the current tree (Q-1). This CR still
  resolves both: the new requirements make the remaining parts verifiable whatever the PRB text
  says.

## Open questions

All answered by the human on 2026-10-31 (D-1). Kept for the record.

- **Q-1 (stale PRB observations):** *Answered:* the architect records the true current state in
  each PRB. Done at the Plan stage: every PRB in scope has a `## Investigation` section (§9.2)
  with `file:line` references. Summary: PRB-007 is partly stale (backend already `USER medhub`; no
  `:-default` on a secret), and its remainder is the frontend image, the template placeholders, an
  unguarded `POSTGRES_PASSWORD`, the superuser application credential and the key reuse. PRB-004's
  "no PHI column uses it" is stale (`clinical_entry.description` does); the key-id defect stands.
  PRB-005 is partly stale (migration 0006 has silent `DO INSTEAD NOTHING` rules) and found a live
  instance (the logout event stores the session token). PRB-026's location is stale (commit
  `eca0a68` moved the branch from the repository into `AppointmentService`); the defect stands.
  PRB-011's mechanism is corrected (the current formatters drop `extra`; the worker has no logging
  configuration). PRB-027 is wider than reported (router checks too). **No PRB's defect is gone
  entirely; none is recommended for rejection.**
- **Q-2 (field-level PHI scope):** *Answered:* no further encrypted columns in this CR.
- **Q-3 (key separation):** *Answered:* yes, in this CR, including the migration of the SSE key
  for existing attachments, rehearsed on a backup (TASK-196).
- **Q-4 (PRB-014):** *Answered:* no client-side AC on SR-005; TASK-142 is defence in depth.
- **Q-5 (SMTP password):** *Answered:* SMTP without authentication is supported; `SMTP_PASSWORD`
  is required only when `SMTP_USER` is set (TASK-197).
- **Q-6 (split):** *Answered:* one CR, no split.

New, for the human (Plan stage):

- **Q-7 (traceability-only links, for the human):** SR-032 and SR-034 carry no `mitigates` link,
  although CR-004's TASK-188 implements their authorization rules as RISK-001 controls. Add
  `mitigates` RISK-001 to both (and RISK-005 to SR-034, whose session kill on deactivation is a
  takeover control) as a traceability-only change that keeps their approval, as in their earlier
  1.1 entries? *Answered (plan gate, 2026-10-31):* yes; SR-032 1.1 and SR-034 1.2 carry the links.
- **Q-8 (RISK-011 loss path, for the human, at verification):** CR-004 removes the rotation and
  key-sharing causes of RISK-011, not the key-loss cause (no backup procedure, PRB-057). Re-score
  RISK-011 to 3 × 1 only once PRB-057 is resolved, or accept the loss path for development use and
  re-score now? *Answered (plan gate, 2026-10-31):* keep 3 × 2 `alarp` until PRB-057 is resolved.
- **Q-9 (PRB candidate, outside CR-004):** the activation token and the anonymized-data retrieval
  code are passed to Celery tasks as arguments (`backend/app/workers/email_tasks.py:76,140`), so
  they sit in plaintext in the Redis broker and result backend. Not a log (SR-043) and not the
  audit trail (SR-023); no requirement covers it. *Recommended: raise a PRB (minor) and decide its
  CR separately.*

## Decisions

- **D-1 (human, 2026-10-31, before the Plan stage):** one CR (Q-6). Q-1 to Q-5 answered as above.
  The architect confirms or refutes A-3 from the code.
- **D-2 (Plan stage, 2026-10-31, Software Architect role; binding with the human's approval of
  the plan):**
  - **A-3 confirmed.** No code path under `backend/app`, `backend/modules` or `backend/scripts`
    updates or deletes `audit_log` rows (PRB-005 Investigation). Three test clean-ups delete them
    and move to the owner connection (TASK-190).
  - **The `REVOKE` alone would not work**: the application connects as the database superuser
    that owns the table. SR-023 AC 8 needs a separate runtime role
    ([ADR-0017](../design/adr/0017-database-roles-and-append-only-audit-log.md), `Proposed`).
  - Envelope `mh1:<kid>:…` with the prefix as AES-GCM associated data; existing values
    re-encrypted by migration 0010; rotation by a re-encryption command; SSE key separated by a
    copy migration ([ADR-0018](../design/adr/0018-field-encryption-key-identifier-and-key-separation.md), `Proposed`).
  - The originating client address is an application-level rule with a `TRUSTED_PROXIES` setting
    and a fixed proxy address ([ADR-0019](../design/adr/0019-originating-client-address-trusted-proxy-rule.md), `Proposed`).
  - PRB-026 and PRB-027 need no new ADR: ADR-0006 already decides the single decision point.
  - New design record ADD-026 (SI-DEPLOY). ADD-005, 006, 007, 013, 016, 017, 018 and 025 revised,
    all `in_review`.
  - The session cap uses `WATCH`/`MULTI` rather than a Lua script, so no new dependency is needed
    (`fakeredis` runs Lua only with `lupa`).
  - The frontend image stays the pinned `nginx` image, run as its `nginx` user on 8080: no new
    SOUP item.
- **D-3 (human decision 2026-10-31, PRB-061 folded into TASK-191):** the `celery-worker` container
  runs gunicorn because `backend/entrypoint.sh` never runs `"$@"` (PRB-061 Investigation), and no
  beat process exists. The fix is part of TASK-191, which already moves the migrations into
  `db-migrate`: the entrypoint becomes `exec "$@"`, gunicorn is the default `CMD`, and the started
  stack must show the worker and beat running. PRB-061 is added to the Scope table and to `links`.
- **D-4 (human decision 2026-11-01):** accept the window between TASK-190 and TASK-191; branch not
  merged, tagged or deployed to a shared database until TASK-191 lands.
- **D-5 (human decision 2026-11-01):** accept the window between TASK-193 and TASK-194, in which
  existing field-encrypted values (unprefixed) cannot be read through the ORM. The branch is not
  merged, tagged or deployed to a database holding field-encrypted values until TASK-194 lands.
  No start-up guard: once TASK-194's migration 0010 runs in `db-migrate`, which completes before
  the application services start, the window closes structurally.
- **D-6 (human decision 2026-11-01):** PRB-056 (empty `CORS_ORIGINS` in the template) is folded
  into CR-004 and fixed in TASK-193, which already edits `config.py` and the template. PRB-056 is
  added to the Scope table and to `links`.
- **D-7 (human decisions 2026-11-01, TASK-194 QA round 1):** PRB-062 (DEPLOY.md runs `db-migrate`
  without `--build`) is fixed in TASK-194. A row that migration 0010 cannot decrypt gets a documented
  manual recovery procedure in `infra/DEPLOY.md`, with no code change. The API's `strip()` of clinical
  descriptions (`clinical/service.py:49`, older than CR-004) is accepted behaviour, with no PRB. The
  human approves the rehearsal result of migration 0010 (QA's rehearsal: 315 rows, identical per-row
  hashes, refusal on a wrong key or a damaged row, survival of a SIGKILL).
- **D-8 (human decisions 2026-11-01, TASK-195 QA round 1):** the `--verify-key-ids` guard stays the
  last step of `db-migrate`. QA approval of a task may set the PRB it resolves to `resolved`, as done so
  far; `closed` remains a human step at release. This clarifies "Out of scope" (Scope): only the human
  sets `closed` or approves records other than tasks and test records.
- **D-9 (human decision 2026-11-02, TASK-196 QA round 1):** PRB-063 (attachment download fails for file
  names outside Latin-1) is folded into CR-004 and fixed in a new task TASK-204.
- **D-10 (human decision 2026-11-02, TASK-196 QA round 2):** after two QA rounds, TASK-196 is accepted with the
  round-2 text fix (DEPLOY.md rollback split into paths (a) from `f7d79fc` and (b) from a pre-CR-004 release, using
  QA's verified sequence; step 1 clarifications) and no QA re-review. The orchestrator records TASK-196, TS-008,
  TS-014 and TS-015 as `approved` and PRB-007 as `resolved` (D-8) on this decision.
- **D-11 (human decision 2026-11-06):** PRB-064, PRB-065 and PRB-066 (session defects found in the TASK-199
  review) are folded into CR-004 and fixed in TASK-205.
- **D-12 (human decision 2026-11-06):** PRB-067 (the /me refetch loop found in the TASK-142 review) is folded into CR-004 and fixed in TASK-142.
- **D-13 (human decision 2026-11-06):** administrators get the Appointments page and its navigation entry (SR-010 AC 4, SR-011 AC 3).
- **D-14 (human decision 2026-11-07):** PRB-068 (activation token in logs) and PRB-069 (unbounded attachment names) are
  folded into CR-004 and fixed in TASK-206, together with forwarding Celery's --loglevel (TASK-138 QA follow-up).
- **D-15 (human decision 2026-11-07):** TASK-142, after three QA rounds, takes QA's verified one-line fix for R3-1
  followed by one short QA check.
- **D-16 (human decisions 2026-11-07):** SR-043 gains an AC for credentials and secrets in operational and proxy
  logs; PRB-070 (activation link does not match the app route) is folded into CR-004 and fixed in TASK-206; the
  attachment name limit is 255 UTF-8 bytes.
- **D-17 (human decision 2026-11-07):** PRB-071 (the API process cannot enqueue Celery tasks) is `critical` and is fixed in
  TASK-206, not left to a later change request.
- **D-18 (human decisions 2026-11-07):** TASK-207 takes QA's two MEDIUM fixes and the LOW record fixes from TASK-206;
  PRB-072, PRB-073 and PRB-074 are recorded as known anomalies outside CR-004, and PRB-013 stays open.
- **D-19 (human decision 2026-11-07):** a hand-crafted Referer or a token in another path's query string can reach the proxy
  error log on an upstream failure or 413; accepted as a residual against SR-043 AC 4, listed for the release's
  residual-anomaly evaluation. SR-043's text is not edited; TASK-201 carries the note.
- **D-20 (orchestrator):** PRB-076, a start-up failure introduced by TASK-185's fixed subnet, is fixed in TASK-202 round 2. `medhub` moves out of Docker's default address pools (`10.77.77.0/24`); the proxy address, `ip_range` and `TRUSTED_PROXIES` follow.
- **D-21 (human decisions 2026-11-10, CR-004 close of build):** the residuals proposed by TASK-202 are accepted unchanged: RISK-001 2×2, RISK-004 3×2 ALARP,
  RISK-005 3×1, RISK-006 2×2, RISK-007 3×2 ALARP, RISK-008 2×2, RISK-009 2×2, RISK-011 3×2 ALARP. PRB-074 (plaintext task arguments in Redis) is accepted as a
  known anomaly while only development data exists and is re-evaluated before the first release. Accepted as documented residuals: the reverse-proxy master
  runs as UID 0; `celery-beat` and `db-migrate` hold settings they do not use; a rejected module manifest only logs a warning (see PRB-075). The human
  approved the RISK, ADD and SOUP records left in review by CR-004.
- **D-22 (human decision 2026-11-10):** PRB-077, found by the first hosted CI run on PR #38, is fixed in TASK-208: the volume's default name is written out in the Compose file. TASK-202 returns to `draft` until a hosted run is green.

## Change analysis (Risk stage, §7.4, 2026-10-31)

The Software Architect role ran this analysis. Scales and matrix: `docs/medtrace.yml` (5 × 5
`risk_matrix`) and PLAN-005.

- **Records consulted:** RISK-001, 004, 005, 006, 007, 008, 011; SR-005, 009, 016, 022, 023, 024,
  029, 030, 031, 032, 034, 040, 041, 042, 043; the 13 PRBs; ADR-0006, 0010, 0011, 0013, 0015, 0016;
  ADD-005..025; SOUP-004, 005, 011, 013, 014, 020, 021, 024, 036.
- **Code read:** see each PRB's Investigation; also `infra/docker-compose.yml`, `infra/.env.example`,
  `backend/entrypoint.sh`, `backend/Dockerfile`, `frontend/Dockerfile`,
  `infra/reverse-proxy/nginx.conf`, `backend/app/db/alembic/versions/0006_*.py`,
  `backend/app/core/logging.py`, `backend/app/api/deps.py`, `backend/scripts/migrate_object_store.py`.

**Conclusion.** `risk_impact: affects_controls` is **confirmed**.

- **No new hazard; class B unchanged.** Every harm a change can reach is already in RISK-001, 004,
  005, 006, 007, 008 or 011, at severity 3 at most. Class B covers it.
- **RISK-004 is added to the analysis**: moving the authorization checks can deny a legitimate
  access (the CR text listed RISK-001/005/006/007/008/011 only).
- **New causes introduced by the change itself**, each with a control in the plan:
  1. the field migration, the rotation and the SSE key separation can make data unreadable
     (RISK-011, RISK-007): one transaction with rollback, `--check`, read-back, source read only,
     rehearsals on backup copies, "ask first";
  2. the runtime-role grants can make a statement fail (RISK-007): grants re-applied after every
     migration, real-database tests as the runtime role, a rehearsal;
  3. the authorization moves can allow or deny wrongly (RISK-001, RISK-004): characterisation
     decision-table tests before each move;
  4. a wrong `TRUSTED_PROXIES` silently makes every address the proxy's (RISK-006): started-stack check;
  5. start-up refusals (secrets, keys, `db-migrate`) are deployment-time availability effects by
     design, each naming the setting (RISK-007);
  6. typed audit fields refuse a caller's bad value instead of writing a row (RISK-006): the safer
     direction, logged without the value.
- **A-3 holds**, so the `REVOKE` breaks no application path; it does break three test clean-ups,
  which TASK-190 moves to the owner connection.
- **PRB-028 / SR-016: no impact** (§7.4.1). Modules are trusted, reviewed code (ADR-0005); a
  malformed version cannot reach a hazardous situation. No RISK record is touched for it.

| Change (tasks) | Software items | §7.4.1 contribution | §7.4.2 controls affected | §7.4.3 verification |
|---|---|---|---|---|
| Client address rule; audit address; rate limit (185, 137, 186) | SI-API, SI-AUDIT, SI-DEPLOY | Removes a forgeable or missing address and the shared bucket. New: silent misconfiguration (cause 4) | RISK-006 (strengthened), RISK-007 (strengthened) | TS-016 TC-016.1..5, TS-009 TC-009.9 |
| Single decision point (187, 188, 189) | SI-AUTHZ, SI-APPT, SI-IDENTITY, SI-API | Removes divergent and unaudited decisions. New: decision changed in the move (cause 3) | RISK-001, RISK-006 (strengthened), RISK-004 (new control) | TS-002 TC-002.7, .8; TS-003 TC-003.6; TS-009 TC-009.10 |
| Typed audit fields; logout token (192) | SI-AUDIT, SI-API | Removes a stored credential. New: refused row (cause 6) | RISK-006, RISK-005 | TS-009 TC-009.12 |
| Runtime DB role; `db-migrate` (190, 191) | SI-PERSIST, SI-DEPLOY | Append-only by privilege; no superuser application credential. New: missing grant (cause 2) | RISK-006, RISK-001 (strengthened), RISK-007 | TS-009 TC-009.11, TS-015 TC-015.2, rehearsal |
| Secrets refused; template; non-root (140, 197, 203, 198) | SI-AUTH, SI-DEPLOY | Removes known credentials and a root process. New: refusals (cause 5) | RISK-001, RISK-005, RISK-011 (strengthened), RISK-007 | TS-015 TC-015.1..4, TS-001 TC-001.7 |
| Key envelope; migration; rotation (193, 194, 195) | SI-PERSIST | Makes rotation possible. New: unreadable values (cause 1) | RISK-011, RISK-007 | TS-008 TC-008.9..11, rehearsal |
| SSE key separation (196) | SI-OBJSTORE, SI-DEPLOY | One key no longer reaches both stores. New: unreadable attachments (cause 1) | RISK-011, RISK-007 | TS-014 TC-014.7, TS-015 TC-015.3, rehearsal |
| Log redaction (138) | SI-WORKER, SI-API | Removes the uncontrolled PII copy | RISK-008 (strengthened) | TS-017 TC-017.1..3 |
| CSRF exact match; session cap; route guard (139, 199, 142) | SI-API, SI-AUTH, SI-FE-SHELL | Remove latent bypasses; guard is defence in depth; PRB-067 availability fix (a failing `/me` is no longer refetched in a loop and shows a retry alert) | RISK-005, RISK-001 | TS-011 TC-011.6, TS-001 TC-001.6, TS-002 TC-002.9 |
| Module version (200) | SI-MODHOST | None (no hazard) | none | TS-010 TC-010.5 |
| Download file names; failed download audited (204, added in 1.8) | SI-API, SI-ATTACH | Removes the 500 for file names outside Latin-1 and the header-injection path; a failed download now leaves FAILURE evidence. New: none (header built in one place, never raises) | RISK-007, RISK-006 (strengthened) | TS-007 TC-007.9, TC-007.10 |
| Session refresh, expired members, eviction report (205, added in 1.10) | SI-AUTH, SI-API | Removes a race that brings back an ended session (logout, eviction, password-change kill); the cap counts live sessions only; the eviction notice is shown. New: a refresh that loses the race answers 401 (the safe direction); cap contention answers 503 with `Retry-After` | RISK-005 (strengthened) | TS-001 TC-001.8..10 |
| Token-free logs, activation link, bounded names, worker log level (206, added in 1.13; activation link and SR-043 1.1 AC 4 in 1.14; API task dispatch, PRB-071, in 1.16) | SI-API, SI-ATTACH, SI-WORKER, SI-DEPLOY, SI-FE-CORE | Removes a stored credential from the backend, proxy and frontend-container logs (SR-043 1.1 AC 4: no request line, query string or header in any proxy log format, no Referer from the activation page); the e-mailed activation link reaches the activation page (PRB-070); the API process dispatches tasks to the configured broker, so activation, erasure-code and appointment e-mails are sent and the deactivation task reaches the worker (PRB-071; `app/main.py` lifespan sets the configured Celery app as the process default); a long name can no longer make a download fail at the proxy; `--loglevel` works again. New: names over 255 UTF-8 bytes are refused at upload (400, shown to the user); long stored names download under a shortened name; nginx error-log entries for activation paths only at `crit` | RISK-005, RISK-007, RISK-006, RISK-009 (strengthened) | TS-017 TC-017.4, .5; TS-007 TC-007.11; TS-003 TC-003.3 |
| TASK-206 QA follow-ups (207, added in 1.18) | SI-WORKER, SI-DEPLOY, SI-IDENTITY, SI-APPT | Dispatch no longer waits on a result store (`task_ignore_result`: the 20 s block inside a request's transaction when Redis is unreachable is gone); the activation redaction and locations match without case (`~*`), so the case variants of the activation URL are redacted and send `Referrer-Policy: no-referrer`; a failed enqueue at the session-kill and appointment sites writes a WARNING with the id (PRB-013 call sites; PRB-013 stays open); `log-secrets-check.sh` covers the activation `POST`, an erasure and a retrieval, and the secrets of `infra/.env`. New: `/API/V1/ACTIVATION/x` now reaches the backend (404) instead of the SPA; a hand-crafted Referer or a query string on another path can still reach the proxy error log (D-19, accepted residual) | RISK-005, RISK-007 (strengthened); residuals unchanged | TS-017 TC-017.4, .6; TS-003 TC-003.7 |

**Residual scores per record.** Not changed now: the scores depend on the fixes landing.
TASK-202 re-scores them from the evidence. Each record (`in_review`) states its expected residual:

| RISK | Current (S × P → acceptability) | Expected after CR-004 | Why |
|---|---|---|---|
| RISK-001 | 2 × 2 → acceptable | 2 × 2 → acceptable | The residual assumed deny-by-default verified with no bypass; CR-004 makes that true. Not 2 × 1: one wrong rule now applies everywhere |
| RISK-004 | 3 × 2 → alarp | 3 × 2 → alarp | New characterisation control holds probability; ALARP argument unchanged |
| RISK-005 | 3 × 1 → acceptable | 3 × 1 → acceptable | Its open dependencies (PRB-003, 018, 023) close |
| RISK-006 | 2 × 2 → acceptable | 2 × 2 → acceptable | Three causes removed; PRB-058 and PRB-032 remain open, so not 2 × 1 |
| RISK-007 | 3 × 2 → alarp | 3 × 2 → alarp | Set by the single-host decision (ADR-0010) and PRB-057 |
| RISK-008 | 2 × 2 → acceptable | 2 × 2 → acceptable | Log cause removed; retention causes (PRB-012) remain |
| RISK-011 | 3 × 2 → alarp | 3 × 1 → acceptable **only if** PRB-057 is resolved or the human accepts the loss path (Q-8); otherwise 3 × 2 → alarp | Rotation and key sharing removed; key loss without backup is not |

Acceptability is the `risk_matrix` cell, not a judgement. Accepting a residual is the human's
decision, through approval of each RISK record.

**Safety-relevant SRs and their RISK coverage.** SR-005, 009 → RISK-001; SR-022 → RISK-007, 011
(and 006, 008, 010, 012); SR-023 → RISK-001, 004, 005, 006; SR-024 → RISK-008; SR-029, 030, 031 →
RISK-005; SR-041 → RISK-001, 005, 011; SR-042 → RISK-006, 007; SR-043 → RISK-008. **SR-032 and
SR-034** are covered through RISK-001's control table and TASK-188's `mitigates` links, but carry
no `mitigates` link themselves (Q-7). **SR-016** is not safety-relevant for this change (above).

## Plan

The plan is the TASK records below (overlay: no `docs/plans/<feature>.md`). Nothing starts until
the human approves the plan, ADR-0017..0019 and the RISK records' control plans.

- All tasks on `fix/review-2026-07-security`, one commit per QA-approved task with its records.
- An `approved` record that several tasks change is bumped and has its approval cleared once,
  by the first task that changes it; later tasks add to the same version (CR-002 rule). Here:
  TS-001 (TASK-140 first), TS-002 (TASK-187), TS-008 (TASK-193), TS-009 (TASK-137), TS-014
  (TASK-196). New: TS-015 (TASK-197), TS-016 (TASK-185), TS-017 (TASK-138).
- **"Ask first" steps** (CR-004 Boundaries): TASK-191 (grant change on an existing database),
  TASK-194 (field migration), TASK-195 (rotation), TASK-196 (SSE key separation). Each runs only
  on test databases and backup copies until the human approves its rehearsal result. TASK-194,
  TASK-195 and TASK-196 are each their own commit.

| Order | Task | PRB | SR (AC) | RISK (`mitigates`) | Size | Depends on | Status |
|---|---|---|---|---|---|---|---|
| 1 | [TASK-185](../design-outputs/tasks/TASK-185-originating-client-address-trusted-proxy-rule.md) Originating client address, trusted-proxy rule | 010, 029 | SR-042 AC 1–3; SR-023 | 006, 007 | M | — | new |
| 2 | [TASK-137](../design-outputs/tasks/TASK-137-capture-client-ip-in-authz-and-consent-audit.md) Client address on audit rows | 010 | SR-023 AC 6; SR-042 | 006 | S | 185 | updated |
| 3 | [TASK-186](../design-outputs/tasks/TASK-186-retrieval-rate-limit-per-client-address.md) Retrieval rate limit per client | 029 | SR-042 AC 4–5; SR-024 | 007, 008 | S | 185 | new |
| — | **Checkpoint A** | | | | | 1–3 | |
| 4 | [TASK-187](../design-outputs/tasks/TASK-187-single-decision-point-appointments-and-modules.md) Decision point: appointments, modules | 026 | SR-005 AC 1, 3; SR-011 AC 4; SR-015; SR-023 AC 7 | 001, 004, 006 | M | 137 | new |
| 5 | [TASK-188](../design-outputs/tasks/TASK-188-single-decision-point-identity-services.md) Decision point: identity services | 027 | SR-032 AC 1, 4, 5; SR-034 AC 1; SR-023 AC 7 | 001, 004, 006 | M | 187 | new |
| 6 | [TASK-189](../design-outputs/tasks/TASK-189-single-decision-point-routers-and-static-check.md) Decision point: routers, static check | 027 | SR-005 AC 1, 3; SR-008; SR-009; SR-023 AC 7 | 001, 004, 006 | M | 188 | new |
| 7 | [TASK-192](../design-outputs/tasks/TASK-192-typed-audit-fields-no-secret-in-any-field.md) Typed audit fields, logout token | 005 | SR-023 AC 5, 9 | 006, 005 | M | 137 (parallel with 4–6) | new |
| — | **Checkpoint B** | | | | | 4–7 | |
| 8 | [TASK-140](../design-outputs/tasks/TASK-140-auth-config-hygiene-dead-signing-key-lockout-required.md) Remove signing key; lockout required | 018 | SR-029 AC 1; SR-030 | 005 | S | — (any time before 9) | updated |
| 9 | [TASK-197](../design-outputs/tasks/TASK-197-refuse-missing-or-placeholder-secrets-at-start-up.md) Refuse placeholder secrets at start-up | 007 | SR-041 AC 3; SR-022 AC 3 | 001, 005, 011 | M | 140 | new |
| 10 | [TASK-203](../design-outputs/tasks/TASK-203-environment-template-compose-guards-and-secret-guide.md) Empty template, Compose guards, guide | 007 | SR-041 AC 2, 4 | 001, 005 | M | 140, 197 | new |
| 11 | [TASK-198](../design-outputs/tasks/TASK-198-non-root-frontend-image-and-uid-checks.md) Non-root frontend; UID checks | 007 | SR-041 AC 1, 6 | 001 | M | 203 | new |
| 12 | [TASK-190](../design-outputs/tasks/TASK-190-runtime-database-role-and-audit-privileges.md) Runtime DB role, audit privileges | 005 | SR-023 AC 8 | 006, 001 | M | — (code; any time) | new |
| 13 | [TASK-191](../design-outputs/tasks/TASK-191-db-migrate-service-and-runtime-role-in-deployment.md) `db-migrate` service, runtime role deployed (**ask first**) | 005, 007 | SR-023 AC 8; SR-041 AC 2 | 006, 001, 007 | M | 190, 203 | new |
| — | **Checkpoint C** (started stack) | | | | | 8–13 | |
| 14 | [TASK-193](../design-outputs/tasks/TASK-193-key-identifier-in-field-encryption-envelope.md) Key id in the envelope | 004 | SR-022 AC 3, 6 | 011, 007 | M | 197 | new |
| 15 | [TASK-194](../design-outputs/tasks/TASK-194-migrate-existing-field-values-to-identified-envelope.md) Migrate existing field values (**ask first**, own commit) | 004 | SR-022 AC 7 | 011, 007 | S | 193, 191, 190 | new |
| 16 | [TASK-195](../design-outputs/tasks/TASK-195-key-rotation-command-procedure-and-rehearsal.md) Rotation command, procedure, rehearsal (**ask first**, own commit) | 004 | SR-022 AC 8 | 011, 007 | M | 194 | new |
| 17 | [TASK-196](../design-outputs/tasks/TASK-196-separate-object-store-sse-key-and-migrate-attachments.md) Separate SSE key, migrate attachments (**ask first**, own commit) | 007 | SR-041 AC 5, 6; SR-022 | 011, 007 | M | 197, 203 | new |
| — | **Checkpoint D** (rehearsals recorded) | | | | | 14–17 | |
| P1 | [TASK-138](../design-outputs/tasks/TASK-138-pii-scrubbing-for-worker-and-notification-logs.md) Log redaction | 011 | SR-043 AC 1–3; SR-024 | 008 | M | — (parallel) | updated |
| P2 | [TASK-139](../design-outputs/tasks/TASK-139-csrf-exemption-exact-match-hardening.md) CSRF exact match | 003 | SR-031 AC 3 | 005, 001 | S | — (parallel) | updated |
| P3 | [TASK-199](../design-outputs/tasks/TASK-199-atomic-concurrent-session-cap.md) Atomic session cap | 023 | SR-030 AC 7 | 005 | S | — (parallel) | new |
| P4 | [TASK-200](../design-outputs/tasks/TASK-200-anchor-module-version-expression.md) Module version anchored | 028 | SR-016 AC 1 | none (no hazard) | XS | — (parallel) | new |
| P5 | [TASK-142](../design-outputs/tasks/TASK-142-frontend-route-level-role-guards.md) Frontend route guard | 014 | SR-005; SR-009 (defence in depth, Q-4) | 001 | M | — (parallel) | updated |
| P6 | [TASK-204](../design-outputs/tasks/TASK-204-safe-download-file-names-and-failed-download-audit.md) Any file name downloads (RFC 6266); failed download audited | 063 | SR-013 AC 3; SR-023 AC 2 | 007, 006 | M | — (parallel; commit after TASK-196) | new |
| P7 | [TASK-205](../design-outputs/tasks/TASK-205-session-refresh-dead-members-and-eviction-notice.md) Session refresh race, expired cap members, eviction report | 064, 065, 066 | SR-030 AC 1–3, 5, 7 | 005 | M | 199 (committed); parallel | new |
| P8 | [TASK-206](../design-outputs/tasks/TASK-206-token-free-logs-bounded-file-names-celery-loglevel.md) Token-free logs, activation link, bounded attachment names, Celery `--loglevel`, API task dispatch | 068, 069, 070, 071 | SR-043 AC 4, AC 2; SR-033; SR-013 AC 1, 3; SR-023 AC 2, 6 | 005, 007, 006, 009 | L | 138, 204 (committed); parallel | new |
| P9 | [TASK-207](../design-outputs/tasks/TASK-207-task-206-qa-follow-ups.md) TASK-206 QA follow-ups: fast enqueue, case-insensitive redaction, enqueue warnings | — (013 stays open) | SR-043 AC 1, 4; SR-023 | 005, 007 | S | 206 (committed) | new |
| P10 | [TASK-208](../design-outputs/tasks/TASK-208-object-store-volume-name-on-current-compose.md) Non-empty default name for the object store volume | 077 | SR-041 | 007 | S | 196 (committed) | new |
| 18 | [TASK-201](../design-outputs/tasks/TASK-201-arc42-and-design-records-for-cr-004.md) arc42, ADD and ADR index | — | SR-022, 023, 041, 042, 043 | — | M (docs) | all above | new |
| 19 | [TASK-202](../design-outputs/tasks/TASK-202-verify-cr-004-end-to-end.md) Verify end to end; re-score risks (**Checkpoint F**) | all | all in scope | (relates_to all) | S | all above | new |

**Parallel work and shared files.**

- P1..P6 share no source file with the numbered tasks (P1: `core/logging.py`, `workers/`; P2:
  `security_middleware.py`; P3: `auth/session.py`; P4: `modules/discovery.py`; P5: `frontend/`;
  P6: `api/routers/attachments.py`, `api/content_disposition.py`, `attachments/service.py`).
  Commit them between any two numbered tasks. P7 shares no source file with P1..P6 still open or with
  the open numbered tasks; it edits `auth/session.py` after TASK-199 (P3, committed) and
  `api/routers/auth.py` after TASK-192 (committed), and also `auth/login.py`, `api/errors.py` and
  `frontend/src/auth/LoginPage.tsx`.
- TASK-192 runs in parallel with 187..189 (it edits `audit/service.py`, `audit/actions.py`,
  `api/routers/auth.py`; they edit `authz/`, `appointments/`, `identity/`, other routers).
- TASK-190 (code) can run any time; TASK-191 waits for 203.
- Sequential by shared file: `backend/app/core/config.py` (185 → 140 → 197 → 193 → 196);
  `infra/docker-compose.yml` (185 → 203 → 198 → 191 → 196); `infra/.env.example` (140 → 203 →
  191 → 196); `backend/app/authz/service.py` (187 → 188 → 189); `backend/app/audit/service.py`
  (137 → 192).

**Checkpoints.**

- **A** (after 1–3): backend suite (coverage ≥ 85 %) green; a 403 through a trusted peer leaves
  an `AUTHZ_DENIED` row with the client address; two clients through one proxy have separate
  rate-limit buckets.
- **B** (after 4–7): backend, DICOM-module and frontend suites green; the static role-check test
  and the decision table green; no audit row in the suite's database contains a session token.
- **C** (after 8–13, started stack): stack starts from the empty template with generated
  secrets and refuses a placeholder; every built image and running process non-root; the
  runtime role cannot update `audit_log`; the TASK-191 rehearsal recorded.
- **D** (after 14–17): TASK-194, 195 and 196 rehearsals recorded and approved by the human;
  every clinical entry and attachment of the rehearsal copy reads back through the API.
- **F** = TASK-202.

**SR acceptance-criteria coverage** (every AC named in the CR scope):

| SR | AC → task |
|---|---|
| SR-022 | AC 3 → 193, 197; AC 6 → 193; AC 7 → 194; AC 8 → 195 |
| SR-023 | AC 5 → 192; AC 6 → 185, 137; AC 7 → 187, 188, 189; AC 8 → 190, 191; AC 9 → 192 |
| SR-041 | AC 1 → 198; AC 2 → 203, 191; AC 3 → 197; AC 4 → 203; AC 5 → 196; AC 6 → 198, 196, 202 |
| SR-042 | AC 1–3 → 185; AC 4–5 → 186 |
| SR-043 | AC 1–3 → 138 |
| SR-005 | AC 1, AC 3 → 187, 189; AC 4 (negative cases) → decision tables of 187–189; defence in depth → 142 |
| SR-009 | AC 2, AC 3 → 189 (projection unchanged), 142 |
| SR-011 AC 4, SR-015 | 187 |
| SR-016 AC 1 | 200 |
| SR-029 AC 1; SR-030 AC 5 | 140 |
| SR-030 AC 7 | 199 |
| SR-031 AC 3 | 139 |
| SR-032 AC 1, 4, 5; SR-034 AC 1 | 188 |
| SR-024 (retrieval path, logs) | 186, 138 |
| SR-013 AC 3; SR-023 AC 2 (failed download audited) | 204 |
| SR-030 AC 1–3, AC 5 (ended session stays ended), AC 7 (oldest active; notification) | 205 |
| SR-043 1.1 AC 4 (new, approved 2026-11-07) and AC 2, SR-033 (no credential or secret in logs); SR-033 AC 1, AC 3, AC 7 (activation link); SR-013 AC 1, AC 3 and SR-023 AC 2, AC 6 (bounded names; FAILURE-row address); SR-033 AC 1, AC 3, AC 7 and SR-034 AC 2 (tasks dispatched from the API, PRB-071) | 206 |
| SR-043 AC 1, AC 4 (case-insensitive activation paths; enqueue-failure warning; widened started-stack check); SR-023 (a failed session-kill enqueue leaves a warning, the only signal that no `SESSION_KILL_PROPAGATED` row follows); SR-033 AC 7 and SR-034 AC 2 (dispatch does not wait on a result store) | 207 |

**ADD coverage** (class B, every SR in scope): SR-005 (ADD-007, 018, 020), SR-009 (ADD-007, 018),
SR-016 (ADD-014), SR-022 (ADD-016, 025, 026), SR-023 (ADD-013, 007, 016, 005, 026), SR-024
(ADD-008, 017), SR-029, 030 (ADD-006), SR-031 (ADD-005), SR-032, 034 (ADD-007, 008), SR-041
(ADD-026, 025), SR-042 (ADD-005, 013, 026), SR-043 (ADD-017, 005).

**Test specifications.**

| TS | Change | Test cases | Tasks |
|---|---|---|---|
| TS-001 | 1.1 → 1.2 | TC-001.6 atomic cap; TC-001.7 lockout required, no signing key | 199, 140 |
| TS-002 | 1.1 → 1.2 | TC-002.7 decision table; TC-002.8 static check; TC-002.9 client guard | 187–189, 142 |
| TS-003 | 1.1 → 1.2 | TC-003.6 identity rules decided centrally | 188 |
| TS-008 | 1.5 → 1.6 | TC-008.9 envelope; TC-008.10 old-format migration; TC-008.11 rotation and rehearsal | 193–195 |
| TS-009 | 1.2 → 1.3 | TC-009.9 address; TC-009.10 every decision audited; TC-009.11 privileges; TC-009.12 no secret in any field | 137, 187–189, 190–191, 192 |
| TS-010 | 1.1 → 1.2 | TC-010.5 version anchored | 200 |
| TS-011 | 1.1 → 1.2 | TC-011.6 CSRF exact exemptions | 139 |
| TS-014 | 1.5 → 1.6 | TC-014.7 SSE key separation and migration (adds `verifies` SR-041) | 196 |
| TS-015 | new | TC-015.1 UIDs; TC-015.2 Compose guards; TC-015.3 start-up refusal; TC-015.4 template and guide (`verifies` SR-041) | 198, 203, 197, 191, 196 |
| TS-007 | 1.4 → 1.5 | TC-007.9 file names outside Latin-1 and header integrity; TC-007.10 failed download audited (adds `verifies` SR-023) | 204 |
| TS-001 | 1.3 → 1.4 | TC-001.8 refresh never re-creates an ended session; TC-001.9 expired members pruned, oldest active evicted; TC-001.10 eviction reported, contention 503 | 205 |
| TS-007 | 1.5 → 1.6 | TC-007.11 name bounded at upload, header bounded for any name; TC-007.6 asserts the client address; TC-007.9 bidi case | 206 |
| TS-017 | 1.1 → 1.2 | TC-017.4 SR-043 AC 4 pass criterion (no credential or secret in any log); TC-017.5 `--loglevel` honoured and redacted (adds `verifies` SR-033) | 206 |
| TS-003 | 1.3 → 1.4 | TC-003.3 activation link built in the app route's form (link-route tests) | 206 |
| TS-003 | 1.5 → 1.6 | TC-003.7 dispatch does not wait on a result store; failed session-kill enqueue logged | 207 |
| TS-007 | 1.6 → 1.7 | TC-007.11 records the multipart parser's plain 400 at about 8 KB and over | 207 |
| TS-017 | 1.2 → 1.3 | TC-017.4 case variants, widened script, real form of the 500 record; TC-017.6 enqueue failure logged (adds `verifies` SR-023) | 207 |
| TS-016 | new | TC-016.1..3 address rule; TC-016.4..5 rate limit (`verifies` SR-042) | 185, 186 |
| TS-017 | new | TC-017.1..3 log exclusion (`verifies` SR-043) | 138 |

**SOUP touched** (no version change, so no new anomaly review; relied-on requirements updated
by the task, records `in_review`): SOUP-004 Uvicorn, SOUP-005 Gunicorn (forwarded headers off,
185); SOUP-011 cryptography (AES-GCM associated data, 193); SOUP-013 redis-py, SOUP-021 Redis
(`WATCH`/`MULTI`, 199); SOUP-014 Celery (`setup_logging`, 138); SOUP-020 PostgreSQL (privileges
for a non-owner role, 190); SOUP-024 nginx (unprivileged on 8080, 198); SOUP-036 SeaweedFS (SSE key
per volume, re-key by copy, 196).

### Plan risks

| Risk | Impact | Mitigation |
|---|---|---|
| A field or attachment migration leaves data unreadable | Clinical values or images lost (RISK-011, RISK-007) | One transaction with rollback (194), read-back (195), source read only (196); rehearsals on backup copies; "ask first"; old volume kept until the human releases it |
| No backup procedure exists (PRB-057) | A failed real migration cannot be undone from a backup | Rehearsals use volume copies made by the task; no real installation is migrated in CR-004 (no release exists, A-1); PRB-057 stays open and bounds RISK-011 (Q-8) |
| An authorization rule changes while moved | Wrong allow (RISK-001) or deny (RISK-004) | Decision tables committed green before each move, unchanged after; negative controls |
| The runtime role misses a grant | 500s on some path (RISK-007) | `app.db.roles` after every migration; persistence tests as the runtime role; started-stack smoke; rehearsal on a populated copy |
| `TRUSTED_PROXIES` wrong on a host | All addresses are the proxy's, silently (RISK-006) | Started-stack check in the smoke test; fixed proxy address in Compose, not in `.env` |
| Fixed `medhub` subnet collides with a host network | Stack does not start | DEPLOY.md names the two lines to change |
| Many tasks edit `config.py` and the Compose file | Merge conflicts, lost edits | Sequential order above; one commit per task |
| Auditing every allowed decision adds rows per request | Slower lists (SR-026) | Suite timings compared in TASK-202; no new hazard |
| Test clean-ups break under the `REVOKE` | Flaky or failing suites | TASK-190 moves them to the owner connection |
| No Docker daemon on the workstation | Real-DB, real-Redis and stack checks cannot run | Use the reference workstation; CI runs the testcontainers suites |

## Version history

- 1.0 (2026-10-31) — Created at the Specify stage (GitHub sancharly/medhub#27).
- 1.1 (2026-10-31) — Risk and Plan stages (Software Architect role). Status stays `open`.
  - Open questions Q-1..Q-6 recorded as answered by the human (D-1). New Q-7 (traceability-only
    `mitigates` links on SR-032, SR-034), Q-8 (RISK-011 loss path), Q-9 (PRB candidate: secrets as
    Celery task arguments).
  - D-2: A-3 confirmed; the `REVOKE` needs role separation; design decisions ADR-0017, ADR-0018,
    ADR-0019 (`Proposed`); ADD-026 created; ADD-005, 006, 007, 013, 016, 017, 018, 025 revised
    (`in_review`).
  - Every in-scope PRB has a `## Investigation` (§9.2); none is recommended for rejection.
  - "Change analysis (Risk stage)": `affects_controls` confirmed, no new hazard, class B
    unchanged; RISK-004 added to the analysis. RISK-001, 004, 005, 006, 007, 008, 011 revised
    (`in_review`) with control rows and expected residuals; scores re-scored by TASK-202.
  - Plan: TASK-137..140, 142 updated; TASK-185..203 created (`draft`); checkpoints A–D, F; AC,
    ADD, TS and SOUP coverage; plan risks. `relates_to` links to the new tasks, ADDs and RISK-004.
- 1.2 (2026-11-01) — PRB-061 added (found in TASK-203): `resolves` link, Scope row, D-3 (human
  decision 2026-10-31, folded into TASK-191). No other change.
- 1.3 (2026-11-01) — D-4 (human decision 2026-11-01): the audit window between TASK-190 and
  TASK-191 is accepted. No other change.
- 1.4 (2026-11-01) — D-5 (human decision 2026-11-01): the window between TASK-193 and TASK-194 is
  accepted. D-6 (human decision 2026-11-01): PRB-056 folded into TASK-193; `resolves` link and
  Scope row added. No other change.
- 1.5 (2026-11-01) — D-7 (human decisions 2026-11-01, TASK-194 QA round 1): PRB-062 fixed in TASK-194
  (`resolves` link added); damaged-row procedure documented; API `strip()` accepted; 0010 rehearsal
  approved. No other change.
- 1.6 (2026-11-01) — D-8 (human decisions 2026-11-01, TASK-195 QA round 1): `--verify-key-ids` guard
  kept in `db-migrate`; QA approval may set a PRB to `resolved`, `closed` stays a release-time human step.
  No other change.
- 1.7 (2026-11-02) — D-9 (human decision 2026-11-02, TASK-196 QA round 1): PRB-063 (attachment download
  fails for file names outside Latin-1, found in the TASK-196 rehearsal) folded into CR-004: `resolves`
  link, Scope row PRB-063 to TASK-204 (the task is written by the Software Architect). No other change.
- 1.8 (2026-11-02) — TASK-204 written by the Software Architect role for PRB-063 (D-9): Scope row SR corrected
  from SR-013 (AC unassigned) to SR-013 AC 3 and SR-023 AC 2, with RISK-006 added beside RISK-007; TASK-204 added
  to the Plan as P6 (independent, before TASK-201); `relates_to` TASK-204 link; TASK-204 rows in the
  change-analysis, SR AC coverage and TS tables (TS-007 1.4 → 1.5); P6 named in the shared-files note.
  No other change.
- 1.9 (2026-11-02) — D-10: TASK-196 accepted by the human with the QA round-2 text fix and no re-review. No other change.
- 1.10 (2026-11-06) — D-11 (human decision 2026-11-06): PRB-064, PRB-065 and PRB-066 (session defects found in
  the TASK-199 review) folded into CR-004 and fixed in TASK-205: `resolves` links, `relates_to` TASK-205, Scope
  rows, Plan row P7, rows in the change-analysis, SR AC coverage and TS tables (TS-001 1.3 → 1.4), and P7 with
  its overlaps with committed tasks (TASK-199, TASK-192) in the shared-files note. No other change.
- 1.11 (2026-11-06) — D-12 (human decision 2026-11-06): PRB-067 (the /me refetch loop found in the TASK-142 review) folded into CR-004 and fixed in TASK-142: `resolves` link and Scope row. No other change.
- 1.12 (2026-11-07) — D-13 (human decision 2026-11-06): administrators get the Appointments page and its navigation entry (SR-010 AC 4, SR-011 AC 3); the route-guard change-analysis row mentions the PRB-067 fix. No other change.
- 1.13 (2026-11-07) — D-14 (human decision 2026-11-07): PRB-068 and PRB-069 folded into CR-004 and fixed in TASK-206
  with the Celery `--loglevel` follow-up: `resolves` links, `relates_to` TASK-206, Scope rows, Plan row P8, rows in the
  change-analysis, SR AC coverage and TS tables (TS-007 1.5 → 1.6, TS-017 1.1 → 1.2). D-15 (human decision
  2026-11-07): TASK-142 takes QA's one-line fix for R3-1 and one short QA check. No other change.
- 1.14 (2026-11-07) — D-16 (human decisions 2026-11-07): SR-043 gains AC 4 (SR-043 1.1, `in_review`) for credentials and
  secrets in operational and proxy logs; PRB-070 (activation link) folded into CR-004 and fixed in TASK-206; attachment
  name limit 255 UTF-8 bytes. `resolves` PRB-070, Scope row PRB-070, PRB-068 row cites SR-043 AC 4; TASK-206's
  change-analysis, SR AC coverage, TS (TS-017 TC-017.4 reworded, TS-003 1.3 → 1.4) and Plan P8 rows updated. No other change.
- 1.15 (2026-11-07) — SR-043 1.1 (AC 4) approved by the human in chat on 2026-11-07: "pending approval" changed to
  approved in the PRB-068 Scope row and the SR AC coverage row. TASK-206 built and handed to QA (`in_review`); PRB-071
  (the API process cannot enqueue Celery tasks, found while checking PRB-070 on a started stack) raised and left `open`,
  outside CR-004's scope until the human decides. No other change.
- 1.16 (2026-11-07) — D-17 (human decision 2026-11-07): PRB-071 is `critical` and fixed in TASK-206. `resolves` PRB-071, Scope
  row PRB-071, Plan P8 and the TASK-206 change-analysis and coverage rows updated. PRB-071 stays `open` until QA approves
  TASK-206 (D-8). No other change.
- 1.17 (2026-11-07) — D-18 (human decisions 2026-11-07): TASK-207 takes QA's two MEDIUM fixes and the LOW record fixes
  from TASK-206; PRB-072, PRB-073 and PRB-074 are known anomalies outside CR-004 (no `resolves` link); PRB-013 stays open.
  `relates_to` TASK-207 and Plan row P9. No other change.
- 1.18 (2026-11-07) — D-19 (human decision 2026-11-07): the Referer and query-string case that can reach the proxy error log is an accepted residual against SR-043 AC 4. TASK-207 built: change-analysis, SR AC coverage and TS rows (TS-003 1.5 → 1.6, TS-007 1.6 → 1.7, TS-017 1.2 → 1.3). No other change.
- 1.19 (2026-11-08) — Checkpoint F (TASK-202): the whole-CR verification is recorded in TASK-202's hand-off (backend 1547 passed, 6 skipped, coverage 94.51%; DICOM 25; frontend 315; infra 110; started stack smoke 78 and log check 38, 0 failed; activation e-mail flow and field-key rotation with attachments on a started stack). Residuals proposed for RISK-001, 004, 005, 006, 007, 008, 009, 011, all unchanged, in `in_review` for the human. The CR stays `open` for the human's close-out decision.
- 1.20 (2026-11-08) — D-20 (orchestrator): PRB-076 (start-up failure from TASK-185's fixed subnet, found in the TASK-202 QA review) fixed in TASK-202 round 2: `resolves` PRB-076, Scope row, `medhub` subnet moved to `10.77.77.0/24` outside Docker's default pools. No other change.
- 1.21 (2026-11-10) — D-21: residuals, PRB-074 and three design residuals accepted by the human; RISK, ADD and SOUP records approved. No other change.
- 1.22 (2026-11-10) — D-22: PRB-077 (empty object store volume name, found by the first hosted CI run) fixed in TASK-208: `resolves` PRB-077, `relates_to` TASK-208, Scope row and Plan row P10. No other change.
