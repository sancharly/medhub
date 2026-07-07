---
id: "SR-028"
type: software-requirement
title: "Traceable, version-controlled development records"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "NFR-005"
    relation: derives_from
  - target: "NFR-006"
    relation: derives_from
tags: []
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
