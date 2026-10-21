---
id: SR-028
type: software-requirement
title: Traceable, version-controlled development records
status: approved
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-07-07"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 5915a99ba057b662f759cb8e9fc24845d407baef59063b376724af253a99096d
approval_note: self-approved
links:
  - target: RR-006
    relation: satisfies
  - target: RR-007
    relation: satisfies
  - target: RR-008
    relation: satisfies
  - target: RR-010
    relation: satisfies
  - target: RISK-007
    relation: mitigates
  - target: RISK-010
    relation: mitigates
  - target: NFR-005
    relation: derives_from
  - target: NFR-006
    relation: derives_from
tags:
  - control:design
  - control:protective
---

## Summary

The development shall maintain uniquely identified, version-controlled requirements with bidirectional traceability and risk analysis, and shall trace each software requirement to at least one test.

## Description

This requirement implements the process/documentation obligations of the medical-device regulation and IEC 62304. Each requirement (user need, NFR, software requirement) is uniquely identified, kept under version control with status and version history, and carries risk analysis. Software requirements reference their origin user need/NFR, and each is traced to at least one system test, forming an auditable design and verification record.

## Acceptance Criteria

1. Every requirement has a unique identifier, a status, and a version history, and is stored under version control.
2. Every software requirement records its origin user need or NFR (bidirectional traceability is maintained).
3. Every requirement includes a documented risk analysis (rationale, potential risks, control measures).
4. Each software requirement is traced to at least one system test before release.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-005 "Medical device regulatory compliance (MDR and FDA)" and NFR-006 "IEC 62304 development process compliance".

## Risk Analysis

### Rationale

Traceable, controlled records are mandatory for MDR/FDA technical documentation and IEC 62304 lifecycle conformity.

### Potential Risks

- Compliance risk: missing traceability or records blocks regulatory acceptance.
- Quality risk: untraced requirements may go unverified.

### Control Measures

- Maintain requirements in the repository using the template (IDs, status, version history, origin, risk analysis); establish requirement-to-test traceability during the testing phase per the development plan.

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-007, RISK-010 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.2 (2026-09-17) — Added `satisfies` link to RR-006, RR-007, RR-008, RR-010 (regulatory requirements
  extracted from the NFRs with clause citations). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.3 (2026-10-21) — Tagged `control:design`, `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.4 (2026-10-21) — Restored from `obsolete` by the owner's decision: the restatement as RR-011
  was withdrawn because SR-028 is the only SR realizing RR-006/007/008 and is implemented by
  TASK-001/005/111/147/154. Its architecture coverage is now ADD-024. Content unchanged.
