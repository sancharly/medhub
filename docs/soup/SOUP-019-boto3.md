---
id: SOUP-019
type: soup
title: boto3
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Amazon Web Services
soup_version: 1.43.117
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-22"
approved_digest: 3cd7e459f725f657bd715cdb6dd761f9cf10c0e81ee517fcadf06c06abb85019
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-019 — boto3 1.43.117

## Functional and performance requirements

S3 API client used by `ObjectStorageClient` to store and fetch attachment objects with server-side encryption (SR-013, SR-022).

## Required hardware and software environment

Python 3.12; botocore; a MinIO or S3 endpoint (SOUP-022).

Declared as a required runtime dependency: `"boto3>=1.43.0"` under `[project] dependencies` in
`backend/pyproject.toml`, resolved by `backend/uv.lock` to boto3 1.43.117 and installed in the
production image by `uv sync --frozen --no-dev` (`backend/Dockerfile`).

Transitive dependencies covered by this record, at the versions locked in `backend/uv.lock`:
botocore 1.43.117, s3transfer 0.19.3, jmespath 1.1.0. Its other dependencies, `python-dateutil` and
`urllib3`, were already locked for other components and are unchanged.

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
- 2026-10-22 — undeclared → 1.43.117; declared as a required dependency (PRB-002, CR-001, TASK-157).
  Locked with botocore 1.43.117, s3transfer 0.19.3 and jmespath 1.1.0; no other locked package
  changed (CR-001 A-4). `ObjectStorageClient` is built from the real SDK by
  `backend/tests/test_object_storage.py`, and `import boto3` is checked in the production image by
  the Docker Build job (TS-007 TC-007.5, TS-013 TC-013.8). The anomaly-list review of this version
  is TASK-154.
