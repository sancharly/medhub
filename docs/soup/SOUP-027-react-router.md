---
id: SOUP-027
type: soup
title: React Router (react-router-dom)
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: Remix Software / Shopify
soup_version: 7.18.0
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 303e25347ea70313e783a99753d0abdbb010fa7c44c942f3d2501f9edf198fb1
approval_note: self-approved
links: []
tags:
  - soup
  - layer:frontend
  - class:B
---

# SOUP-027 — React Router (react-router-dom) 7.18.0

## Functional and performance requirements

Client-side routing, authentication redirect and route composition.

## Required hardware and software environment

React 18 (SOUP-025).

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
