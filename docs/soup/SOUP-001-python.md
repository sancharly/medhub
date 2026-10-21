---
id: SOUP-001
type: soup
title: Python runtime
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: Python Software Foundation
soup_version: 3.12-slim
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 31c960446c4db9c4ca1767245888d03c819ba004f97d8f57a780bb82f8fa4c83
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-001 — Python runtime 3.12-slim

> Floating image tag: the exact patch version and base OS are not pinned (PRB-001).

## Functional and performance requirements

Language runtime and standard library for every backend item, including `secrets` and `hashlib` for tokens and digests.

## Required hardware and software environment

Debian-based `python:3.12-slim` container image (backend `Dockerfile`, builder and runtime stages). Tests ran on CPython 3.12.3.

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
