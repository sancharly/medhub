---
id: "TASK-225"
type: task
title: "arc42 sections, ADR index and deployment guide for CR-006"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
links:
  - target: "SR-013"
    relation: implements
  - target: "SR-017"
    relation: implements
  - target: "SR-026"
    relation: implements
  - target: "SR-030"
    relation: implements
  - target: "CR-006"
    relation: relates_to
tags: ["cr:CR-006", "documentation", "arc42"]
---

# TASK-225 — arc42 sections, ADR index and deployment guide for CR-006

- **Role:** Document Writer (arc42 narrative); the Software Architect reviews consistency with the ADDs.
- **CR:** CR-006. **Depends on:** TASK-135 … TASK-224 committed (documents what was built, not the plan).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** M (docs only).

## Objective

Keep the arc42 narrative consistent with the ADD records changed at the CR-006 Plan stage and with the code
(the ADD records point to these sections and must not duplicate them).

## Sections to update (`docs/design/`)

| Section | Change | From |
|---|---|---|
| 04 solution strategy | Concurrency model: blocking IO in the thread pool, pools sized together | ADR-0022, TASK-136 |
| 05 building blocks | `U-ATT-Upload` / `U-ATT-Fetch` bounded IO; DICOM module bounds; frontend lazy routes, `useMe`, `useMyModules` | ADD-012, 015, 018, 019, 020/021 |
| 06 runtime views | Attachment download (two passes, `If-Match`, abort); upload size refusal; erasure refused when its e-mail cannot be queued; retention retry | ADR-0021, TASK-141, 217 |
| 07 deployment view | nginx `client_max_body_size`; `API_THREADPOOL_SIZE`, `DB_POOL_*` (values as approved by the human, D-14); migration 0011 locks four tables while building | TASK-135, 136, 219 |
| 08 cross-cutting concepts | Client session timers from the server expiry; debounced activity; chunk-failure boundary; error contract of the 503 erasure response | TASK-144, 145, 222, 141 |
| 10 quality requirements | Normal load = 20 clients on one worker (D-3); initial-payload budget (SR-026 AC 7 value); 150 MiB / 1 GiB bounds (D-2) | SR-026, SR-017 |
| 11 risks and technical debt | NumPy absent so the frame decode cannot render (PRB-048); two object-store reads per download | P-6, ADR-0021 |
| 12 interfaces | `PlatformServices.attachments.open(..., max_bytes)`; `GET /me` `sessionExpiresInSeconds`; extend `expiresInSeconds`; erasure 503 | TASK-217, 144, 141 |

Also: `docs/design/adr/README.md` index lines for ADR-0021 and ADR-0022 (status as decided at the plan gate);
`infra/DEPLOY.md` (pool settings, body limit, migration 0011 window); remove any request-id promise found by
TASK-224.

## Acceptance criteria

- [ ] Every row above done or marked "no change" with a reason; links from ADD-005, 008, 009, 012, 015, 016,
  017, 018, 019, 020, 021, 023 resolve.

## Definition of Done

- [ ] `traceability-check` no error for this record

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect).
