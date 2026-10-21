---
id: SOUP-011
type: soup
title: cryptography
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: Python Cryptographic Authority (PyCA)
soup_version: 49.0.0
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 62078ac17a49e0c127ee3901ca7774133011398840d01766f1ff5571aadf2e41
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-011 — cryptography 49.0.0

## Functional and performance requirements

AES-256-GCM authenticated field encryption at rest (SR-022) and key handling.

## Required hardware and software environment

Python 3.12; bundled OpenSSL; cffi 2.0.0.

Transitive dependencies covered by this record: cffi 2.0.0, bundled OpenSSL.

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
