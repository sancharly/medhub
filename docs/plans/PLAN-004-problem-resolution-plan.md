---
id: PLAN-004
type: lifecycle-plan
title: Software problem resolution plan
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
plan_kind: problem-resolution
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: a723c1eb74b6e94b59ca794ee85b99ffd92e7bcb6f529f2efe60f5f0f42238b8
approval_note: self-approved
links: []
tags:
  - regulatory
  - class:B
---

# PLAN-004 — Software problem resolution plan

IEC 62304:2006+A1:2015 §9. Split out of ADD-002 (v2.0) when the plans became `lifecycle-plan`
records.

## Process

Defects — reported by users, found in review, or found during verification — are recorded as PRB
records with an honest `criticality` and resolved through a CR that links `resolves` → PRB, using
`problem-report-resolution`. Problems found during formal verification are never fixed on the fly
without a PRB. Trends across problem reports are reviewed at each release (§9.8).

## Records and statuses

- A problem report is a `problem-report` record in [`../problem-reports/`](../problem-reports/)
  with `criticality` (`minor` / `major` / `critical`) set from actual impact. Statuses:
  `open → investigating → resolved → closed`, or `rejected`.
- Its fix is a `change-request` record in [`../change-requests/`](../change-requests/), which
  carries the `resolves` link to the PRB. Statuses: `open → in_progress → closed`, or `rejected`.
- A PRB is `resolved`/`closed` only with an incoming `resolves` link from a CR (§9.7).
- The work is done with the `medical-records:problem-report-resolution` skill.

## Safety evaluation (§9.2–9.4)

Every problem report records whether it is safety-relevant and which RISK record it contributes
to; a safety-relevant problem goes through the change analysis of
[PLAN-005](PLAN-005-risk-management-plan.md) before its CR is implemented.

## Release interaction

A `critical` PRB open at release time blocks the release gate of
[PLAN-001](PLAN-001-software-development-plan.md); any other open PRB is listed and evaluated as a
known residual anomaly in the release record.
