---
id: "TASK-223"
type: task
title: "Module boundary test with an allow-list of platform imports"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
links:
  - target: "SR-016"
    relation: implements
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-030"
    relation: relates_to
  - target: "RISK-001"
    relation: relates_to
  - target: "ADD-014"
    relation: relates_to
  - target: "TS-010"
    relation: relates_to
tags: ["cr:CR-006", "verification", "modules"]
---

# TASK-223 — Module boundary test with an allow-list of platform imports

- **Software item / unit:** SI-MODHOST boundary (ADD-014); test only.
- **PRB:** PRB-030. **CR:** CR-006 (verification; no behaviour change).
- **Depends on:** TASK-218 (it edits the DICOM module's imports; run the test on the final shape).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** XS (`backend/tests/modules/test_module_boundary.py`; records TS-010).

## Objective

SR-016 AC 3: a module obtains data only through the platform's authorized interfaces. The boundary test
(`test_module_boundary.py:9-12`) denies only `app.db` and `app.core.object_storage`; any other `app.*` import
passes.

## Implementation detail

- Parse every `.py` under `backend/modules/*/` with `ast`; collect `import app…` / `from app… import` targets
  (including relative-looking and `importlib.import_module("app…")` string literals).
- Allow-list: the platform interfaces the module host publishes (today `app.api.deps` for
  `get_current_user` / `get_platform_services`, `app.api.errors`); anything else fails with the file and line.
  The list lives in the test with a comment pointing to ADD-014.

## Tests (write first)

- `test_modules_import_only_allowed_platform_interfaces` (SR-016 AC 3).
- `test_boundary_check_catches_planted_import` (SR-016 AC 3): a temporary module file importing
  `app.identity.service` makes the check fail.
- TS-010 (1.2 → 1.3, approval cleared) TC-010.x.

## Acceptance criteria

- [ ] SR-016 AC 3: allow-list check green on the code, red on the planted import.

## Definition of Done

- [ ] `uv run pytest tests/modules modules/dicom_viewer/tests` green; `traceability-check` no error for this record

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) for PRB-030.
