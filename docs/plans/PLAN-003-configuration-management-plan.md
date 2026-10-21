---
id: PLAN-003
type: lifecycle-plan
title: Software configuration management plan
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
plan_kind: configuration-management
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: b3b7032ad26acec9dc30d31515db7823cdc6430cab90cf52c625369dc541de42
approval_note: self-approved
links: []
tags:
  - regulatory
  - class:B
---

# PLAN-003 — Software configuration management plan

IEC 62304:2006+A1:2015 §8. Split out of ADD-002 (v2.0) when the plans became `lifecycle-plan`
records.

## Configuration items (§8.1.1)

Source code, configuration, build and deployment files, and the design records under `docs/`
all live in one git repository. Everything a lifecycle stage produces is version-controlled; CI
test reports need not be committed.

## SOUP identification (§8.1.2)

Every third-party component is one `soup` record in [`../soup/`](../soup/), with title,
`manufacturer` and the exact `soup_version` resolved by the lock files (`backend/uv.lock`,
`frontend/package-lock.json`) or by the pinned container image. A range or floating tag that no
lock file pins is a finding.

## Identification of the released system (§8.1.3)

Each release is a `release` record with `release_version`, tagged in git; the record's `git_tag`
names the tag.

## Change control (§8.2) and Git Flow

Code, documentation and design records live in one git repository; everything a stage produces is
version-controlled. SOUP items are identified with title, manufacturer and exact version in the SOUP
list (§8.1.2), pinned by the lock files.

One branch per unit of work, named `feature/…`, `user-story/…`, `enabler-story/…`, `bug/…` or
`doc/…`, merged to `main` through a pull request. Automated test reports produced by CI need not be
committed. Commits follow the `commit-message` skill.

- Every change is made on a branch and merged through a pull request; nothing is pushed to
  `main` directly.
- `/ship-feature` commits each QA-approved task on the feature branch, with that task's records
  in the same commit. Pushing and opening the pull request need the human's confirmation.
- An `approved` design record is never edited in place: it returns to `draft`, gets a new
  `version`, and is reviewed again.

## Configuration status accounting (§8.3)

Record history is git history; the current status of every configuration item is its record
`status`, reported by `traceability-check` into `docs/reports/`.
