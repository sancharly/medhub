---
id: "SOUP-026"
type: soup
title: "React DOM"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: "Meta Platforms"
soup_version: "18.3.1"
links: []
tags: ["soup", "layer:frontend", "class:B"]
---

# SOUP-026 — React DOM 18.3.1

## Functional and performance requirements

DOM rendering with escaping by default (XSS mitigation, SR-031).

## Required hardware and software environment

Modern evergreen browsers; React (SOUP-025).

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
