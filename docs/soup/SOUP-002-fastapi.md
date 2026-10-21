---
id: "SOUP-002"
type: soup
title: "FastAPI"
status: in_review
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: "Sebastián Ramírez (tiangolo)"
soup_version: "0.138.0"
links: []
tags: ["soup", "layer:backend", "class:B"]
---

# SOUP-002 — FastAPI 0.138.0

## Functional and performance requirements

HTTP routing, dependency injection used as the authorization enforcement point on every protected route (SR-005), request validation through Pydantic, and OpenAPI 3.1 generation.

## Required hardware and software environment

Python 3.12; Starlette (SOUP-003); Pydantic (SOUP-006).

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
