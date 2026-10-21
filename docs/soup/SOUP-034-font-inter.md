---
id: SOUP-034
type: soup
title: Fontsource Inter (@fontsource-variable/inter)
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: Fontsource
soup_version: 5.2.8
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 0b6a7293e796f6f26b1e93439a0f1119157e8773100430d88738bbc10bdb3d5e
approval_note: self-approved
links: []
tags:
  - soup
  - layer:frontend
  - class:B
---

# SOUP-034 — Fontsource Inter (@fontsource-variable/inter) 5.2.8

## Functional and performance requirements

Self-hosted body typeface, so no third-party font CDN receives user traffic.

## Required hardware and software environment

Browser with variable-font support.

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
