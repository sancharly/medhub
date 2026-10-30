---
id: "PRB-055"
type: problem-report
title: "The smoke test still requires the minio_data volume that CR-002 removed"
status: open
version: "1.0"
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

## Proposed resolution

Remove `minio_data` from the section 8 loop and rerun the smoke test on a started stack, expecting
a full pass. In scope for CR-002 and resolved by TASK-179.

## Source

Software developer and QA, CR-002 TASK-179 (2026-10-30).
