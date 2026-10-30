---
id: "TASK-181"
type: task
title: "Re-score RISK-012 and re-evaluate the related risks from the verification evidence"
status: draft
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
    SR-022 AC 4 and AC 5, TASK-175 and TASK-179, and TS-008 TC-008.6 and TC-008.7;
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

- [ ] CR-002 **AC-13**: every RISK-012 row names an implementing TASK that `mitigates` RISK-012
      and a verification. The residual is re-scored from that evidence, `acceptability` follows
      `risk_matrix`, the ALARP and "introduced" sections are updated, and the record is
      `in_review`.
- [ ] CR-002 **AC-14**: RISK-010 path 2 is re-evaluated against the outcome. RISK-001, 002, 003,
      007 and 011 are named with a result each. Nothing is re-scored without evidence.
- [ ] CR-002 **AC-19** (PRB-043, PRB-007 parts).

## Verification

`traceability-check` over the project. Check that no non-`obsolete` record other than the
retiring tasks links SOUP-022 or SOUP-023:
`grep -rln 'target: "\?SOUP-02[23]' docs | xargs grep -L '^status: obsolete'`. The only output
may be CR-002, TASK-175, TASK-176 and SOUP-022/023 themselves.

## Definition of Done

- [ ] The changed RISK records are `in_review`, with version bumps and cleared approval records
      where they were `approved`.
- [ ] `traceability-check` shows no error for these records.
