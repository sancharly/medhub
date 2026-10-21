---
id: "PLAN-002"
type: lifecycle-plan
title: "Software maintenance plan"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-21"
updated: "2026-10-21"
plan_kind: maintenance
links: []
tags: ["regulatory", "class:B"]
---

# PLAN-002 — Software maintenance plan

IEC 62304:2006+A1:2015 §6. Split out of ADD-002 (v2.0, section "Maintenance (§6)") when the
plans became `lifecycle-plan` records.

## Scope

Released MedHub software, its configuration and its SOUP.

## Process

Released software is maintained through the same process as development
([PLAN-001](PLAN-001-software-development-plan.md)): feedback and problems enter as problem reports
([PLAN-004](PLAN-004-problem-resolution-plan.md)), are evaluated for safety impact
([PLAN-005](PLAN-005-risk-management-plan.md), §7.4), and are implemented as change requests through
the development stages. A modification is released only through the release gate of PLAN-001.

## Feedback sources (§6.1 a–b)

- Problem reports raised by users, administrators and the team.
- Audit and code-review findings.
- SOUP anomaly lists and security advisories.

## SOUP monitoring (§6.1 f)

SOUP anomaly lists and security advisories are reviewed for each `soup` record in
[`../soup/`](../soup/) at every dependency change, before every release, and at most 365 days
apart (`soup_anomaly_max_age_days` in `docs/medtrace.yml`). The review date goes in the record's
`anomaly_review`. Owner: the Software Architect role, with the human accountable.

## Maintenance of this plan

This plan is a living document; a change is a new `version` and a new review.
