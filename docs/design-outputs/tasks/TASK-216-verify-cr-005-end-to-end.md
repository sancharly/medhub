---
id: "TASK-216"
type: task
title: "Verify CR-005 end to end"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-12"
updated: "2026-11-12"
links:
  - target: "SR-028"
    relation: implements
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-005"
    relation: relates_to
  - target: "RISK-006"
    relation: relates_to
  - target: "RISK-007"
    relation: relates_to
  - target: "RISK-011"
    relation: relates_to
  - target: "TS-013"
    relation: relates_to
  - target: "TASK-209"
    relation: relates_to
  - target: "TASK-210"
    relation: relates_to
  - target: "TASK-211"
    relation: relates_to
  - target: "TASK-212"
    relation: relates_to
  - target: "TASK-213"
    relation: relates_to
  - target: "TASK-214"
    relation: relates_to
  - target: "TASK-215"
    relation: relates_to
tags: ["verification", "traceability", "cr:CR-005"]
---

# TASK-216 — Verify CR-005 end to end

- **Software items:** all touched by CR-005 (SI-DEVINFRA, SI-DEPLOY, backend tests).
- **CR:** CR-005 (AC-11, AC-12, AC-13; the negative-control criterion as a whole).
- **Depends on:** TASK-209..215, all QA-approved and committed.
- **Branch:** `bug/build-hygiene`.
- **Size:** S (records only: RISK-010, TS-013 environment, CR-005, this task; PLAN-002 if Q-5 is
  answered yes; `docs/design/05-building-blocks.md` only if it describes the CI check's scope).

## Objective

Evidence that the whole change holds on the branch head and on hosted runners, that the records
are complete and traceable, and that the §7.4.3 verification of the affected controls is recorded.

## Steps

1. **Regression (AC-12)** on the branch head:
   - `cd backend && uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=85`;
     `uv run pytest modules/dicom_viewer/tests`;
   - `cd frontend && npm run lint && npm run typecheck && npm test -- --run`;
   - `python3 -m unittest discover -s infra/tests -v`; `python3 infra/check_image_pins.py`;
   - OpenAPI export byte-identical (`uv run python -m app.export_openapi --output openapi/openapi.json && git diff --exit-code`).
2. **Hosted CI (AC-12, needs the human's go-ahead to push):** every job green on the pushed head;
   from the logs record: `Python 3.12.15` in every Python job, `v24.22.2` in every Node job,
   `uv-0.13.7`, the pinned linter version, and each action downloaded at its pinned SHA.
3. **Negative controls (CR-005):** re-run the mutations of TASK-211, TASK-213 and TASK-214 on a
   scratch copy of the head; each check fails as recorded there.
4. **Records (AC-11):** ADD-024 1.3, ADD-026 1.5, SOUP-005 1.3, TS-013 1.6 in review and consistent
   with the code; each PRB has its `## Resolution`; TS-013 environment names the commit tested.
   RISK-010 1.6: replace "planned" in the CR-005 control rows by the evidence; confirm the
   residual 3 × 1 → acceptable. RISK-006, RISK-007 and RISK-011: no change unless the evidence
   contradicts the change analysis (CR-005 "Change analysis").
5. **PLAN-002 (only if Q-5 = yes):** in "SOUP monitoring", one paragraph: the build and CI tool
   pins of SR-028 AC-8 are reviewed with the SOUP list (before every release, at most 365 days
   apart), and a pin is moved only by a reviewed commit. 1.2 → 1.3, `in_review`.
6. **Traceability (AC-13):** `medical-records:traceability-check` over `docs/`: 0 errors for
   CR-005's records (CR-005, SR-028, TASK-209..216, TS-013, ADD-024, ADD-026, SOUP-005, RISK-010,
   PRB-034, PRB-038, PRB-040, PRB-041).

## Acceptance criteria

- [ ] CR-005 AC-11: every record above updated and in review; four PRB resolutions written.
- [ ] CR-005 AC-12: all local suites green (coverage ≥ 85 %); every hosted job green with the
      pinned versions visible in the logs.
- [ ] CR-005 AC-13: `traceability-check` 0 errors for CR-005's records; negative controls re-run.

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
