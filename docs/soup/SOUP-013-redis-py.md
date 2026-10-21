---
id: "SOUP-013"
type: soup
title: "redis-py"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: "Redis Ltd."
soup_version: "8.0.0"
links: []
tags: ["soup", "layer:backend", "class:B"]
---

# SOUP-013 — redis-py 8.0.0

## Functional and performance requirements

Client for the opaque session store with TTLs (SR-030) and for the Celery broker connection.

## Required hardware and software environment

Python 3.12; Redis server 7 (SOUP-021).

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
