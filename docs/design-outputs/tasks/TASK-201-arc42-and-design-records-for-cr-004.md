---
id: "TASK-201"
type: task
title: "Bring arc42, the ADD records and the ADR index in line with CR-004"
status: draft
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-07"
links:
  - target: "SR-041"
    relation: implements
  - target: "SR-042"
    relation: implements
  - target: "SR-043"
    relation: implements
  - target: "SR-022"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-026"
    relation: relates_to
tags: ["documentation", "cr:CR-004", "control:information"]
---

# TASK-201 — Bring arc42, the ADD records and the ADR index in line with CR-004

- **Software item / unit:** documentation only (arc42 sections, ADD records, ADR index).
- **CR:** CR-004. The Document Writer may take it.
- **Depends on:** every CR-004 implementation task (TASK-137..142, TASK-185..200, TASK-203).
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (docs only)

## Carried from the TASK-195 QA review (2026-11-01)

- LOW: `infra/DEPLOY.md`, "Field-encryption key rotation", the paragraph after the command line says
  that a run which cannot get the table lock within 10 seconds "stops, unchanged". That holds only
  for the first batch. After it, the earlier batches stay committed: every row is readable, and the
  instruction ("run it again") is the same. Reword it to match the "If `--check` or `--apply` exits 1"
  section.

## Carried from the TASK-142 QA review (2026-11-06)

- LOW: ADD-018, `U-FE-RouteGuard`, names `navConfig.ts` as the role table. Replace "The role lists
  come from the same table as the navigation (`navConfig.ts`), so the two cannot diverge" with:
  "The role table is `frontend/src/core/nav/routeRoles.ts`; `navConfig.ts` derives its role lists
  from it, so the two cannot diverge." ADD-018 is human-approved, so the change needs re-approval.

## Objective

The narrative matches what was built. ADD records point at arc42; arc42 is not duplicated into
records.

## Scope

- `docs/design/05-building-blocks.md`: SI-DEPLOY row and units (ADD-026); new units
  `U-API-ClientAddress`, `U-API-RateLimit`, `U-PER-Roles`, `U-FE-RouteGuard`; `U-AUTHZ-Policy` as
  the only decision point; `U-OBJ-Server` SSE key.
- `docs/design/06-runtime-views.md`: start-up order with `db-migrate`; client address through the
  proxy.
- `docs/design/07-deployment-view.md`: `db-migrate`, fixed `medhub` subnet and proxy address,
  frontend on 8080, two database roles, two keys.
- `docs/design/08-cross-cutting-concepts.md` §8.2 (single decision point, every decision
  audited), §8.3 (non-root, placeholder refusal, key separation), §8.4 (address, append-only by
  privilege, typed fields; ADR-0017, ADR-0019), §8.11 (secret settings table, key rotation; ADR-0018).
- `docs/design/11-risks-and-technical-debt.md`: PRB-057 (no backup) still bounds key loss.
- `docs/design/12-interfaces.md`: new and removed settings.
- ADD-005, 006, 007, 013, 016, 017, 018, 025, 026: replace each "(CR-004 change)" unit note with
  the final unit text as built; keep them `in_review`.
- `docs/design/adr/README.md`: ADR-0017..0019 status as the human decided.

## Acceptance criteria

- [ ] Each SR-041/042/043 AC and SR-022 AC 6 to AC 8, SR-023 AC 6 to AC 9 is reflected in the
      arc42 section the ADDs point to (inspection, recorded in the handoff).
- [ ] No ADD record still says "planned" or "CR-004 change" for something that is built.

## Verification

Inspection against the merged code; `traceability-check` on the ADD records.

## Definition of Done

- [ ] arc42 sections updated; ADDs final and `in_review`.
- [ ] `traceability-check` shows no error for ADD-005..026 touched by CR-004.
