---
id: "TASK-171"
type: task
title: "Correct the API-client wording in the task template, and re-check traceability"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-028"
    relation: implements
  - target: "CR-003"
    relation: relates_to
  - target: "ADD-023"
    relation: relates_to
  - target: "TASK-167"
    relation: relates_to
  - target: "TASK-169"
    relation: relates_to
  - target: "TASK-170"
    relation: relates_to
tags: ["documentation", "templates", "cr:CR-003", "issue:sancharly/medhub#32"]
---

# TASK-171 — Correct the API-client wording in the task template, and re-check traceability

- **Software item / unit:** none. `docs/templates/task.md` is the body template for TASK records.
- **Depends on:** TASK-169 and TASK-170 (`relates_to`), for the final `traceability-check`.
- **Branch:** `bug/soup-upgrades`
- **Size:** XS
- **Needs:** nothing.

## Objective

Finish the PRB-044 correction (CR-003 D-7). TASK-166 and TASK-167 corrected ADD-023 and arc42,
but the task template, which every new TASK copies, still calls the frontend API client
"generated". Make it describe the client as ADD-023 does. Then run `traceability-check` over the
whole project, because TASK-168's run predates TASK-169..171.

## Implementation detail

1. `docs/templates/task.md`:
   - repo layout (line 76): `api/(generated client)` → `api/(client.ts, generated/ types)`;
   - frontend conventions (line 90): "typed client generated from OpenAPI" → "hand-written
     `ApiClient` (`frontend/src/api/client.ts`) using types generated from the OpenAPI schema
     (ADD-023)".
2. Run `traceability-check` over the whole project.

## Acceptance criteria

- [x] CR-003 **AC-22**: no sentence in `docs/templates/task.md` says the API client is generated.
- [x] CR-003 **AC-19** (after D-7): `traceability-check` reports 0 errors, and PRB-049 and PRB-050
      show as resolved through CR-003.

## Verification

```sh
grep -n 'generated' docs/templates/task.md   # only the types are generated
```

## Definition of Done

- [x] `traceability-check` over the whole project reports 0 errors.

## Evidence (developer handoff, 2026-10-30)

- `docs/templates/task.md` lines 76 and 90–91 changed as in Implementation detail.
  `grep -n generated docs/templates/task.md` matches three lines: the two corrected ones, which
  both say that the types are generated, not the client, and `:60` ("OpenAPI regenerated and
  re-linted"), which is about the schema and the types. *(Corrected after the QA review's LOW
  finding; the count was two.)*
- `traceability-check` (the fallback parser of the TASK-168 run, `medical-records` 0.3.2 rules),
  whole project, on the working tree with TASK-169..171, CR-003 1.4 and PRB-049/050 1.1: 353
  records, **0 errors**. Warnings: W1 3, W2 4, W7 1, W3 1, W6 1 (all unchanged from the
  2026-10-30 report), W5 1 (the pre-existing TASK-132 → TASK-101). No class-gated finding. No
  warning names TASK-169..171, PRB-049, PRB-050 or CR-003.

## QA review (2026-10-30)

**Verdict: APPROVED** (`in_review → approved`). There is one LOW finding, in the Evidence text. It
does not affect the template.

**Review notes.**
- `docs/templates/task.md:76` lists `api/(client.ts, generated/ types)`. `:90-91` describes a
  hand-written `ApiClient` (`frontend/src/api/client.ts`) using types generated from the OpenAPI
  schema (ADD-023). That matches ADD-023 (`:31-34`) and the code: `frontend/src/api/client.ts:41`
  is `export class ApiClient`, and `frontend/src/api/generated/` holds `openapi.ts` and `types.ts`.
  No sentence says the client is generated (AC-22).
- AC-19 after D-7: CR-003 1.4 has `resolves` links to PRB-049 and PRB-050, and both are `resolved`
  1.1 with a `## Resolution`. The fallback parser reports 0 errors.

### Findings

- **[LOW] The Evidence miscounts the `grep` matches.** `TASK-171:68-70` says
  `grep -n generated docs/templates/task.md` "now matches only the two corrected lines". It matches
  three. `:60` ("OpenAPI regenerated and re-linted (API tasks only)") is also a match, because
  "regenerated" contains "generated". That line is about the schema and the types, not the client,
  so the template is correct. Fix: in the Evidence, say "three lines: the two corrected lines and
  the `:60` DoD item about regenerating the OpenAPI schema".

### Verification run (QA, 2026-10-30)

| Check | Result |
|---|---|
| `git diff docs/templates/task.md` | 2 hunks: `:76` and `:90-91`, as in Implementation detail |
| `grep -n -i generat docs/templates/task.md` | `:60` (OpenAPI regenerated), `:76`, `:91`. Each one is about the types or the schema |
| ADD-023 `:31-34` and `frontend/src/api/` | Hand-written `ApiClient` in `client.ts`; `generated/openapi.ts`, `generated/types.ts` |
| `traceability-check` (fallback parser, `medical-records` 0.3.2 rules), whole project, working tree | 353 records, **0 errors**, 0 class-gated. Warnings: W1 3, W2 4, W3 1, W6 1, W7 1, all as in `docs/reports/gap-report-2026-10-30.md`. W5 1 (pre-existing TASK-132 → TASK-101). The 40 CR-003 W5s in that report were cleared by the design review (e29894c). No warning names TASK-169..171, PRB-049, PRB-050 or CR-003 |
| Same check, after QA set TASK-169..171 `approved` 1.1 | Unchanged: 353 records, 0 errors, 0 class-gated, 11 warnings (the same list). Approving the three tasks adds no W5 |
