---
id: SOUP-015
type: soup
title: pydicom
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: pydicom contributors
soup_version: 3.0.2
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 1e2b34fe813ebd9777b1b4ef291bceea0a9a37b5ff983772256f295eff76d648
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-015 — pydicom 3.0.2

> Safety-relevant: rendering correctness feeds RISK-003.

## Functional and performance requirements

DICOM parsing, metadata extraction and validation on upload, and pixel/frame access for the DICOM endpoint (SR-013, SR-017).

## Required hardware and software environment

Python 3.12; NumPy for pixel data where present.

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
