---
id: "PRB-038"
type: problem-report
title: "POSTGRES_PASSWORD is required by Compose but absent from .env.example"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
criticality: minor
links: []
tags: ["configuration-management", "infrastructure"]
---

# PRB-038 — POSTGRES_PASSWORD is required by Compose but absent from .env.example

## Observed

`infra/docker-compose.yml` sets `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}` on the `postgres` service,
and `infra/DEPLOY.md` lists `POSTGRES_PASSWORD` among the required variables, but
`infra/.env.example` does not define it (it defines only `DATABASE_URL`, with the password
`changeme`). Every `docker compose` invocation from a copy of the example prints
`The "POSTGRES_PASSWORD" variable is not set. Defaulting to a blank string.` (observed 2026-10-22,
local `infra/.env`, which also lacks it).

## Impact

- On a fresh `postgres_data` volume the `postgres` image is expected to refuse to initialise with an
  empty superuser password (not run: it would require deleting the developer's volume). A new
  deployment following `.env.example` would not come up.
- On an existing volume the password set at first initialisation stays in force, which hides the
  gap, and `DATABASE_URL` and `POSTGRES_PASSWORD` can silently disagree.

## Safety evaluation

No hazard is realized: the failure is at bring-up and loud, or masked by an existing volume. A blank
password on a network-internal database is a configuration weakness (RISK-001 is about PHI at rest
and in transit), not a control the software relies on. Hence `minor`.

## Proposed resolution

Add `POSTGRES_PASSWORD` to `infra/.env.example` with the same placeholder as `DATABASE_URL`, and
state in DEPLOY.md that the two must match. Needs a task.

## Source

Found by the software developer while running TASK-155 verification (AC-5); out of scope for CR-001.
