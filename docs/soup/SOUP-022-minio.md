---
id: SOUP-022
type: soup
title: MinIO object storage
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
manufacturer: MinIO, Inc.
soup_version: latest
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: aa75a0600f500e82e9d7283fc54f40ef3db2870628c796ba6158275f0570eb24
approval_note: self-approved
links: []
tags:
  - soup
  - layer:infrastructure
  - class:B
---

# SOUP-022 — MinIO object storage latest

> Floating `latest` tag (PRB-001).

## Functional and performance requirements

S3-compatible object storage for attachments with server-side encryption (SR-013, SR-022).

## Required hardware and software environment

`minio/minio:latest` container image with a persistent volume.

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
