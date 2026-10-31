---
id: "PRB-057"
type: problem-report
title: "No backup and restore procedure exists for the database or the object store, although the design says one is documented"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
criticality: major
links: []
tags: ["operations", "durability", "documentation"]
---

# PRB-057 — No backup and restore procedure exists for the database or the object store, although the design says one is documented

## Observed

While updating the deployment documentation for CR-002 TASK-180 on 2026-10-30, the document writer
found no backup and restore procedure for the new `object_store_data` volume. QA confirmed that
`infra/DEPLOY.md` has none for PostgreSQL either, while the design records claim that backups are
documented.

## Impact

An operator has no tested way to back up or restore clinical data (`postgres_data`) or attachments
(`object_store_data` together with `AT_REST_ENCRYPTION_KEY`, without which the objects cannot be
decrypted). A disk loss or a failed upgrade could lose patient records. The design records state
the opposite, so the gap is hidden from a reviewer.

## Investigation

- `infra/DEPLOY.md` has no backup or restore section for `postgres_data` or `object_store_data`. The
  only backup steps are the one-off ones in "Migrating from MinIO" (CR-002 TASK-178).
- ADR-0010 (`docs/design/adr/0010-*.md:37`) and arc42 section 11 say backups are "documented",
  which is untrue.
- The object store's SSE key derives from `AT_REST_ENCRYPTION_KEY` (ADR-0015, SOUP-036), so a volume
  backup without the key cannot be restored, and nothing says so outside the migration section.
- The TASK-180 rewrite of arc42 07 "Backups" leaves a TODO pointing at this gap.

## Safety evaluation

Data integrity and availability of clinical records and attachments (UN-008 durability) depend on a
restore path that does not exist. No incorrect data is shown and no clinical function misbehaves,
so no direct patient harm follows from the defect alone; loss of records could affect continuity of
care. Hence `major`, not `critical`. No released version exists, so no notification is needed.

## Proposed resolution

Write and rehearse a backup and restore procedure in `infra/DEPLOY.md` covering `postgres_data`
(`pg_dump`/restore), `object_store_data` and the `AT_REST_ENCRYPTION_KEY` it depends on, with a
restore check (attachments download with matching checksums). Correct ADR-0010 and arc42 section 11.
Consider whether a requirement for backup and restore exists and is verified. Needs a task and a CR;
outside CR-002's scope.

## Source

Document writer and QA, CR-002 TASK-180 (2026-10-30).
