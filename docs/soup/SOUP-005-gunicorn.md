---
id: SOUP-005
type: soup
title: Gunicorn
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: Benoit Chesneau
soup_version: 26.0.0
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: bb1245c7d1a8a043a160c68ffd108735494187588652c8273bb3fc85b45db4bf
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-005 — Gunicorn 26.0.0

## Functional and performance requirements

Production process manager supervising Uvicorn workers.

## Required hardware and software environment

Python 3.12; Linux (POSIX process model).

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
