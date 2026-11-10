---
id: "TASK-201"
type: task
title: "Bring arc42, the ADD records and the ADR index in line with CR-004"
status: approved
version: "1.6"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-08"
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

## Carried from the TASK-206 QA review (2026-11-07), via TASK-207

- LOW (finding 7): ADD-017 does not describe `_bind_celery_app()` (`backend/app/main.py`, the API lifespan sets the
  configured Celery app as the process default; PRB-071). Add it. ADD edits stay in this task.
- Residual note (human decision 2026-11-07, CR-004 D-19): list for the release's residual-anomaly evaluation, against
  SR-043 AC 4: a hand-crafted `Referer` that carries a token, or a token in the query string of another path, sent to a
  non-activation location during an upstream failure or a 413, is written to the proxy error log. No MedHub URL or
  browser flow produces it. SR-043's text is not edited.

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

- [x] Each SR-041/042/043 AC and SR-022 AC 6 to AC 8, SR-023 AC 6 to AC 9 is reflected in the
      arc42 section the ADDs point to (inspection, recorded in the handoff).
- [x] No ADD record still says "planned" or "CR-004 change" for something that is built.

## Verification

Inspection against the merged code; `traceability-check` on the ADD records.

## Definition of Done

- [x] arc42 sections updated; ADDs final and `in_review`.
- [x] `traceability-check` shows no error for ADD-005..026 touched by CR-004 (QA 2026-11-08: 0 errors over all ADDs, CR-004, TASK-201).

## Hand-off (2026-11-08, Document Writer role)

Documentation only; no source, test, SR, RISK, SOUP, PRB or CR file was edited.

**Inspection of the acceptance criteria against the arc42 sections** (section numbers are the files in `docs/design/`):

| Requirement | Where it is described |
|---|---|
| SR-041 AC 1 (non-root) | 05 `U-DEP-RuntimeUsers`; 07 "Network, start-up order and runtime users"; 08.3 least privilege |
| SR-041 AC 2, AC 4 (no defaults, empty template) | 05 `U-DEP-Compose`, `U-DEP-EnvTemplate`; 07 secrets; 08.11 secret settings |
| SR-041 AC 3 (refusal at start-up) | 05 `U-DEP-SecretRule`; 06.8; 08.3 |
| SR-041 AC 5 (separate keys) | 05 `U-OBJ-Preflight`, `U-OBJ-Server`; 06.11; 07 keys; 08.3, 08.11 |
| SR-042 AC 1 to AC 3 (address rule, setting) | 05 `U-API-ClientAddress`; 06.9; 07 network; 08.4 |
| SR-042 AC 4, AC 5 (retrieval limit) | 05 `U-API-RateLimit`; 10 |
| SR-043 AC 1 to AC 4 (logs) | 05 `U-WK` logging, `U-API-ErrorHandler`, `U-DEP-ProxyLogging`; 08.14; residual in 11 |
| SR-022 AC 6 to AC 8 (envelope, conversion, rotation) | 05 `U-PER-Crypto`, `U-PER-Migrations`; 06.10; 08.11 |
| SR-023 AC 6 (address) | 05 `U-AUD-Writer`; 08.4 |
| SR-023 AC 7 (every decision audited) | 05 `U-AUTHZ-Policy`; 08.2 |
| SR-023 AC 8 (append-only by privilege) | 05 `U-PER-Roles`; 07; 08.3, 08.4 |
| SR-023 AC 9 (typed fields) | 05 `U-AUD-Writer`; 08.4 (exact `target_id` shapes) |

**Records changed.** ADD-005 1.2, ADD-007 1.2, ADD-008 1.1, ADD-013 1.3, ADD-016 1.2, ADD-018 1.2 and ADD-025 1.4 were `approved`
and are `in_review` with the approval record cleared. ADD-006 1.3, ADD-012 1.6, ADD-017 1.3 and ADD-026 1.3 were `in_review`
and stay so. ADR-0010 and ADR-0019 carry dated notes; the ADR index already shows ADR-0017..0019 as Accepted.

**Open points for the human or later tasks** are listed in arc42 section 11 (residuals) and in the Document Writer's report:
the module-discovery decision, the unused keys in `celery-beat` and `db-migrate`, and the reverse-proxy UID 0 acceptance.
`traceability-check` has not been run by this role; QA runs it on ADD-005..026.

## QA review 1 (2026-11-08) — CHANGES REQUESTED

Spot-checked 30 claims against HEAD b905560: 27 hold. Traceability: 0 errors (7 old W5/W6 warnings on
records this task did not touch). Infra tests: 110 OK. The status goes back to `draft`.

