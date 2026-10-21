---
id: SOUP-014
type: soup
title: Celery
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: Celery project
soup_version: 5.6.3
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: fe6c58f385f6c69a3575ff4288c8c489662693f3f3d221a5a6a77f12a9fda47e
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-014 — Celery 5.6.3

## Functional and performance requirements

Asynchronous tasks with retry and backoff: activation and appointment notifications (SR-033, SR-035), session-revocation propagation (SR-034) and retention erasure (SR-024).

## Required hardware and software environment

Python 3.12; Redis server 7 as broker and result backend.

Transitive dependencies covered by this record: kombu 5.6.2, billiard 4.2.4, amqp 5.3.1.

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
