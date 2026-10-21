---
id: SOUP-025
type: soup
title: React
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: Meta Platforms
soup_version: 18.3.1
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 503a9052110b7bbdb611aa35e73a4277b99cd128151e6bab0c3ebed361a7c5e1
approval_note: self-approved
links: []
tags:
  - soup
  - layer:frontend
  - class:B
---

# SOUP-025 — React 18.3.1

## Functional and performance requirements

Component model and rendering for every frontend item.

## Required hardware and software environment

Modern evergreen browsers (SR-019).

## Anomaly list review

**Not yet performed.** No published anomaly list, release notes or advisory database has been
reviewed for this exact version, so `anomaly_review` is absent. The first review is TASK-154; until
it lands this item fails the release gate's SOUP check.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