1. **HIGH: the module-manifest remedy in DEPLOY.md is wrong** (`infra/DEPLOY.md:189-199`). The FK
   `fk_group_module_enablement_module_id` (`0001_initial.py:151-155`) has no `ON DELETE`.
   Disabling a module (`module_repo.set_enablement`, `module_repo.py:30-42`) sets `enabled=false`
   and keeps the row. So "disable it for the groups first" does not prevent the FK failure. A
   PostgreSQL 16 probe confirmed it: `DELETE FROM module_registry` fails with 23503 when a
   `group_module_enablement` row has `enabled=false`. The failure also stops the start. The
   lifespan logs "Module registry sync failed at startup" and re-raises (`backend/app/main.py:76-79`),
   so the backend does not start. That contradicts "the start does not fail" in the same paragraph.
   Rewrite it as verified, without "(not exercised on a stack)": the delete fails whenever a group
   has an enablement row for the module, enabled or not, and the backend then does not start.
   Remedy: fix the manifest, or reinstall the previous module version, and restart. Apply the same
   correction to `docs/design/11-risks-and-technical-debt.md:52` (the start already fails in this
   case, so the open decision is wider), `docs/design/05-building-blocks.md:100` ("discovery does not
   fail the start" holds for discovery only, not for the sync that follows) and
   `docs/design-outputs/architecture/ADD-013-audit-service.md:60-63`. The fail-at-start behaviour
   (also for a module that is simply uninstalled) is a code defect outside this task: raise a PRB.
2. **MEDIUM: "db-migrate holds field-key settings it does not use" is wrong**
   (`docs/design/07-deployment-view.md:31`, `docs/design/11-risks-and-technical-debt.md:51`,
   `docs/design-outputs/architecture/ADD-026-deployment-configuration-and-runtime-hardening.md:120-121`).
   `db-migrate` reads the field keyring in migration 0010 (`0010_field_encryption_key_id.py:175,191`)
   and in `reencrypt --verify-key-ids` (`reencrypt.py:233`). `infra/DEPLOY.md:37` already lists it
   correctly as a field-encryption user. Replace with: `celery-beat` holds object-store and field-key
   settings it does not use; `db-migrate` holds object-store settings it does not use.
3. **LOW: a decision basis that is never produced** (`docs/design/05-building-blocks.md:59`). The
   text lists `CONSENT:APPOINTMENT:{id}`. `decide()` returns `CONSENT:MANUAL` for any consent access
   (`backend/app/authz/service.py:269`), and the appointment form appears only in the docstring
   (`service.py:13,29`). Remove it, or state that consent decisions record `CONSENT:MANUAL` whatever
   the grant source.
4. **LOW: `evictedSession` is always present** (`docs/design/12-interfaces.md:78`). It is a required
   boolean (`backend/app/api/schemas/auth.py:39`, `openapi.json`). Write "carries `evictedSession`
   (boolean, camelCase), `true` when the login evicted the oldest session".
5. **LOW: malformed table row** (`docs/design/12-interfaces.md:87`). The row has a fifth, empty cell
   in a four-column table. Remove the trailing `|                                    |`.
6. **LOW: the shape list is written twice**
   (`docs/design-outputs/architecture/ADD-013-audit-service.md:46-53`). The `target_id` list is the
   same as section 8.4 (`08-cross-cutting-concepts.md`, Typed fields). Keep it in 8.4 and point to it
   from ADD-013, as `05-building-blocks.md` already does ("shapes in section 8.4").
7. **LOW, existing text in the edited table: wrong `SMTP_PASSWORD` row** (`infra/DEPLOY.md:40`). The
   row says `backend`, `celery-worker`. The `backend` service receives no `SMTP_PASSWORD`
   (`infra/docker-compose.yml`, backend `environment`), as 07 and 8.11 say. Change it to
   `celery-worker` only, with the rotation "recreate `celery-worker`".

Not a doc finding, for a later code task: the module docstring of `backend/app/core/client_address.py`
says `--forwarded-allow-ips=` is in `entrypoint.sh`. It is in the `CMD` of `backend/Dockerfile:24`.

## Round 2 hand-off (2026-11-08, Document Writer role)

QA findings 1 to 7 addressed; docs only. DEPLOY.md "Module manifests" now states the verified failure (FK `fk_group_module_enablement_module_id`,
backend does not start, remedy: fix the manifest or reinstall the previous version) and cites PRB-075;
the same correction is in arc42 05 `U-MH-Discovery`, arc42 11 and ADD-013 (1.4). `db-migrate` keys corrected in arc42 07, arc42 11 and ADD-026 (1.4).
`CONSENT:APPOINTMENT:{id}` removed from arc42 05; `evictedSession` and the empty table cell fixed in arc42 12; ADD-013 points to arc42 8.4 for the
`target_id` shapes; `SMTP_PASSWORD` is `celery-worker` only in DEPLOY.md (row and rotation step).

For TASK-202 (code docstring, not edited here): the `backend/app/core/client_address.py` docstring says `--forwarded-allow-ips=` is in `entrypoint.sh`;
it is in the `CMD` of `backend/Dockerfile` (line 24).

## QA review 2 (2026-11-08) — APPROVED

All seven findings of review 1 are fixed:

1. `infra/DEPLOY.md` "Module manifests", 05 `U-MH-Discovery`, 11 and ADD-013 1.4 now describe the
   foreign-key failure as verified: any enablement row blocks it, enabled or not. The backend does not
   start, and the remedy is to fix the manifest or reinstall the previous version. Each cites PRB-075,
   and PRB-075 is in the section 11 open table. The texts match PRB-075 and the review 1 facts,
   including the condition "when at least one module is valid" (`main.py`, `if manifests:`).
2. 07, 11 and ADD-026 1.4: `celery-beat` holds the object-store and field-key settings it does not
   use; `db-migrate` holds only the object-store settings it does not use.
3. `CONSENT:APPOINTMENT:{id}` is removed from 05.
4. 12: `evictedSession` is always present, `true` on eviction.
5. 12: the `routeRoles` row has four cells.
6. ADD-013 points to section 8.4 for the `target_id` shapes.
7. DEPLOY `SMTP_PASSWORD` names `celery-worker` only.

Traceability over all ADDs, CR-004, TASK-201 and PRB-075: 427 records, 0 errors. The 7 old W5/W6
warnings are on untouched records. Infra tests: 110 OK. The ADDs stay `in_review` for the human.
