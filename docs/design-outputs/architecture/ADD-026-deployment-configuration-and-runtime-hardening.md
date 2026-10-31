---
id: "ADD-026"
type: architecture-doc
title: "Deployment configuration, secrets and runtime users (SI-DEPLOY)"
status: in_review
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
safety_class: B
links:
  - target: "SR-041"
    relation: implements
  - target: "SR-042"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "SR-022"
    relation: implements
  - target: "RISK-001"
    relation: relates_to
  - target: "RISK-005"
    relation: relates_to
  - target: "RISK-006"
    relation: relates_to
  - target: "RISK-007"
    relation: relates_to
  - target: "RISK-011"
    relation: relates_to
  - target: "SOUP-020"
    relation: relates_to
  - target: "SOUP-024"
    relation: relates_to
  - target: "SOUP-005"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
tags: ["software-item:SI-DEPLOY", "class:B", "layer:infrastructure", "cr:CR-004"]
---

# ADD-026 — Deployment configuration, secrets and runtime users (SI-DEPLOY)

## Responsibility

The deployment definition that MedHub ships, apart from the object store (SI-OBJSTORE, ADD-025):
the Compose topology and start-up order, the environment template, the start-up refusal of
missing or placeholder secrets, the database roles the services connect with, the trusted-proxy
setting, and the runtime users of the images MedHub builds. New item in CR-004; before it, these
concerns were spread over ADR-0010 and the deployment guide with no design record.

## Software units (IEC 62304 §5.4.1)

- `U-DEP-Compose` — `infra/docker-compose.yml`: every secret setting passed with a `:?` guard
  and no default (SR-041 AC 2); the `medhub` network with a fixed subnet (dynamic addresses from an `ip_range` that excludes the proxy's address, so no other
  container can take it first) and the reverse proxy at
  a fixed address, `TRUSTED_PROXIES` set to that address (SR-042 AC 3,
  [ADR-0019](../../design/adr/0019-originating-client-address-trusted-proxy-rule.md)); a one-shot
  `db-migrate` service that `backend` and `celery-worker` wait for
  ([ADR-0017](../../design/adr/0017-database-roles-and-append-only-audit-log.md)).
- `U-DEP-SecretRule` — `backend/app/core/secret_settings.py`: one rule for every secret setting
  (unset, empty, a known placeholder in any case, `change-me-to-…`, any value the template ever
  shipped; `AT_REST_ENCRYPTION_KEY` and `OBJECT_STORE_SSE_KEY` must decode to 32 bytes and differ;
  `SMTP_PASSWORD` required only when `SMTP_USER` is set, CR-004 Q-5). Called by the backend at
  start-up, by the worker on `worker_init`, and by the preflight. Messages name the setting,
  never the value (SR-041 AC 3, AC 5). It generalises the object-store rule of `U-OBJ-Preflight`.
- `U-DEP-EnvTemplate` — `infra/.env.example` with no value for any secret setting, and
  `infra/DEPLOY.md` stating how to generate each one (SR-041 AC 4).
- `U-DEP-DbRoles` — the owner role used only by `db-migrate` (`DATABASE_OWNER_URL`) and the
  runtime role used by `backend` and `celery-worker` (`DATABASE_URL`); the grants themselves are
  `U-PER-Roles` (ADD-016) (SR-023 AC 8, ADR-0017).
- `U-DEP-RuntimeUsers` — `backend/Dockerfile` (`USER medhub`, already in place) and
  `frontend/Dockerfile` (nginx master and workers as the image's unprivileged `nginx` user,
  listening on 8080, pid and temp paths under a writable directory; the reverse proxy targets
  `frontend:8080`). The pulled images (reverse proxy, PostgreSQL, Redis, SeaweedFS) are not built
  by MedHub and are outside SR-041 AC 1 (SR-041 AC 1).

Class B requires decomposition down to software units only.

## Requirements implemented

Software requirements: SR-041 (all AC), SR-042 AC 3, SR-023 AC 8 (deployment side), SR-022 AC 3
and SR-041 AC 5 (key settings).

## Interfaces

Settings consumed by the backend, the worker and the preflights: see `infra/DEPLOY.md` and
[12-interfaces.md](../../design/12-interfaces.md). New settings in CR-004: `DATABASE_OWNER_URL`,
`TRUSTED_PROXIES`, `AT_REST_ENCRYPTION_KEY_ID`, `AT_REST_ENCRYPTION_RETIRED_KEYS`,
`OBJECT_STORE_SSE_KEY`. Removed: `SESSION_SIGNING_KEY` (PRB-018).

## Architecture narrative

This record is a summary and traceability anchor. The narrative is
[07 deployment view](../../design/07-deployment-view.md) (topology, start-up order) and
[08 cross-cutting concepts](../../design/08-cross-cutting-concepts.md) §8.3 and §8.11
(configuration and secrets); the item belongs in the table of
[05 building blocks](../../design/05-building-blocks.md). TASK-201 brings those sections in line.
Governing decisions: [ADR-0010](../../design/adr/0010-deployment-model.md),
[ADR-0011](../../design/adr/0011-security-compliance-approach.md),
[ADR-0017](../../design/adr/0017-database-roles-and-append-only-audit-log.md),
[ADR-0018](../../design/adr/0018-field-encryption-key-identifier-and-key-separation.md),
[ADR-0019](../../design/adr/0019-originating-client-address-trusted-proxy-rule.md).

## Verification

TS-015 (new; SR-041) for the Compose and template assertions, the start-up refusals and the UID
checks on images and the started stack; TS-016 (new; SR-042) for the trusted-proxy setting on the
started stack; TS-009 for the runtime-role privilege test.

## Risk relevance

Carries controls of RISK-001 and RISK-005 (no known credential, no root process, no superuser
application credential), RISK-011 (separate keys) and RISK-006 (append-only by privilege). Its
own failure modes are availability effects at deployment time (RISK-007): a refused start-up
names the setting; a missing grant makes a statement fail until the next `db-migrate` run.

## Version history

- 1.0 (2026-10-31) — Created at the CR-004 Plan stage (Software Architect role), `in_review`.
- 1.1 (2026-10-31) — TASK-185: unit text confirmed against the implementation; `ip_range` added to `U-DEP-Compose` (found on the started stack: without it Docker gave the proxy's fixed address to another container). Content change, so the approval record is cleared and the record returns to review.
