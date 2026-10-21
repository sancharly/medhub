---
id: SOUP-009
type: soup
title: Alembic
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: SQLAlchemy authors
soup_version: 1.18.4
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: b325166a18aa69ce2d6085c46e7ccfcddc49dd7b8fe818e37a71dbdc85260fad
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-009 — Alembic 1.18.4

## Functional and performance requirements

Schema migrations applied at bring-up, giving a reproducible database state.

## Required hardware and software environment

Python 3.12; SQLAlchemy (SOUP-008); PostgreSQL 16.

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
