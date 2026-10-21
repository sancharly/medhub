---
id: RR-006
type: regulatory-requirement
title: IEC 62304 lifecycle records and traceability
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 30ddda066593b3d7054381ff48e10c0a681716067ed0a4326af7638ba6b88493
approval_note: self-approved
links: []
tags:
  - iec62304
  - regulatory
---

# RR-006 — IEC 62304 lifecycle records and traceability

## Summary

Development of medical device software must follow a defined lifecycle whose activities produce controlled, traceable records.

## Source

IEC 62304:2006+A1:2015 §4.3 (safety classification), §5.1 (development plan), §5.2 (requirements), §5.3-5.4 (architecture and units), §5.5-5.7 (verification), §5.8 (release), §6 (maintenance), §8 (configuration management), §9 (problem resolution); NFR-006.

## Obligation

The project shall maintain a software development plan, a classified safety class, requirement, architecture, task, verification, risk, SOUP and problem-resolution records under version control, each traceable to the records it derives from and to the evidence that verifies it.

## Acceptance criteria

- A software development plan record exists and states the safety class with its rationale.
- Every software requirement traces upward to a user need, NFR or regulatory requirement and downward to a verification record.
- Every defect is recorded as a problem report and resolved through a change request.
- The traceability check reports zero errors before a release.

## Realized by

RR-011 (formerly SR-028). Records: PLAN-001..005, SOUP-001..035, the record set under `docs/`. Skill: `medical-records:traceability-check`.
