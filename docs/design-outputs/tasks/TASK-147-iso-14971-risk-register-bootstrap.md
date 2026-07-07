---
id: "TASK-147"
type: task
title: "ISO 14971 risk register bootstrap"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "NFR-005"
    relation: implements
  - target: "NFR-006"
    relation: implements
  - target: "NFR-004"
    relation: relates_to
  - target: "NFR-007"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:high", "regulatory"]
---

- **Phase:** Review 2026-07 — regulatory blockers
- **Implements:** NFR-005 (MDR/FDA), NFR-006 (IEC 62304 process)
- **Depends on:** —
- **Branch:** `doc/risk-register`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — finding W (High, regulatory)

## Objective

`docs/risks/` contains only `.gitkeep` — the design record has **no controlled risk-management
file**. Risk content exists only as an arc42 narrative
(`docs/design/11-risks-and-technical-debt.md`): prose, no per-hazard IDs, no severity×probability
classification, no mitigations traced to requirements or verification. IEC 62304 requires software
safety classification driven by risk analysis; ISO 14971 requires a maintained risk-management
file. This blocks any release claim.

## Implementation detail

- Create per-risk records in `docs/risks/` following the MedTrace frontmatter schema
  (`RISK-XXX-slug.md`: id, type: risk, status, links) — one file per hazard, consistent with the
  design-record structure used for SRs/TASKs.
- Each record: hazardous situation, cause, severity, probability, risk level (matrix), mitigations
  (each linked `mitigated_by` → SR/TASK), residual risk, verification link.
- Seed the register from: arc42 §11 items, security review outputs (AUDIT-FINDINGS.md), and this
  review's High/Medium findings (memory-DoS, audit-IP gap, PII-in-logs, erasure gap TASK-116).
- Add a software safety classification statement (62304 class, justification) — likely in
  `docs/software-development-plan.md` or a dedicated record — and link it from the register.
- Extend the traceability matrix with a risk column (coordinates with TASK-114).

## Acceptance criteria

- [ ] ≥ the known hazard set is recorded as individual RISK-XXX files with severity/probability and
  linked mitigations resolving to existing SR/TASK IDs.
- [ ] Software safety classification documented and justified.
- [ ] Traceability matrix references risk IDs; no dangling links (validated).

## Definition of Done

- [ ] Records pass the design-record-structure conventions (frontmatter lint)
- [ ] TASK-114 scope note updated to include the risk column
- [ ] Reviewed/approved status transition recorded per document control convention
