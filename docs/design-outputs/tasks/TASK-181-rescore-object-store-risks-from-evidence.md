---
id: "TASK-181"
type: task
title: "Re-score RISK-012 and re-evaluate the related risks from the verification evidence"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-040"
    relation: implements
  - target: "SR-013"
    relation: implements
  - target: "SR-022"
    relation: implements
  - target: "RISK-012"
    relation: relates_to
  - target: "RISK-010"
    relation: relates_to
  - target: "RISK-001"
    relation: relates_to
  - target: "RISK-007"
    relation: relates_to
  - target: "RISK-011"
    relation: relates_to
  - target: "CR-002"
    relation: relates_to
  - target: "PRB-043"
    relation: relates_to
  - target: "PRB-007"
    relation: relates_to
tags: ["risk", "cr:CR-002", "issue:sancharly/medhub#33"]
---

# TASK-181 — Re-score RISK-012 and re-evaluate the related risks from the verification evidence

- **Software item / unit:** risk records only. No code.
- **Depends on:** TASK-172..179, all merged on the branch (`relates_to` through CR-002)
- **Branch:** `bug/minio-object-store`
- **Size:** S (RISK-012, RISK-010, RISK-007, RISK-011, RISK-001, PRB-043, PRB-007)

## Objective

CR-002 AC-13, AC-14 and AC-19 (PRB-043 and PRB-007), §7.3 and §7.4.3. With the controls
implemented and verified, the risk records are re-scored or confirmed from the evidence, never
from the plan. This task implements no control, so it links the RISKs with `relates_to`.
Acceptance is the human's decision: every record is left `in_review`.

## Implementation detail

- **RISK-012** (1.1 since the Risk stage; keep the version and extend its history entry):
  - fill each control row's "Verified by" with the TC IDs and the evidence that passed
    (TASK-172..179);
  - re-score `probability_residual` from that evidence. Severity stays 4;
  - derive `acceptability` from `risk_matrix`;
  - rewrite the ALARP section (remove it, with a statement, if the result is acceptable);
  - update "Risks introduced by controls";
  - move the `relates_to` links from SOUP-022 and SOUP-023 to SOUP-036 (AC-12).
- **RISK-010** (approved 1.4: bump to 1.5 and clear the approval record). Re-evaluate path 2 per
  AC-14:
  - **3 × 1 only if** a maintained, patchable store is deployed: SOUP-036 at the pinned digest,
    with a review that found a fix path (TASK-172) and the PLAN-002 monthly check in place.
    Otherwise state why path 2 stays at 2;
  - the residual is the worst path;
  - replace `relates_to` SOUP-022 and SOUP-023 with SOUP-036;
  - add to "risks introduced by controls" that the replacement ships on a rolling release line.
- **RISK-007** (bump and clear the approval record):
  - `cause` and body: "MinIO failure" becomes "object-store failure";
  - link SOUP-022 → SOUP-036;
  - add the control rows "bucket initialisation ordered and fail-fast (SR-040 AC 4, TASK-175,
    TS-014 TC-014.4)" and "checksum refusal fails with a clear error (SR-013 AC 5, TASK-173,
    TS-007)";
  - no re-score.
- **RISK-011** (bump and clear the approval record):
  - link SOUP-022 → SOUP-036;
  - the row "Server-side encryption enforced on the object store, verified at bring-up" gains
    SR-022 AC 4 and AC 5, TASK-175 and TASK-179, and TS-008 TC-008.6 and TC-008.8;
  - add a row for the rehearsed migration (TASK-178);
  - body "MinIO (SOUP-022)" becomes generic;
  - note the carried-over key reuse (Q-3, PRB-007);
  - no re-score.
- **RISK-001** (bump and clear the approval record): add the control row "Object store reachable
  only by the backend, no console, non-default credentials (SR-040, TASK-174, TASK-176, TASK-177,
  TS-014)". No re-score.
- **RISK-002 and RISK-003**: no edit and no re-score (CR-002 out of scope; the human decided on
  2026-10-22). Confirm in CR-002 that their bodies name no replaced item.
