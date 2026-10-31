---
id: "TASK-200"
type: task
title: "Anchor the module version expression fully"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
links:
  - target: "SR-016"
    relation: implements
  - target: "PRB-028"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-014"
    relation: relates_to
tags: ["security", "modules", "cr:CR-004"]
---

# TASK-200 — Anchor the module version expression fully

- **Software item / unit:** SI-MODHOST discovery (ADD-014).
- **PRB:** PRB-028. **CR:** CR-004.
- **Depends on:** none. Independent; can run in parallel.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** XS (`backend/app/modules/discovery.py`; 1 test file; TS-010)
- **Risk:** no hazard (PRB-028 Safety evaluation; ADR-0005 trusted modules), so no `mitigates`
  link; recorded as "no impact" in CR-004's §7.4 analysis.

## Objective

SR-016 AC 1 (module contract): a manifest version must be a semantic version, nothing after it.
PRB-028 Investigation: `discovery.py:13,29` uses `^\d+\.\d+\.\d+` with `.match`.

## Implementation detail

`_SEMVER_RE = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?")`
used with `fullmatch` (SemVer 2.0 core with optional pre-release and build). Rejection keeps the
current warning and skip.

## Tests (write first)

`backend/tests/modules/test_discovery.py` (extend): accepted `1.2.3`, `0.1.0-rc.1`, `1.0.0+build.5`;
rejected `1.2.3-evil!`, `1.2.3.4`, `1.2.3 `, `01.2.3`, `1.2`, `v1.2.3`.

## Acceptance criteria

- [ ] SR-016 AC 1: a version with trailing characters is rejected at discovery
      (`backend/tests/modules/test_discovery.py`).

## Verification

```sh
cd backend && uv run pytest tests/modules -v && uv run ruff check . && uv run mypy app
cd backend && uv run pytest modules/dicom_viewer/tests -v     # the bundled module's version still passes
```

## Records

- **TS-010** → 1.2 (`in_review`): TC-010.5 (version fully anchored), `verifies` SR-016.
- **PRB-028**: `## Resolution`, `resolved`.

## Definition of Done

- [ ] Tests pass; TS-010 `in_review`; PRB-028 `resolved`.
- [ ] `traceability-check` shows no error for TASK-200, TS-010, SR-016, PRB-028.
