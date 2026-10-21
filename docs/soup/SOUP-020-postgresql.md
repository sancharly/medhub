---
id: SOUP-020
type: soup
title: PostgreSQL server
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: PostgreSQL Global Development Group
soup_version: "16"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 0fb5bbfd3286bb65b48ee8e84b32e9662da866a55a8f453a6d3c80e26d0df930
approval_note: self-approved
links: []
tags:
  - soup
  - layer:infrastructure
  - class:B
---

# SOUP-020 — PostgreSQL server 16

> Floating image tag: the minor version is not pinned (PRB-001).

## Functional and performance requirements

Relational storage of all PHI and records, constraints, and transactional integrity.

## Required hardware and software environment

`postgres:16` container image with a persistent volume (`infra/docker-compose.yml`).

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