- **PRB-043** → `resolved`, with a `## Resolution` covering each of its five configuration
  findings and the four CVEs, and the task that removed each. **PRB-007** stays `open` and gets a
  note that its object-store credentials are resolved by CR-002 (TASK-174).
- CR-002 "Escalations": complete it from TASK-172's review.

## Acceptance criteria

- [x] CR-002 **AC-13**: every RISK-012 row names an implementing TASK that `mitigates` RISK-012
      and a verification. The residual is re-scored from that evidence, `acceptability` follows
      `risk_matrix`, the ALARP and "introduced" sections are updated, and the record is
      `in_review`.
- [x] CR-002 **AC-14**: RISK-010 path 2 is re-evaluated against the outcome. RISK-001, 002, 003,
      007 and 011 are named with a result each. Nothing is re-scored without evidence.
- [x] CR-002 **AC-19** (PRB-043, PRB-007 parts).

## Verification

`traceability-check` over the project. Check that no non-`obsolete` record other than the
retiring tasks links SOUP-022 or SOUP-023:
`grep -rln 'target: "\?SOUP-02[23]' docs | xargs grep -L '^status: obsolete'`. The only output
may be CR-002, TASK-175, TASK-176 and SOUP-022/023 themselves.

## Definition of Done

- [x] The changed RISK records are `in_review`, with version bumps and cleared approval records
      where they were `approved`.
- [x] `traceability-check` shows no error for these records.

## Verification results (Software Architect role, 2026-10-30)

Records only, no code. Evidence read: TASK-172..180 ("Evidence" / "Verification results" and every
QA review round), TS-007 (TC-007.6..8), TS-008 (TC-008.6..8), TS-013 (TC-013.9, TC-013.10), TS-014
(TC-014.1..6), SOUP-036 (F-1..F-5, review 2026-10-30, monitoring), PLAN-002 1.2, PRB-007, PRB-036,
PRB-042, PRB-043, PRB-051, PRB-052, PRB-055..057, ADR-0015, CR-002. Scales and matrix:
`docs/medtrace.yml` (5 × 5 `risk_matrix`).

### Records changed

| Record | Before | After | Status |
|---|---|---|---|
| RISK-012 | 1.1, 4 × 2 → `alarp`; links SOUP-022, SOUP-023 | 1.1 (history entry extended), **4 × 1 → `acceptable`** (row 4, col 1); every row has TASK, commit and TS/TC evidence; interim row removed (option b); rows added for the monthly advisory check and information for safety; ALARP replaced by "not needed"; risks introduced rewritten; links SOUP-036 | `in_review`, no approval record |
| RISK-010 | 1.4 `approved`, 3 × 2 → `alarp`; links SOUP-022, SOUP-023 | 1.5, **3 × 1 → `acceptable`** (row 3, col 1), conditional on PLAN-002 1.2; path 2 rewritten; monthly-check row; rolling-release bullet; links SOUP-036 | `in_review`, approval record cleared |
| RISK-007 | 1.3 `approved`, 3 × 2 `alarp`; links SOUP-022 | 1.4, not re-scored; "object-store failure"; rows for the fail-fast initialiser (TC-014.4) and the checksum refusal (TC-007.6..8); backup row notes PRB-057; risks introduced listed; links SOUP-036 | `in_review`, approval record cleared |
| RISK-011 | 1.2 `approved`, 3 × 2 `alarp`; links SOUP-022 | 1.3, not re-scored; SSE row + SR-022 AC 4/AC 5, TASK-175, TASK-179, TC-008.6, TC-008.8; migration row (TASK-178, TC-008.7); MinIO wording generic; key reuse (Q-3, Q-7, PRB-007), F-4 and PRB-057 noted; links SOUP-036 | `in_review`, approval record cleared |
| RISK-001 | 1.1 `approved`, 2 × 2 `acceptable` | 1.2, not re-scored; row "object store reachable only by the backend, no console, non-default credentials" (SR-040; TASK-174, 176, 177; TS-014); version history added | `in_review`, approval record cleared |
| RISK-002, RISK-003 | — | not edited, not re-scored (CR-002 Out of scope, D-2). `grep -n -i "minio\|SOUP-02[23]"` on both bodies: no match, so they name no replaced item | unchanged |
| PRB-043 | `open` 1.1 | `resolved` 1.2: `## Resolution` maps each CVE and each of the five configuration findings to its control, commit and reproducible evidence; Safety evaluation completed (after-resolution state, `critical` kept, release gate) | — |
| PRB-007 | `open` 1.0 | `open` 1.1: note that the object-store credentials are resolved by CR-002 (TASK-174, `8c46bcc`); key separation of `AT_REST_ENCRYPTION_KEY` tracked here (Q-7, D-6) | — |

