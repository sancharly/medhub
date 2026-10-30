---
id: "TASK-180"
type: task
title: "Update the deployment guide, the ADD records and arc42 for the new object store"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-040"
    relation: implements
  - target: "SR-028"
    relation: implements
  - target: "RISK-012"
    relation: mitigates
  - target: "CR-002"
    relation: relates_to
  - target: "ADD-012"
    relation: relates_to
  - target: "ADD-024"
    relation: relates_to
  - target: "ADD-025"
    relation: relates_to
  - target: "TASK-177"
    relation: relates_to
  - target: "TASK-178"
    relation: relates_to
  - target: "TASK-179"
    relation: relates_to
tags: ["documentation", "arc42", "cr:CR-002", "issue:sancharly/medhub#33", "control:information"]
---

# TASK-180 — Update the deployment guide, the ADD records and arc42 for the new object store

- **Software item / unit:** documentation of SI-OBJSTORE (ADD-025), SI-ATTACH (ADD-012) and
  SI-DEVINFRA (ADD-024). No code.
- **Depends on:** TASK-177, TASK-178 and TASK-179 (`relates_to`), so that every fact described
  is already in place
- **Branch:** `bug/minio-object-store`
- **Size:** M (6–8 documentation files, text only). The Document Writer may take the arc42 part.

## Objective

CR-002 AC-20. `infra/DEPLOY.md` and the ADD and arc42 sections that describe the object store
and the deployment topology must match AC-1 to AC-6 and the component chosen by ADR-0015. That
means no console, scripted bucket administration, key generation, the network and SeaweedFS. The
deployment guide is the "information for safety" side of RISK-012's controls.

## Implementation detail

- **`infra/DEPLOY.md`:**
  - remove step 5 (console URL and `mc` commands);
  - describe what `object-store-init` does and how to re-run it
    (`docker compose run --rm object-store-init`);
  - describe bucket administration with scripted S3 calls from the backend image. **See CR-002
    Q-6** on the AC-20 wording "with `mc`".
  - keep TASK-174's key-generation step and TASK-178's migration section;
  - add the `object-store` network, the component and its version, and the monthly advisory
    check (PLAN-002 as revised by TASK-172).
- **ADD-012** (version from TASK-175):
  - `U-ATT-Fetch` now verifies the stored checksum and refuses with an audit FAILURE (TASK-173);
  - ADR-0015 is named among the governing decisions.
- **ADD-024**:
  - bump the version and clear the approval record;
  - `U-INF-CIPipeline` gains the job `object-store-integration` and the CI override file;
  - Verification lists TC-008.7.
- **ADD-025**:
  - check the units against the implemented services;
  - check the SOUP links (SOUP-019, SOUP-036; none to SOUP-022 or SOUP-023);
  - keep it `in_review`.
- **arc42** (`docs/design/`, following the `arc42` skill):
  - `07-deployment-view.md`: the table row "MinIO (S3)" becomes the new component, plus the
    `object-store` network, the preflight and the initialiser. The operational notes cover keys,
    no console and migration;
  - `05-building-blocks.md`: SI-OBJSTORE and its three units;
  - `11-risks-and-technical-debt.md`: the MinIO debt is closed, and the replacement's advisory
    cadence is named;
  - `12-interfaces.md`, only if it names MinIO or the console.
  - Update the deployment diagram (`docs/specifications/diagram-deployment.puml`) under the
    `plantuml` skill.
- **ADR-0009**: under Status, add "Amended by ADR-0015 (self-hosted product)". The ADR index
  already lists ADR-0015.
- **`docs/templates/task.md`**: replace "MinIO (S3 / SSE-AES256)" in the stack list with the
  chosen component.

## Acceptance criteria

- [ ] CR-002 **AC-20**: DEPLOY.md, ADD-012, ADD-024, ADD-025 and arc42 sections 05, 07 and 11 match
      AC-1..AC-6 and ADR-0015. `git grep -n -i "minio" docs/design infra/DEPLOY.md` returns only
      historical or migration mentions, each one deliberate.

## Verification

Inspection against the Compose file and the evidence of TASK-174..179, then `traceability-check`
for the ADD records. Render the PlantUML diagram once to check that it compiles.

## Definition of Done

- [ ] Every listed file is updated. No narrative is copied into the ADD records.
- [ ] `traceability-check` shows no error for ADD-012, ADD-024 and ADD-025.
