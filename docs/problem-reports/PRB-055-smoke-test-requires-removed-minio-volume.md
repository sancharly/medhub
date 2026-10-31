---
id: "PRB-055"
type: problem-report
title: "The smoke test still requires the minio_data volume that CR-002 removed"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
criticality: minor
links: []
tags: ["verification", "infrastructure"]
---

# PRB-055 — The smoke test still requires the minio_data volume that CR-002 removed

## Observed

On a healthy stack built from `bug/minio-object-store` after commit db0b480 (CR-002 TASK-178),
`infra/smoke-test.sh` reports 26 passed and 1 failed: section 8 reports "named volume
'minio_data' defined" as failed. Found by the software developer during TASK-179 and confirmed by
QA on 2026-10-30.

## Impact

The smoke test cannot pass in full, so CR-002 AC-16 cannot be met and the smoke test no longer
separates a healthy stack from a broken one.

## Investigation

Section 8 of `infra/smoke-test.sh` (line 125) loops over
`postgres_data redis_data object_store_data minio_data` and expects each name to be declared
under `volumes:` in `infra/docker-compose.yml`. TASK-178 removed the `minio_data` declaration (the
legacy volume is now named as external in `infra/migration/compose.minio-legacy.yml`), but the
smoke-test list was not updated. A regression introduced by CR-002 TASK-178.

## Safety evaluation

Verification tooling only: no product behaviour, data integrity, safety-related function or
clinical decision is affected. No released version exists, so no notification is needed. Hence
`minor`.

## Resolution

`minio_data` is removed from the section 8 loop of `infra/smoke-test.sh`
(`for vol in postgres_data redis_data object_store_data; do`). Fixed in the commit "CI, TEST: Check
object-store encryption end to end in CI (TASK-179)" on `bug/minio-object-store`; verify with
`git show <that commit> -- infra/smoke-test.sh`. The regression came with db0b480 ("FIX, DOC:
Migrate existing objects from MinIO, rehearsed on a backup (TASK-178)").

Verification (reproducible): start the stack in its own project with a temporary `infra/.env` made
from `infra/.env.example` with generated keys and `CORS_ORIGINS=[]` (PRB-056),
`COMPOSE_PROJECT_NAME=medhub-sm179b docker compose -f infra/docker-compose.yml up -d --build`, wait
about 45 seconds, then `bash infra/smoke-test.sh`. Before the change: 26 passed, 1 failed (named
volume 'minio_data' defined: missing). After: `=== Results: 26 passed, 0 failed ===`. The stack was
then removed with `down -v` and the dev `infra/.env` and volumes were unchanged.

## Source

Software developer and QA, CR-002 TASK-179 (2026-10-30).
