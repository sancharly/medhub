---
id: "CR-004"
type: change-request
title: "Close the open security defects from the 2026-07 review and audit"
status: open
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-01"
branch: fix/review-2026-07-security
risk_impact: affects_controls
links:
  - target: "PRB-003"
    relation: resolves
  - target: "PRB-004"
    relation: resolves
  - target: "PRB-005"
    relation: resolves
  - target: "PRB-007"
    relation: resolves
  - target: "PRB-010"
    relation: resolves
  - target: "PRB-011"
    relation: resolves
  - target: "PRB-014"
    relation: resolves
  - target: "PRB-018"
    relation: resolves
  - target: "PRB-023"
    relation: resolves
  - target: "PRB-026"
    relation: resolves
  - target: "PRB-027"
    relation: resolves
  - target: "PRB-028"
    relation: resolves
  - target: "PRB-029"
    relation: resolves
  - target: "PRB-061"
    relation: resolves
  - target: "SR-005"
    relation: relates_to
  - target: "SR-009"
    relation: relates_to
  - target: "SR-016"
    relation: relates_to
  - target: "SR-022"
    relation: relates_to
  - target: "SR-023"
    relation: relates_to
  - target: "SR-024"
    relation: relates_to
  - target: "SR-029"
    relation: relates_to
  - target: "SR-030"
    relation: relates_to
  - target: "SR-031"
    relation: relates_to
  - target: "SR-032"
    relation: relates_to
  - target: "SR-034"
    relation: relates_to
  - target: "SR-041"
    relation: relates_to
  - target: "SR-042"
    relation: relates_to
  - target: "SR-043"
    relation: relates_to
  - target: "RR-001"
    relation: relates_to
  - target: "RR-002"
    relation: relates_to
  - target: "RR-003"
    relation: relates_to
  - target: "RR-004"
    relation: relates_to
  - target: "NFR-004"
    relation: relates_to
  - target: "NFR-007"
    relation: relates_to
  - target: "RISK-001"
    relation: relates_to
  - target: "RISK-005"
    relation: relates_to
  - target: "RISK-006"
    relation: relates_to
  - target: "RISK-007"
    relation: relates_to
  - target: "RISK-008"
    relation: relates_to
  - target: "RISK-011"
    relation: relates_to
  - target: "TASK-137"
    relation: relates_to
  - target: "TASK-138"
    relation: relates_to
  - target: "TASK-139"
    relation: relates_to
  - target: "TASK-140"
    relation: relates_to
  - target: "TASK-142"
    relation: relates_to
  - target: "CR-002"
    relation: relates_to
  - target: "RISK-004"
    relation: relates_to
  - target: "TASK-185"
    relation: relates_to
  - target: "TASK-186"
    relation: relates_to
  - target: "TASK-187"
    relation: relates_to
  - target: "TASK-188"
    relation: relates_to
  - target: "TASK-189"
    relation: relates_to
  - target: "TASK-190"
    relation: relates_to
  - target: "TASK-191"
    relation: relates_to
  - target: "TASK-192"
    relation: relates_to
  - target: "TASK-193"
    relation: relates_to
  - target: "TASK-194"
    relation: relates_to
  - target: "TASK-195"
    relation: relates_to
  - target: "TASK-196"
    relation: relates_to
  - target: "TASK-197"
    relation: relates_to
  - target: "TASK-198"
    relation: relates_to
  - target: "TASK-199"
    relation: relates_to
  - target: "TASK-200"
    relation: relates_to
  - target: "TASK-201"
    relation: relates_to
  - target: "TASK-202"
    relation: relates_to
  - target: "TASK-203"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
  - target: "ADD-006"
    relation: relates_to
  - target: "ADD-007"
    relation: relates_to
  - target: "ADD-013"
    relation: relates_to
  - target: "ADD-016"
    relation: relates_to
  - target: "ADD-017"
    relation: relates_to
  - target: "ADD-018"
    relation: relates_to
  - target: "ADD-025"
    relation: relates_to
  - target: "ADD-026"
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
| PRB-061 The celery-worker container runs gunicorn, not Celery (found in TASK-203; added in 1.2) | major | SR-023, SR-024, SR-030, SR-041 AC 3 (worker start-up refusal, effective in the started stack) | TASK-191 |

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
| CSRF exact match; session cap; route guard (139, 199, 142) | SI-API, SI-AUTH, SI-FE-SHELL | Remove latent bypasses; guard is defence in depth | RISK-005, RISK-001 | TS-011 TC-011.6, TS-001 TC-001.6, TS-002 TC-002.9 |
| Module version (200) | SI-MODHOST | None (no hazard) | none | TS-010 TC-010.5 |

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
| 18 | [TASK-201](../design-outputs/tasks/TASK-201-arc42-and-design-records-for-cr-004.md) arc42, ADD and ADR index | — | SR-022, 023, 041, 042, 043 | — | M (docs) | all above | new |
| 19 | [TASK-202](../design-outputs/tasks/TASK-202-verify-cr-004-end-to-end.md) Verify end to end; re-score risks (**Checkpoint F**) | all | all in scope | (relates_to all) | S | all above | new |

**Parallel work and shared files.**

- P1..P5 share no source file with the numbered tasks (P1: `core/logging.py`, `workers/`; P2:
  `security_middleware.py`; P3: `auth/session.py`; P4: `modules/discovery.py`; P5: `frontend/`).
  Commit them between any two numbered tasks.
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
