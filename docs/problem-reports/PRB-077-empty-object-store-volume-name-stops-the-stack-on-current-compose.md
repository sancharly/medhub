---
id: "PRB-077"
type: problem-report
title: "The object store cannot start on current Docker Compose because its volume name renders empty"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-10"
updated: "2026-11-10"
criticality: major
links: []
tags: ["deployment", "hazard:availability", "found-in:ci-pr-38"]
---

# PRB-077 — The object store cannot start on current Docker Compose because its volume name renders empty

## Observed

Found by the first hosted CI run of the CR-004 branch (PR #38, head 366cba9, runs 42776350360 and 42776389757).

- `Object Store Integration`: `up` stopped with `invalid volume name or ID: value is empty`.
- `Image Pin Check`: the `infra/tests` step failed with `KeyError: 'name'` in
  `test_the_object_store_volume_defaults_and_can_be_named`; 1 error in 112 tests.

Every local run passed on Docker Compose 2.20.2.

## Impact

Availability at deployment time: where Compose rejects the empty name, the object store does not start, so
attachments are unavailable (RISK-007). The stack refuses to start with an error that does not name the variable.
No data is disclosed or altered.

## Investigation

TASK-196 added `name: ${OBJECT_STORE_VOLUME:-}` to the `object_store_data` volume. With the variable unset or empty,
as on every installation that has not run the SSE-key copy, the name renders empty. Compose 2.20.2 replaces an empty
name with `<project>_object_store_data`. The Compose on the CI runner does not. The runner's exact version was not
recorded.

## Safety evaluation

Failure to start is loud and nothing is changed, so no wrong clinical information is shown. Criticality **major**: a
default installation cannot start on the affected Compose versions. Contributes to RISK-007. No release exists
(CR-004 A-1), so no notification is needed. The human sets the final criticality.

## Resolution

TASK-208 (CR-004 D-22). The default is written out: `name: ${OBJECT_STORE_VOLUME:-${COMPOSE_PROJECT_NAME}_object_store_data}`.
It is the name Compose gave the volume before, so an existing store keeps its data, and `OBJECT_STORE_VOLUME` works
as before for the SSE-key procedure. `.env` keeps the variable, so a store already switched to another volume is
unaffected.

## Source

Hosted CI on PR #38; human decision D-22.

## Version history

- 1.0 (2026-11-10) — Created from the first hosted CI run; fix in TASK-208. The CR-004 `resolves` link is in place. Stays `open` until QA approves TASK-208 (D-8).
- 1.1 (2026-11-10) — TASK-208 approved by QA; `open → resolved` (D-8). The hosted run (TASK-208 AC-5) is still to come.
