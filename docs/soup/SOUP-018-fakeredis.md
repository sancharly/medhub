---
id: SOUP-018
type: soup
title: fakeredis
status: obsolete
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: fakeredis contributors
soup_version: 2.36.2
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-018 — fakeredis 2.36.2

> No longer shipped: moved to the `dev` dependency group (PRB-033, CR-001). Development tooling that is not shipped is not SOUP.

## Functional and performance requirements

None: no software item uses it. It was declared as a runtime dependency in `backend/pyproject.toml` but is imported only by tests. It is now in the `dev` dependency group and is not part of the production image.

## Required hardware and software environment

Python 3.12.

## Anomaly list review

Not required: the record is obsolete, so no anomaly-list review is made for it (TASK-154 skips it).

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — removed from the runtime dependency set (dev group only); record obsolete; PRB-033, CR-001