### Checks

- `python3 infra/check_image_pins.py` → exit 0. `python3 -m unittest discover -s infra/tests` → 32
  tests OK (re-run of the static evidence the re-score cites).
- `grep -rln 'target: "\?SOUP-02[23]' docs | xargs grep -L '^status: obsolete'` → CR-002, TASK-175,
  TASK-176 only (the retiring records, CR-002 AC-12).
- Cited test names and paths exist (`test_object_store_is_pinned_internal_and_has_no_console_or_admin_option`,
  `test_object_store_network_is_internal_and_joined_only_by_backend_and_initialiser`,
  `tests/core/test_object_store_credentials.py`, `tests/core/test_object_store_init.py`,
  `tests/test_env_example.py`); `git grep -n -i minioadmin -- ':!docs'` matches only
  `app/core/object_store_credentials.py` and the two test modules that name the default set; the
  known-default set in `KNOWN_DEFAULTS` matches PRB-007's note.
- `traceability-check` (fallback parser, no MedTrace tooling in the repository; E1–E9, W1–W7,
  class-B gated rules, `acceptability` against `risk_matrix`; `modified_after_approval` not
  computable), whole project, 377 records, working tree including the uncommitted PRB-052
  amendment: **0 errors**. Gated findings: `soup_without_risk` on SOUP-036 cleared (RISK-007,
  010, 011 and 012 link it); **2 `risk_control_unverified` warnings** (QA's parser; mine did not
  implement that rule): TASK-174 and TASK-177 implement only SR-040, which has no TR yet. They
  become errors in release scope, and the release TR clears them. Warnings: W5 76, W6 5, W2 5, W1 3, W7 1.
  - W5: approved records (mainly SRs and TASKs that `mitigates` them) linking the RISKs now held at
    `in_review` (RISK-010 17, RISK-001 14, RISK-012 14, RISK-007 13, RISK-011 6), RISK-006 4 (PRB-052
    amendment), SOUP-036 2, ADD-025 2, ADD-012 1, ADD-024 1, PLAN-002 1, and the pre-existing
    TASK-132 → TASK-101. They clear when the human approves the records.
  - W6: TASK-175 → SOUP-023, TASK-176 and CR-002 → SOUP-022, CR-002 → SOUP-023 (retiring records,
    AC-12); TASK-165 → SOUP-033 (pre-existing, CR-003 D-6).
  - W1/W2/W7: pre-existing SR-017, SR-018, SR-019, SR-026, TASK-073; SR-040 W2 (no TR until
    release).
  - Every `acceptability` equals the value `risk_matrix` derives from the residual scores.

### For the human to accept (risk acceptability is a human decision)

1. **RISK-012 1.1 at 4 × 1 → `acceptable`**, replacing the development-only acceptance of 4 × 2
   (D-6). Includes the residual conditions: monthly SeaweedFS check, and TASK-182's hosted CI and
   fresh-host runs (a failure reopens the score).
2. **RISK-010 1.5 at 3 × 1 → `acceptable`**, valid only together with **PLAN-002 1.2** (monthly
   rule for rolling-release items); without it path 2 stays 3 × 2 → `alarp`.
