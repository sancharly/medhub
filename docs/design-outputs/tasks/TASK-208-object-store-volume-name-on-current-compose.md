---
id: "TASK-208"
type: task
title: "Give the object store volume a non-empty default name"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-10"
updated: "2026-11-10"
links:
  - target: "SR-041"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-004"
    relation: relates_to
  - target: "PRB-077"
    relation: relates_to
  - target: "TASK-196"
    relation: relates_to
  - target: "TASK-202"
    relation: relates_to
tags: ["deployment", "object-store", "cr:CR-004", "control:design"]
---

# TASK-208 — Give the object store volume a non-empty default name

- **Software items / units:** SI-DEPLOY (ADD-025, ADD-026).
- **PRB:** PRB-077. **CR:** CR-004 (D-22).
- **Depends on:** TASK-196 (committed). Reopens TASK-202's AC-1, which waits for a green hosted run.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** S.

## Objective

The `object_store_data` volume must have a valid name on every supported Compose version, with
`OBJECT_STORE_VOLUME` unset, empty or set, and an existing store must keep its volume.

## Implementation detail

- `infra/docker-compose.yml`: `name: ${OBJECT_STORE_VOLUME:-${COMPOSE_PROJECT_NAME}_object_store_data}`.
- An override file used only by the SSE-key procedure was rejected: the procedure leaves `OBJECT_STORE_VOLUME` set
  for good, so every later Compose command would have to name that file.
- A fixed default name was rejected: stacks with another project name would share one volume.

## Tests (write first)

In `infra/tests/test_compose_object_store.py`:

- `test_the_default_volume_name_is_the_project_default`: under `-p`, unset and empty both give `<project>_object_store_data`.
- `test_no_volume_name_can_render_empty`: a static check, because Compose 2.20 hides the defect at render time.
- `test_the_object_store_volume_defaults_and_can_be_named`: the default name must start with the project name.

## Acceptance criteria

- [x] AC-1: with `OBJECT_STORE_VOLUME` unset or empty the volume is `<project>_object_store_data`, with and without `-p`.
- [x] AC-2: with `OBJECT_STORE_VOLUME` set, the volume has that name.
- [x] AC-3: no volume name in the Compose file can render empty.
- [x] AC-4: the object store starts on a scratch stack, on the default-named volume.
- [x] AC-5: `Image Pin Check` and `Object Store Integration` are green on the hosted run of the fix. (runs 42779806388 (push) and 42779810219 (pull_request), head d53eb7f: all 8 jobs green.)

## Verification

1. `python3 -m unittest discover -s infra/tests -v`.
2. Start the object store on a scratch, project-scoped stack and inspect the volume name.
3. Read the two jobs on the hosted run after the push.

## Records

PRB-077, CR-004 (D-22, P10), TASK-202 (back to `draft` until the hosted run is green).

## Implementation notes and verification results (2026-11-10)

`python3 -m unittest discover -s infra/tests`: 114 tests, OK on Compose 2.20.2. AC-5 needs the hosted run.

## QA review (2026-11-10): APPROVED

No CRITICAL or HIGH finding. AC-5 is left unticked: it needs the hosted run, which cannot exist before the push.

### Findings

1. **LOW: on Compose 2.20.2 `COMPOSE_PROJECT_NAME` in the environment beats `-p` for this one expression, and can be empty.** `infra/docker-compose.yml:38`. Compose 2.20.2 sets the variable from the project name only when it is not already set. Result on 2.20.2: `-p qa208x` with `COMPOSE_PROJECT_NAME=qa208other` names the volume `qa208other_object_store_data` and mounts it; `COMPOSE_PROJECT_NAME=` (shell or `.env`) renders `_object_store_data`, and `up` stops with the daemon's invalid-name error. Compose 5.6.1 gives `<project>_object_store_data` in both cases. Neither the repository nor the CI job sets the variable that way, the empty case fails loudly, and `down -v` did not remove the other project's volume in the probe. So AC-1 holds in every configuration the project uses. → Add one sentence next to `infra/DEPLOY.md:60`: do not export `COMPOSE_PROJECT_NAME` with a value other than the `-p` name, and never set it empty.
2. **LOW: `test_no_volume_name_can_render_empty` covers one spelling.** `infra/tests/test_compose_object_store.py:318`. The regular expression catches only `name: ${VAR:-}`; `name: ${VAR}`, `name: ${VAR-}` or `name: ""` pass it. → Widen it to any `name:` whose value can be empty, or iterate over the `volumes` entries under Compose 5.
3. **LOW: D-22 is attributed differently in two records.** `docs/problem-reports/PRB-077-*.md`, Source says "orchestrator decision D-22"; CR-004 D-22 says "human decision 2026-11-10". → Make the two agree on who decided.

### Verification run

- `python3 -m unittest discover -s infra/tests -v`: 114 tests, OK on Compose 2.20.2. On Compose 5.6.1 (the Linux binary from the local `docker` image, run in a container on a scratch tree): 114 tests, OK; the HEAD Compose file on 5.6.1 reproduces the hosted failure, `KeyError: 'name'`, 1 error in 112 tests.
- AC-1, AC-2 (`docker compose config`, both Compose versions): unset and empty give `<project>_object_store_data` with `-p`, and without `-p` with the name derived from the directory (`infra`, and `My.Dir_x` normalised to `mydir_x`); a set value gives that name. HEAD on 5.6.1 has no `name` for the volume, as in the hosted run.
- AC-3: `object_store_data` is the only volume with a `name:` in both Compose files; a scan found no other empty name.
- AC-4, on throwaway `qa208*` projects from a scratch copy of `infra/` with a generated env file: the `object-store` service went healthy on `qa208a_object_store_data` (2.20.2) and `qa208e_object_store_data` (5.6.1). The HEAD file on 5.6.1 stops with `invalid volume name or ID: value is empty`.
- Upgrade: a volume made by the HEAD line (2.20.2), holding a marker file, was reused by the new line under the same project on 2.20.2 and then 5.6.1: same `CreatedAt`, same labels, marker intact, no new volume, no warning about the volume. With `OBJECT_STORE_VOLUME` set to a pre-existing volume, the store mounted that volume on both versions and no default volume was created.
- CI replay on 5.6.1 from a scratch checkout with the job's env step and `OBJECT_STORE_CI_PORT=18399`: `up -d --build --wait object-store-preflight object-store object-store-init` exit 0, init exit 0; `pytest -m object_store` 6 passed. Against the local daemon (24.0.5), not the runner's.
- `python3 infra/check_image_pins.py`: exit 0.
- Mutants on a scratch tree, each red: old line, a fixed default name, dropping `OBJECT_STORE_VOLUME`.
- Traceability parser: 0 errors.
- Docker clean-up: the scratch containers, volumes, networks and images were removed by name; the volume, network, image and container lists match the start.

## Version history

- 1.0 (2026-11-10) — Created and built; `in_review`.
- 1.1 (2026-11-10) — QA review: APPROVED (3 LOW). `in_review → approved`; AC-1 to AC-4 ticked; AC-5 waits for the hosted run. PRB-077 `resolved` (D-8).
- 1.2 (2026-11-10) — AC-5 ticked: runs 42779806388 (push) and 42779810219 (pull_request), head d53eb7f, all 8 jobs green. Status stays `approved`.
