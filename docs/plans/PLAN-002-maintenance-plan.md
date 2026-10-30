---
id: PLAN-002
type: lifecycle-plan
title: Software maintenance plan
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-30"
plan_kind: maintenance
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-30"
approved_digest: 139edd8a08b544124db2bb30f76483c5fdbd8736e043057be93a4a92bb88aa60
approval_note: self-approved
links: []
tags:
  - regulatory
  - class:B
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

### End of support (obsolescence)

At every review above, and before every release, check that each item is inside upstream
support:

- **What is checked:** the version line of each `soup` record (for example Redis 7.4, Python
  3.12) and, for a container image, also its base OS release (for example Alpine 3.21, Debian 12).
  The same check covers the images that build shipped artifacts without being SOUP themselves,
  such as the Node stage of `frontend/Dockerfile`.
- **Against what:** the manufacturer's published support or end-of-life policy, the date on which
  that line stops receiving security fixes. Record the date and the source checked with the
  review: in the SOUP record's anomaly-list review section, and for a build image in the
  evidence of the activity that ran the review. When the manufacturer publishes no end date,
  record that, and treat a line that has stopped receiving fixes as out of support.
- **Horizon: 12 months.** Each item must have at least 12 months of support remaining on the
  review date. The horizon is no shorter than the 365-day maximum review interval, so an item
  cannot reach its end of support between two reviews unnoticed.

On a shortfall (less than 12 months left, or support already ended):

1. Raise a problem report ([PLAN-004](PLAN-004-problem-resolution-plan.md)) naming the item, its
   support end date and the source, with `criticality` set from actual impact.
2. Plan the upgrade as a change request that completes before the support end date. An item
   whose support has already ended is upgraded before the next release; if it cannot be, the
   human records in the PRB why the release may ship with it, and the release evaluates it as a
   residual anomaly (§5.8.3).

## Maintenance of this plan

This plan is a living document; a change is a new `version` and a new review.

## Version history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-10-21 | Split out of ADD-002 v2.0 as a `lifecycle-plan` record |
| 1.1 | 2026-10-30 | End-of-support criterion added to SOUP monitoring (§6.1 f), with a 12-month horizon and the action on a shortfall. Root cause of [PRB-045](../problem-reports/PRB-045-redis-image-base-os-end-of-support.md) (Redis image on Alpine 3.21, support ending 2026-11-01) and [PRB-035](../problem-reports/PRB-035-frontend-build-on-end-of-life-node.md) (frontend built on Node 20, end of life 2026-04-30): the reviews checked anomaly lists only, and nothing checked end of support. Raised as a separate plan revision by CR-003 Q-5 |
