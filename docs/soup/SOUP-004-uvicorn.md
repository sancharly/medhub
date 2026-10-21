---
id: SOUP-004
type: soup
title: Uvicorn
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: Encode
soup_version: 0.49.0
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: eded8ad6cd179c700f0127311f6f2d9b25543c7abe89496808ac5e9ccb4469a2
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-004 — Uvicorn 0.49.0

## Functional and performance requirements

ASGI server process for the API (development and the worker class under Gunicorn).

## Required hardware and software environment

Python 3.12; Linux container.

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
