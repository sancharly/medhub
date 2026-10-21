---
id: RR-011
type: regulatory-requirement
title: Traceable, version-controlled development records
status: obsolete
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
links: []
tags:
  - iec62304
  - regulatory
  - supersedes:SR-028
---

> **Obsolete — withdrawn (2026-10-21).** Never approved. SR-028 was restored instead: it is the
> only software requirement realizing RR-006/007/008 and is implemented by TASK-001/005/111/147/154,
> and its architecture coverage is ADD-024. Kept because design-record IDs are never reused.

# RR-011 — Traceable, version-controlled development records

Restated from SR-028 (approved, now `obsolete`) on 2026-10-21 by the owner's decision: this is a
process obligation that the lifecycle plans and the record set satisfy, not a requirement that a
software item implements. The summary, description and acceptance criteria are SR-028's, unchanged.

## Summary

The development shall maintain uniquely identified, version-controlled requirements with bidirectional traceability and risk analysis, and shall trace each software requirement to at least one test.

## Source

IEC 62304:2006+A1:2015 §5.1.1, §5.2.6, §5.7.4 and §8 (configuration management); MDR Annex II
(technical documentation); 21 CFR 820.30(j) (design history file). Derived from NFR-005 and NFR-006.

## Obligation

This requirement implements the process/documentation obligations of the medical-device regulation and IEC 62304. Each requirement (user need, NFR, software requirement) is uniquely identified, kept under version control with status and version history, and carries risk analysis. Software requirements reference their origin user need/NFR, and each is traced to at least one system test, forming an auditable design and verification record.

## Acceptance criteria

1. Every requirement has a unique identifier, a status, and a version history, and is stored under version control.
2. Every software requirement records its origin user need or NFR (bidirectional traceability is maintained).
3. Every requirement includes a documented risk analysis (rationale, potential risks, control measures).
4. Each software requirement is traced to at least one system test before release.

## Realized by

The lifecycle plans [PLAN-001..005](../../../plans/), which define the records, IDs, statuses,
links and gates; the design record set under `docs/`; and the `traceability-check` gap reports in
`docs/reports/`, which are the evidence for criteria 1–4. Criterion 4 is enforced by the release
gate of PLAN-001 (every SR verified by a test report).
