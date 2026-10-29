---
id: "TASK-167"
type: task
title: "Correct the API-client description in arc42 and the building-block diagram"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-29"
updated: "2026-10-29"
links:
  - target: "SR-031"
    relation: implements
  - target: "CR-003"
    relation: relates_to
  - target: "PRB-044"
    relation: relates_to
  - target: "TASK-166"
    relation: relates_to
tags: ["documentation", "architecture", "arc42", "cr:CR-003", "issue:sancharly/medhub#32"]
---

# TASK-167 — Correct the API-client description in arc42 and the building-block diagram

- **Software item / unit:** SI-FE-APICLIENT. arc42 narrative only; no code and no design element.
- **Depends on:** TASK-166 (`relates_to`). The arc42 text follows ADD-023's corrected wording.
- **Branch:** `bug/soup-upgrades`
- **Size:** S
- **Needs:** nothing beyond the repository. Optionally a PlantUML renderer to check that the
  diagram still compiles.
- **Role:** the Document Writer may do this task, because arc42 is the Document Writer's narrative
  (the `arc42` skill, `arc42-root: docs/design/`).

## Objective

Finish PRB-044. The arc42 sections and the building-block diagram repeat the claim that the
SPA's API client is "generated from OpenAPI". Make them say what the code does, in the same
words as ADD-023 (TASK-166): a hand-written `ApiClient` with generated types. Then resolve
PRB-044.

## Implementation detail

Change only the lines below, and match each file's existing table and line format:

- `docs/design/03-context-and-scope.md:31` (SPA ↔ Backend API row): "Hand-written typed client
  (`ApiClient`) with types generated from OpenAPI (api-design.md)".
- `docs/design/05-building-blocks.md:33` (SI-FE-APICLIENT row): "Hand-written typed `ApiClient`
  (types generated from OpenAPI); session/CSRF handling".
- `docs/design/05-building-blocks.md:124` (`U-FEAPI-Client`): the same text as ADD-023's unit line.
- `docs/design/12-interfaces.md:48` (SI-FE-APICLIENT row): replace "methods generated from
  OpenAPI" with "hand-written methods; request/response types generated from OpenAPI".
- `docs/specifications/diagram-building-blocks.puml:14`: the label becomes
  `"API Client\n(hand-written; types from OpenAPI)"`. Keep the alias and the colour tag, as the
  house PlantUML style requires.

`docs/design/adr/0003-frontend-stack.md:15` ("via generated client types") is accurate and is
not changed.

**PRB-044** → `status: resolved`, `version: "1.2"`, with a `## Resolution`. It names:

- the files of TASK-165, TASK-166 and this task;
- the AC-10 checks and the `dist/` checksum result;
- the record checks below.

## Acceptance criteria

- [ ] CR-003 **AC-12** (arc42 part): no statement in `03-context-and-scope.md`,
      `05-building-blocks.md` (table row and unit), `12-interfaces.md` (SI-FE-APICLIENT row) or
      `diagram-building-blocks.puml` says that the client or its methods are generated.
- [ ] CR-003 **AC-19** (PRB-044 part): PRB-044 is `resolved` with its `## Resolution`.

## Verification

```sh
grep -n -i 'client generated\|generated typed client\|methods generated\|(generated from OpenAPI)' \
  docs/design/03-context-and-scope.md docs/design/05-building-blocks.md \
  docs/design/12-interfaces.md docs/specifications/diagram-building-blocks.puml       # no output
```

If a renderer is available, run `plantuml -checkonly docs/specifications/diagram-building-blocks.puml`.

## Definition of Done

- [ ] PRB-044 is `resolved`.
- [ ] `traceability-check` shows no error for PRB-044 and CR-003.
