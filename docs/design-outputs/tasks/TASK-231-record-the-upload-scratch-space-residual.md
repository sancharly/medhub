---
id: "TASK-231"
type: task
title: "Record the upload scratch-space residual in RISK-007 and the deployment guide"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-16"
updated: "2026-11-16"
links:
  - target: "SR-013"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-007"
    relation: relates_to
  - target: "PRB-092"
    relation: relates_to
  - target: "ADD-012"
    relation: relates_to
  - target: "ADD-026"
    relation: relates_to
tags: ["cr:CR-007", "control:information", "deployment"]
---

# TASK-231 — Record the upload scratch-space residual in RISK-007 and the deployment guide

- **Software items:** SI-ATTACH upload (ADD-012; Starlette spooling, ADR-0021) and SI-DEPLOY
  `infra/DEPLOY.md` (ADD-026, `U-DEP-EnvTemplate`).
- **PRB:** PRB-092. **CR:** CR-007 (D-1: no code control, residual accepted by the human in MedTrace).
- **Depends on:** none. Parallel with TASK-229 and TASK-230.
- **Branch:** `fix/cr-007-review-followups`.
- **Size:** XS (`infra/DEPLOY.md`, `docs/risks/RISK-007-clinical-information-unavailable.md`,
  `docs/design/11-risks-and-technical-debt.md`, PRB-092). No code, Compose or test change.

## Objective

SR-013 AC 1 (upload up to 150 MiB) can fail with a 5xx when the API container's temporary directory is
full. The human chose no code control (D-1). The residual is recorded in RISK-007 with one
information-for-safety measure, the DEPLOY.md note, which tells the operator how much space to provide
and what a shortage looks like.

## Steps

1. **`infra/DEPLOY.md`** ("Attachment size", lines 234-235), as worded at CR-007 P-4: the directory
   (the API container's temporary directory, `/tmp` unless `TMPDIR` is set); the sizing rule (about
   150 MiB free per concurrent maximum-size upload the site expects); the failure behaviour (the upload
   answers a 5xx, nothing is stored in the object store or the database, the user can retry); other
   requests that need the directory may fail while it is full.
2. **RISK-007** (approved 1.19 → 1.20; `in_review`; remove `approved_by`, `approved_on`,
   `approved_digest`, `approval_note`). If CR-006 has changed it again, bump from the version found.
   - `cause`: add "upload scratch space full under concurrent large uploads (PRB-092)".
   - Sequence of events: the scratch-space step.
   - Risk control measures: new row "Deployment guide states the upload scratch space and its sizing;
     a shortage fails the upload loudly (5xx) with no partial record (CR-007 D-1, PRB-092)", Type
     Information, Implemented by SR-013 AC 1; TASK-231, Verified by "review of `infra/DEPLOY.md`
     (TASK-231 QA); no automated test: information for safety".
   - Residual risk: a paragraph for CR-007: the cause is accepted as residual with no code control;
     3 × 2 → `alarp`, unchanged (several concurrent maximum-size uploads on a small temporary
     directory; ADR-0010 and PRB-057 still set the residual); the TC-018.3 load test uses 1 MiB uploads
     and does not exercise it; acceptance is the human's, in MedTrace.
   - Version-history line.
3. **`docs/design/11-risks-and-technical-debt.md`:** the "Upload scratch space" row states the residual
   accepted in RISK-007 (CR-007 D-1) and the DEPLOY.md measure.
4. **PRB-092** (1.0 → 1.1): Resolution "Not fixed by design decision (CR-007 D-1): residual accepted in
   RISK-007 with the DEPLOY.md measure"; status as the human decides at CR-007 P-3 (recommended:
   stays `open` as a known residual anomaly, listed in each release record).

## Verification

- Review: the DEPLOY.md note names the directory, the sizing rule and the failure behaviour, and
  matches the code (`ATTACHMENT_MAX_BYTES=157286400`; Starlette spools above 1 MiB, ADR-0021).
- RISK-007: scores unchanged and `acceptability` equal to what `risk_matrix` derives for 3 × 2; the new
  row's "Implemented by" names SR-013 and TASK-231, which links `mitigates` RISK-007.
- `traceability-check` on RISK-007, PRB-092, TASK-231, CR-007: 0 errors.

## Acceptance criteria

- [ ] SR-013 AC 1 residual: the deployment guide states where uploads spool, how much space to provide
  and what happens when it runs out.
- [ ] RISK-007 lists the cause, the information measure and the residual, `in_review` for the human's
  acceptance, scores unchanged.

## Definition of Done

- [ ] DEPLOY.md, RISK-007, section 11 and PRB-092 consistent; `traceability-check` no error for these records

## Version history

- 1.0 (2026-11-16) — Created at the CR-007 Plan stage (Software Architect role), D-1 (PRB-092 residual accepted, no code control). `draft`.
