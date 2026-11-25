---
id: "TASK-239"
type: task
title: "Verify CR-008 end to end, re-score the risks and record the PRB resolutions"
status: draft
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-25"
updated: "2026-11-25"
links:
  - target: "SR-017"
    relation: implements
  - target: "RISK-003"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-008"
    relation: relates_to
  - target: "PRB-048"
    relation: relates_to
  - target: "PRB-046"
    relation: relates_to
  - target: "PRB-075"
    relation: relates_to
  - target: "PRB-094"
    relation: relates_to
  - target: "SR-013"
    relation: implements
  - target: "TS-007"
    relation: relates_to
  - target: "TS-019"
    relation: relates_to
  - target: "TS-010"
    relation: relates_to
  - target: "TS-013"
    relation: relates_to
tags: ["cr:CR-008", "verification"]
---

# TASK-239 — Verify CR-008 end to end, re-score the risks and record the PRB resolutions

- **Role:** Software Developer (runs the verification), with the Software Architect role for the re-score.
- **CR:** CR-008 (Verification approach; IEC 62304 §8.2.3, §9.7).
- **Depends on:** TASK-233 to TASK-238 and TASK-240 all `approved` by QA. Last task.
- **Size:** M (records only; no code unless a defect is found, which becomes a PRB, never a silent fix).

## Objective

Execute CR-008's verification approach on the branch head, replace every "planned" in the RISK and TS
records with the executed result, re-score RISK-003 and RISK-007 from the evidence, and record the
resolutions of PRB-048, PRB-046 and PRB-094.

## Steps

1. **Suites** on the branch head (record the commit): backend with coverage, module suite, Ruff, Black,
   mypy; frontend test, lint, typecheck, build on Node 20+ (CI: 24.22.2); infra tests and pin check;
   Docker Build with the TASK-236 step.
2. **Clean checkout:** in a fresh clone of the branch, `cd backend && uv sync --frozen` and the
   entry-point command of CR-008 (prints `['dicom-viewer']`).
3. **Negative controls** (CR-008): step 2's command and the TASK-236 step on an image built at 396e9de
   (fail); module guard tests with the package uninstalled (fail); allow-list removed (TC-019.6 fails); the upload inflation check removed (TC-007.18 fails).
   Restore after each.
4. **Started stack** (`docker compose -f infra/docker-compose.yml up -d --build`, throwaway secrets as in
   DEPLOY.md), `bash infra/smoke-test.sh` (0 failed, includes TC-010.9's 401). Then as a system
   administrator enable `dicom-viewer` for a group, as a doctor of that group with access to a patient:
   upload a real uncompressed multi-frame DICOM (generated with the TASK-234 fixtures helper and written to
   a file), `GET /studies/{id}` (200 `application/dicom`, SHA-256 equal to the upload), `?frame=0` and the
   last frame (200 `application/octet-stream`, bytes equal to the known values, time recorded),
   `?frame=<frames>` (400), a JPEG Baseline object `?frame=0` (400 `dicom_transfer_syntax_unsupported`);
   a user without the module enabled gets 403. Upload path (PRB-094, TC-007.18 at system level): upload
   a small valid Deflated DICOM (accepted, downloaded byte-identical) and a deflate bomb under 1 MiB stored
   that inflates above 1 GiB (400 `dicom_decoded_size_exceeded`; the backend container's memory, from
   `docker stats --no-stream`, stays within a few hundred MiB of its idle value and no worker restarts in
   `docker compose logs backend`; no attachment row). This is **TC-019.5, backend frame part**; the "first
   rendered image within 10 s" part stays deferred to #29 (SR-026 AC 3; CR-006 D-35, CR-007 D-2).
5. **Records:**
   - TS-019, TS-010, TS-013, TS-007: verification results dated, TC-019.5 backend part executed.
   - RISK-003 (1.6 → 1.7) and RISK-007 (1.21 → 1.22), Software Architect role: each CR-008 row's
     "planned" replaced by the executed test and date; re-score from the evidence (expected unchanged: 4 × 2
     and 3 × 2, alarp); stay `in_review` for the human's acceptance.
   - PRB-048, PRB-046 and PRB-094: a `## Resolution` section each (PRB-094 replaces its "Not fixed yet" text) (what changed, by which TASKs, the evidence with
     commit and date, the negative controls), status `open` → `resolved` (the CR-008 `resolves` links
     exist). Not `closed`: the human closes in MedTrace after the merge.
   - PRB-075: a dated note — with `dicom-viewer` installed the registry sync runs at every start; the
     failure stays unreachable with one module (RISK-007 1.21). Status unchanged.
   - SOUP-037 and SOUP-015: confirm `soup_version` equals `backend/uv.lock`; anomaly review stays
     2026-11-25 unless a new release appeared, in which case review it.
   - CR-008: verification summary; status stays `in_progress` (never `closed` by an agent).
6. `traceability-check` on every CR-008 record (CR, SR-017, RISK-003, RISK-007, SOUP-015, SOUP-037,
   ADD-012, ADD-014, ADD-015, ADD-021, ADD-022, TASK-233 to TASK-240, TS-005, TS-007, TS-010, TS-013, TS-019,
   PRB-046, PRB-048, PRB-094):
   0 errors.

## Verification

The steps are the verification. Pass: every suite green; each negative control fails as expected and
passes when restored; the started-stack results as listed; `traceability-check` 0 errors.

## Acceptance criteria

- [ ] CR-008's verification approach executed on the branch head, every result dated with the commit
  (SR-017 AC 6 to AC 11, SR-013 AC 6; TC-019.5 backend part, TC-010.9, TC-013.15, TC-007.18).
- [ ] RISK-003 and RISK-007 re-scored from the evidence and left `in_review`; PRB-048, PRB-046 and
  PRB-094 `resolved` with their Resolution sections.

## Definition of Done

- [ ] Records updated; `traceability-check` 0 errors; any defect found raised as a PRB

## Carried from TASK-236 (QA, 2026-11-25)

TASK-236 was approved with these open findings (details in TASK-236 "QA review — round 1"):

- R1-1 [MEDIUM] `backend/scripts/check_image_modules.py` compares entry-point names only; an entry point with the
  right name and a wrong value passes. Add a `discover_modules()` (or `ep.load().module_key`) assertion, or record
  the human's decision to rely on TC-010.8 and smoke 9b.
- R1-2 [LOW] TASK-236 and TS-013 TC-013.15 say the `HEAD` 396e9de negative run is "to be verified on hosted CI";
  hosted CI never builds 396e9de. Cite QA's run on the pre-TASK-233 image `infra-backend:latest` (exit 1) instead.
- R1-3 [LOW] TS-010: add "system (TC-010.9)" to Levels and the started-stack precondition (`curl`, `python3`).
- R1-4 [LOW] `infra/smoke-test.sh:175`: an empty `STUDY_ID` (no `python3`) requests `/studies/` and reports "module
  route not mounted". Check it is non-empty or use a fixed UUID.
- Hosted CI: record the Docker Build job's result for the new step on the pushed commit (TC-013.15).

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role). `draft`.
- 1.1 (2026-11-25) — CR-008 D-B: depends on TASK-240; also verifies and resolves PRB-094 (TC-007.18, started-stack upload of a deflate bomb); `implements` SR-013 added. `draft`.
