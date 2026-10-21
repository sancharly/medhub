---
id: SOUP-018
type: soup
title: fakeredis
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: fakeredis contributors
soup_version: 2.36.2
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: a3be98d09164927e8d33e4828f84d23ca6a10b11c2761ea75a30af771d3a3d45
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-018 — fakeredis 2.36.2

> Misdeclared dependency, tracked as PRB-033; this record exists because the package is shipped.

## Functional and performance requirements

None: no software item uses it. It is declared as a runtime dependency in `backend/pyproject.toml` but imported only by tests, so it ships in the production image without being relied on.

## Required hardware and software environment

Python 3.12.

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
