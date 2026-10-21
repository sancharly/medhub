---
id: SOUP-007
type: soup
title: pydantic-settings
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: Pydantic Services
soup_version: 2.14.2
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: f4c2795acccad2f2f3ca31b9647d08e316d6e04dc5f13c667e64b0a64b5747fe
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-007 — pydantic-settings 2.14.2

## Functional and performance requirements

Typed 12-factor configuration and secret handling (`SecretStr`) for every backend item (NFR-007).

## Required hardware and software environment

Python 3.12; Pydantic (SOUP-006); environment variables injected at deploy time.

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
