---
id: SOUP-019
type: soup
title: boto3
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: Amazon Web Services
soup_version: undeclared
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 7c62c112f2a6e1a975bbf34404949688630589060b37f7a879d231ca7b8c78fe
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-019 — boto3 undeclared

> Imported at runtime but declared in no manifest, so no version is identified or installed (PRB-002).

## Functional and performance requirements

S3 API client used by `ObjectStorageClient` to store and fetch attachment objects with server-side encryption (SR-013, SR-022).

## Required hardware and software environment

Python 3.12; botocore; a MinIO or S3 endpoint (SOUP-022).

Transitive dependencies covered by this record: botocore.

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
