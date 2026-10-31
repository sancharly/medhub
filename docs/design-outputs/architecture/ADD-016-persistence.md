---
id: ADD-016
type: architecture-doc
title: Persistence (SI-PERSIST)
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-31"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-31"
approval_note: self-approved at the ship-feature plan gate (sancharly/medhub#27, CR-004)
links:
  - target: SR-003
    relation: implements
  - target: SR-004
    relation: implements
  - target: SR-021
    relation: implements
  - target: SR-022
    relation: implements
  - target: SR-031
    relation: implements
  - target: RISK-002
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: RISK-011
    relation: relates_to
  - target: SOUP-006
    relation: relates_to
  - target: SOUP-008
    relation: relates_to
  - target: SOUP-009
    relation: relates_to
  - target: SOUP-010
    relation: relates_to
  - target: SOUP-011
    relation: relates_to
  - target: SOUP-020
    relation: relates_to
  - target: SR-023
    relation: implements
  - target: RISK-006
    relation: relates_to
tags:
  - software-item:SI-PERSIST
  - class:B
  - layer:backend
---

# ADD-016 — Persistence (SI-PERSIST)

## Responsibility

SQLAlchemy models, repositories, Alembic migrations, encryption-at-rest config

## Software units (IEC 62304 §5.4.1)

- `U-PER-Models` — SQLAlchemy ORM models (FHIR-aligned, SR-021).
- `U-PER-Repos` — repositories with parameterized queries (SR-031.1).
- `U-PER-Migrations` — Alembic migrations (NFR-006).
- `U-PER-Crypto` — at-rest encryption config / pgcrypto where needed (SR-022).
- `U-PER-Crypto` (CR-004 change) — AES-256-GCM field envelope
  `mh1:<key-id>:<base64url(nonce || ciphertext)>` with the prefix as associated data; current key
  plus optional retired keys from settings; unknown key or missing prefix refused; re-encryption
  command `app.db.reencrypt` (`--check`, `--apply`) for rotation (SR-022 AC 6 to AC 8,
  [ADR-0018](../../design/adr/0018-field-encryption-key-identifier-and-key-separation.md)).
- `U-PER-Migrations` (CR-004 change) — migration 0009 drops the `audit_log` rules of 0006;
  migration 0010 converts existing encrypted values to the identified envelope in one
  transaction (SR-022 AC 7). Migrations run only in the `db-migrate` service, as the owner role.
- `U-PER-Roles` (new, CR-004) — `app.db.roles`: creates the runtime role and applies its grants
  after every migration run, revoking `UPDATE`, `DELETE`, `TRUNCATE` on `audit_log` (SR-023 AC 8,
  [ADR-0017](../../design/adr/0017-database-roles-and-append-only-audit-log.md)).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-003, SR-004, SR-021, SR-022, SR-031; CR-004 adds SR-023 (AC 8).
Non-functional requirements constraining this item: —.

## Interfaces

Provided and consumed interfaces are specified in
[12-interfaces.md](../../design/12-interfaces.md); the runtime interactions this item takes part in
are in [06-runtime-views.md](../../design/06-runtime-views.md) and the sequence diagrams under
[`../../specifications/`](../../specifications/).

## Architecture narrative

This record is a summary and traceability anchor, not the narrative. The design itself is in the
arc42 sections — [05 building blocks](../../design/05-building-blocks.md) for the decomposition,
[04 solution strategy](../../design/04-solution-strategy.md),
[08 cross-cutting concepts](../../design/08-cross-cutting-concepts.md) and, for deployment,
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0004](../../design/adr/), [ADR-0006](../../design/adr/), [ADR-0007](../../design/adr/), [ADR-0009](../../design/adr/), [ADR-0010](../../design/adr/), [ADR-0011](../../design/adr/), [ADR-0017](../../design/adr/0017-database-roles-and-append-only-audit-log.md), [ADR-0018](../../design/adr/0018-field-encryption-key-identifier-and-key-separation.md).

## Risk relevance

Participates in RISK-002, RISK-007, RISK-011 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): unit changes for the planned design added (marked "CR-004"), links added. Content change, so the approval record is cleared and the record returns to review. The implementing tasks confirm the unit text when they land.
