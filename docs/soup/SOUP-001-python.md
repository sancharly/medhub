---
id: SOUP-001
type: soup
title: Python runtime
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Python Software Foundation
soup_version: 3.12.15
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-22"
approved_digest: eb8b9848d029ba66a7d16ece8db2f50d86f5f19e82406ce35d2ba6524034e7bd
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-001 — Python runtime 3.12.15

## Functional and performance requirements

Language runtime and standard library for every backend item, including `secrets` and `hashlib` for tokens and digests.

## Required hardware and software environment

Debian-based `python:3.12.15-slim` container image; base OS Debian GNU/Linux 13 (trixie) (A-5: the base OS is part of this item, identified by the digest).

| Full image reference | Used by |
|---|---|
| `python:3.12.15-slim@sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2` | `backend/Dockerfile`: builder stage and runtime stage (identical reference) |

Resolved on 2026-10-22 with `docker buildx imagetools inspect python:3.12-slim` and `docker buildx imagetools inspect python:3.12.15-slim`; both reported the same image configuration (`PYTHON_VERSION=3.12.15`). The digest is the multi-arch image index digest (`Digest:` line of the second command). Tests ran on CPython 3.12.3.

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
- 2026-10-22 — `python:3.12-slim` → `python:3.12.15-slim@sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2`; pinned at the version the tag resolved to, no upgrade (CR-001 A-4, TASK-155); PRB-001.
