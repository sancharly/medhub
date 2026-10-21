---
id: SOUP-012
type: soup
title: argon2-cffi
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: Hynek Schlawack
soup_version: 25.1.0
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 2c2d57a764d6d94c9436090ac0b68f30cd0e46cd0f09c69d7e1427772997c73e
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-012 — argon2-cffi 25.1.0

## Functional and performance requirements

Argon2id password hashing and verification with constant-time comparison (SR-002, SR-025, SR-029).

## Required hardware and software environment

Python 3.12; argon2-cffi-bindings 25.1.0 (bundled libargon2).

Transitive dependencies covered by this record: argon2-cffi-bindings 25.1.0.

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