3. **RISK-007 1.4, RISK-011 1.3, RISK-001 1.2**: content changes, scores unchanged (3 × 2 `alarp`,
   3 × 2 `alarp`, 2 × 2 `acceptable`). RISK-007 and RISK-011 keep their ALARP justifications; note
   PRB-057 (no backup and restore of the store with its key) against both.
4. SOUP-036 1.2 and PLAN-002 1.2 are still `in_review`: the RISK-010 and RISK-012 residuals rest on
   them.

### Left for others

- CR-002 text (not edited here; the working copy carries the PRB-052 amendment awaiting
  approval): "Escalations" completion, "Results per record (AC-14)" with these results, the
  RISK-002/003 confirmation, and "For the human to accept". Proposed text is in the TASK-181
  handoff to the orchestrator.
- TASK-182 checks AC-12 (no W6 beyond the retiring records) and the hosted runs.


## QA review (2026-10-30)

**Verdict: APPROVED.** No CRITICAL or HIGH finding. The RISK records stay `in_review` for the
human. M-1 and M-2 are text corrections to uncommitted records; apply them before the commit.

### Checks

- **Evidence chains (RISK-012).** TASK-172..180 are all `approved` and link `mitigates` RISK-012.
  Commits `9d3b395`, `8c46bcc`, `684ee7b`, `0e01b2a`, `d4cdba0`, `aa2fd61`, `db0b480` and `d2b557a`
  exist, are ancestors of HEAD and carry their task. Every cited TC exists in its TS (TS-007 1.3,
  TS-008 1.5, TS-013 1.5, TS-014 1.4, all `approved`). The recorded passes were found in the task
  records: 9 PASS (TASK-172), the dind run (TASK-176), 27 passed and M1..M3 plus the 18333 probe
  (TASK-177 QA), 4 passed locally (TASK-179), 4 failed under mutation (TASK-173), and the rehearsal
  counts (TASK-178). Still pending, and labelled as pending in the record: the hosted run of
  TC-008.8 and the hosted amd64 fresh run (TASK-182). The monthly-check row also rests on
  PLAN-002 1.2, which is `in_review`.
- **Scores.** 4×1 and 3×1 give `acceptable`, 3×2 gives `alarp` and 2×2 gives `acceptable`, all as
  `docs/medtrace.yml` `risk_matrix` derives them. No severity was lowered.
- **PRB-043.** `resolved`. HEAD CR-002 has `resolves` → PRB-043. Re-run:
  `python3 infra/check_image_pins.py` exits 0. `python3 -m unittest discover -s infra/tests` gives
  32 OK. The console grep on `infra/docker-compose.yml` has no output. `git grep -i minioadmin`
  matches only the rule module and the 2 test modules. The cited backend tests give 70 passed, and
  `modules/dicom_viewer/tests` gives 19 passed.
- **SOUP-036.** Linked from ADD-025 and from RISK-007, 010, 011 and 012. No non-obsolete record
  links SOUP-022/023 apart from CR-002, TASK-175 and TASK-176. RISK-002 and RISK-003 name no MinIO
  item.
- **Approval fields.** Cleared on RISK-001, 007, 010 and 011, each with a version bump. RISK-012
  had no approval record.
- **Traceability.** QA ran its own parser over 377 records: **0 errors**, W5 76, W6 5. On the
  touched records alone: 0 errors, 0 gated findings.

### Findings

- **M-1 [MEDIUM] RISK-011 and RISK-007 ALARP justifications contradict PRB-057.**
  - RISK-011 "ALARP justification" still names "backups before any rotation" as the procedural
    mitigation, yet the same record now says no backup and restore procedure exists (PRB-057).
  - RISK-007 "ALARP justification" argues that unavailability only "delays access", which ignores
    permanent loss with no backup.
  - Fix: in both sections, state that the backup part is not in place (PRB-057), why the `alarp`
    residual still holds until then, and that the record is re-evaluated when PRB-057 is resolved,
    or at the first release, whichever comes first. No re-score.
