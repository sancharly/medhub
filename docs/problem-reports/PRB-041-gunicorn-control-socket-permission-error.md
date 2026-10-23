---
id: "PRB-041"
type: problem-report
title: "Gunicorn control server fails on every start because the service user has no home"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
criticality: minor
links: []
tags: ["operations", "logging", "soup"]
---

# PRB-041 — Gunicorn control server fails on every start

## Observed

On every backend start the log shows
`[ERROR] Control server error: [Errno 13] Permission denied: '/home/medhub'`. The API workers start
and serve normally (login through the proxy returns 401).

## Investigation

- `backend/Dockerfile:18` creates the service user with `useradd -r` and no `-m`, so its `HOME`,
  `/home/medhub`, does not exist and `/home` is `root:root 755`.
- Gunicorn 26.0.0 (SOUP-005) enables its control socket by default (since 25.1.0). With
  `XDG_RUNTIME_DIR` unset it tries to create `$HOME/.gunicorn/gunicorn.ctl`; the control-server
  thread dies with `Errno 13` (`gunicorn/ctl/server.py:184` in the image).
- Effect: the `gunicornc` management interface (worker status, graceful reload) is unavailable.
  Nothing in the repository uses it.

## Impact

- No functional impact on the API.
- An ERROR line on every normal start trains operators to ignore backend log errors, which the
  monitoring behind RISK-007 relies on.
- An unused management interface is enabled by default.

## Safety evaluation

No effect on data integrity, a safety-related function or a clinical decision. No `release` record
exists, so no released version is affected and no notification is needed. Hence `minor`.

## Proposed resolution

Disable the unused control socket by adding `--no-control-socket` to the `gunicorn` command in
`backend/entrypoint.sh` (preferred), or create the user's home with `useradd -m`. Record in SOUP-005
that the control socket is on by default. Needs a task and a CR.

## Source

Observed by the software developer during TASK-160 verification and confirmed by QA (2026-10-22).
Predates CR-001, which did not change the Gunicorn version; outside CR-001's scope.
