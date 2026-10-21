---
id: SOUP-021
type: soup
title: Redis server
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: Redis Ltd.
soup_version: 7-alpine
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 27044965ba94229801eaa832099a11597ed6d7f566c50a4adc230bf294fc8752
approval_note: self-approved
links: []
tags:
  - soup
  - layer:infrastructure
  - class:B
---

# SOUP-021 — Redis server 7-alpine

> Floating image tag (PRB-001).

## Functional and performance requirements

Session store with TTL eviction (SR-030) and Celery broker/result backend.

## Required hardware and software environment

`redis:7-alpine` container image.

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
