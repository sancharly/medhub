---
id: "TASK-215"
type: task
title: "Record a fresh-volume bring-up from the environment template"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-12"
updated: "2026-11-12"
links:
  - target: "SR-041"
    relation: implements
  - target: "RISK-001"
    relation: mitigates
  - target: "CR-005"
    relation: relates_to
  - target: "PRB-038"
    relation: relates_to
  - target: "TASK-203"
    relation: relates_to
  - target: "TASK-214"
    relation: relates_to
tags: ["deployment", "verification", "cr:CR-005", "control:design"]
---

# TASK-215 — Record a fresh-volume bring-up from the environment template

- **Software item / unit:** SI-DEPLOY `U-DEP-Compose`, `U-DEP-EnvTemplate` (ADD-026).
- **PRB:** PRB-038. **CR:** CR-005 (AC-9; Q-1: verification only, no code change).
- **Depends on:** TASK-214 (the bring-up runs the final backend image, so its log also confirms
  AC-8 on a fresh volume).
- **Branch:** `bug/build-hygiene`.
- **Size:** XS (no source file; PRB-038 and this record).
- **Needs:** a Docker host.

## Objective

Show on a fresh volume that the template fixed by CR-004 TASK-203 (commit `4b1daf5`) brings the
stack up with `POSTGRES_PASSWORD`, and that an empty value stops Compose naming it (SR-041 AC 2,
AC 4). This closes the records gap of PRB-038; nothing is changed.

## Procedure

1. A scratch copy of `infra/` (or `-p task215` with a scratch env file), so the developer's
   `infra/.env` and volumes are untouched; check `docker volume ls` has no `task215_*` volume.
2. `.env` = `infra/.env.example` with only the required secret values filled, each generated with
   the command the template names. `DATABASE_OWNER_URL` uses the generated `POSTGRES_PASSWORD`;
   `DATABASE_URL` uses the runtime role and its own password (`infra/DEPLOY.md`).
3. `docker compose -p task215 up -d --build --wait` → exit 0; `postgres` initialised a new
   cluster (log line "database system is ready", no "Database directory appears to contain a
   database"); `db-migrate` exited 0.
4. `COMPOSE_PROJECT_NAME=task215 infra/smoke-test.sh` → every check passed, 0 failed (80 checks at
   HEAD; record the actual count).
5. The same `.env` with `POSTGRES_PASSWORD=` (empty): `docker compose -p task215 config` stops with
   `POSTGRES_PASSWORD must be set`.
6. `docker compose -p task215 down -v`; `docker volume ls` shows no `task215_*` volume and the
   developer's volumes as before.

## Acceptance criteria

- [ ] CR-005 AC-9: steps 3, 4 and 5 give the stated results; outputs recorded below; teardown
      leaves no `task215` resource.
- [ ] Records: PRB-038 `## Resolution` cites TASK-203 and commit `4b1daf5` as the fix and this
      task as the verification (Q-1); `resolved` only after QA approves.

## Verification

The procedure above is the verification. QA repeats steps 3 to 5 on its own scratch project.

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