- **M-2 [MEDIUM] PRB-043 "Safety evaluation" claims that `resolved` lifts the release block.**
  - The `iec62304-sdlc` gate and MedTrace E10 (`release_with_open_critical`) count a `critical`
    PRB as open until it is `closed` or `rejected`. PRB-043 is the only critical PRB.
  - CR-002 AC-19 and PLAN-001 ("no critical PRB open") read it the other way.
  - Fix: reword to "resolved under CR-002 AC-19; under the overlay gate and E10 it still counts
    until `closed`." Add to CR-002 "For the human to accept" that the human must decide how the
    release treats it, for example closing it in the release-record commit after the TR confirms
    it.
- **M-3 [MEDIUM] RISK-012's reopen condition is not wired into TASK-182.**
  - RISK-012 says that a failed hosted TC-008.8 run or a failed fresh-host run reopens the
    re-score. TASK-182 step 5 does not check it.
  - Fix: when TASK-182 is next edited, add to step 5: "RISK-012 1.1 / RISK-010 1.5 residual
    conditions hold (hosted `object-store-integration` green, amd64 fresh run passed); otherwise
    return both to re-score."
- **L-1 [LOW] RISK-001 1.2's new row cites TASK-176, which has no `mitigates` → RISK-001.**
  - Fix the row, not the link. Keep SR-040, TASK-174 and TASK-177 as implementers. Name TASK-176
    as "no console, loopback ports, traced to RISK-001 through SR-040 AC 1; the task mitigates
    RISK-012". Do not reopen the approved TASK-176.
- **L-2 [LOW] The traceability result omits 2 gated warnings.**
  - `risk_control_unverified` fires for TASK-174 and TASK-177: they implement only SR-040, which
    has no TR yet. These are warnings now and become errors in release scope.
  - Fix: correct "gated findings 0" above. The release TR clears them.
- **L-3 [LOW] RISK-012's control-table preamble overstates the evidence.**
  - "Every row is implemented and verified" does not hold for row 7 (hosted run pending) or
    row 9 (PLAN-002 1.2 `in_review`). The TASK-172 rows cite no commit (`68fc68b`).
  - Fix: qualify the sentence and add `68fc68b`.
- **L-4 [LOW] RISK-012's frontmatter `hazard` and `cause` still describe MinIO in the present
  tense** ("will never receive a security fix").
  - Fix: mark them as the hazard as raised (MinIO, 1.0), or make them generic, as RISK-010's
    `cause` now is.

**Post-approval note (2026-10-30):** M-1, M-2 and L-1..L-4 were applied as text fixes to the uncommitted records after this approval (RISK-007, RISK-011, PRB-043, RISK-001, RISK-012, this TASK); no score or status changed. M-3 is for TASK-182.

### Rulings on the architect's open questions

- **(a) PRB-057.** No re-score of RISK-007 or RISK-011 is needed before CR-002 closes. The gap
  pre-dates CR-002, CR-002 does not worsen it, and the residuals are set by ADR-0010 and PRB-004.
  The ALARP texts must be made accurate (M-1).
  - Release-gate condition, not a CR-002 close condition: before the first release, PRB-057 is
    either resolved, or listed in the REL "Known residual anomalies", with RISK-007 and RISK-011
    re-accepted against it.
- **(b) RISK-001 / TASK-176.** Fix the row (L-1).
- **(c) Proposed CR-002 text.** This review did not see the text. To be accurate it must:
  - give F-1..F-5 each with its disposition: F-1 and F-5 by TASK-176 (TC-014.5), F-2 by TASK-177
    (TC-014.6, plus local-peer RPCs), F-3 by `-master.telemetry=false` (TC-014.1), and F-4 to
    RISK-011, RISK-007, PRB-007 and PRB-057;
  - say that no new RISK was raised;
  - list the PRBs raised during CR-002 with their status: PRB-051, 053, 054, 056 and 057 `open`,
    PRB-055 `resolved`, PRB-052 in scope;
  - give each AC-14 record its result, with RISK-010 3×1 conditional on PLAN-002 1.2 and RISK-012
    4×1 conditional on TASK-182;
  - not repeat the M-2 gate claim.
