---
id: "TASK-218"
type: task
title: "DICOM stored-size and decoded-size bounds before any pixel decode"
status: approved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
links:
  - target: "SR-017"
    relation: implements
  - target: "SR-026"
    relation: implements
  - target: "RISK-003"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-006"
    relation: relates_to
  - target: "PRB-006"
    relation: relates_to
  - target: "ADD-015"
    relation: relates_to
  - target: "SOUP-015"
    relation: relates_to
  - target: "TASK-217"
    relation: relates_to
tags: ["cr:CR-006", "dicom", "control:protective"]
---

# TASK-218 — DICOM stored-size and decoded-size bounds before any pixel decode

- **Software item / unit:** SI-MOD-DICOM-BE (ADD-015): `dicom_viewer/dicom.py`, `dicom_viewer/router.py`.
- **PRB:** PRB-006. **CR:** CR-006 (D-2: 150 MiB stored, 1 GiB decoded; separate task, not TASK-135).
- **Depends on:** TASK-217 (`AttachmentService.open(..., max_bytes=)`).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** S (`backend/modules/dicom_viewer/dicom_viewer/dicom.py`, `router.py`; tests
  `backend/modules/dicom_viewer/tests/`; records TS-019 new, ADD-015, SOUP-015 relied-on text).

## Objective

SR-017 AC 6: before decoding any pixel data the module refuses an object over 150 MiB stored or whose
declared decoded size (rows × columns × frames × samples per pixel × bytes per sample) exceeds 1 GiB, with an
RFC 7807 error; a decode that fails part-way returns an error and no image. Today `stream_dicom` calls
`dcmread` and `pixel_array` on the whole object with no bound (`dicom.py:27-28`).

## Implementation detail

- Settings `dicom_max_stored_bytes` (157286400) and `dicom_max_decoded_bytes` (1073741824), read from the
  platform settings; no new environment variable unless the module already has a settings pattern.
- Router: `services.attachments.open(actor, id, max_bytes=dicom_max_stored_bytes)` (TASK-217): the stored
  bound is checked from the attachment record before any read.
- `stream_dicom(data, frame)`: when `frame` is given, first `dcmread(BytesIO(data), stop_before_pixels=True)`;
  compute the declared size from `Rows`, `Columns`, `NumberOfFrames` (default 1), `SamplesPerPixel`
  (default 1), `BitsAllocated` (rounded up to bytes); a missing or non-positive attribute is refused (no
  guess). Over the bound → a problem naming the limit (`dicom_decoded_size_exceeded`). Only then the full
  read and `pixel_array`, inside `try`: any exception → a problem (`dicom_decode_failed`), never partial
  bytes.
- The problem types are documented in the module's router `responses=` (the module router is not in the
  core OpenAPI export; confirm, and if it is, regenerate as an "ask first" contract change).
- **NumPy is not installed** in any environment (SOUP-015 review, PRB-048), so `pixel_array` always fails
  today; this task must not add NumPy (new SOUP, "ask first"). The decode path is tested with `pixel_array`
  stubbed; the real render stays with PRB-048 (finding P-6).

## Tests (write first)

- `test_stored_size_over_bound_refused_before_read` (SR-017 AC 6): attachment record of 150 MiB + 1;
  problem response; the store is not read.
- `test_declared_decoded_size_over_bound_refused_with_small_stored_bytes` (SR-017 AC 6): a small synthetic
  dataset whose header declares 1 GiB + 1; problem; `pixel_array` never called.
- `test_truncated_pixel_stream_gives_error_and_no_image` (SR-017 AC 6): stubbed decode raises; problem
  response, empty body.
- `test_reference_study_at_bounds_not_refused` (SR-017 AC 6, SR-026 AC 3): a 150 MiB stored object whose
  header declares ≤ 1 GiB passes both checks (decode stubbed).
- Recorded in a new TS-019 "DICOM image opening and rendering verification" (`verifies` SR-017), TC-019.1
  to TC-019.4. No TS verifies SR-017 today.

## Acceptance criteria

- [x] SR-017 AC 6: both bounds checked before decode; errors are RFC 7807; no partial image.
- [x] Bounds are exactly 150 MiB and 1 GiB (D-2).
- [x] No new dependency.

## Definition of Done

- [x] `uv run pytest modules/dicom_viewer/tests`, backend suite, `ruff`, `mypy` green
- [x] TS-019 created (`draft` → `in_review` at handoff); ADD-015 consistent; SOUP-015 relied-on text names the
  header-only read on the module path
- [x] `traceability-check` no error for this record

## Implementation record (Software Developer, 2026-11-13)

### Changes

- `backend/app/core/config.py`: settings `dicom_max_stored_bytes` = 157286400 and
  `dicom_max_decoded_bytes` = 1073741824. `infra/.env.example`: `DICOM_MAX_STORED_BYTES`,
  `DICOM_MAX_DECODED_BYTES` (required by `tests/test_env_example.py`, which caught the omission).
- `backend/modules/dicom_viewer/dicom_viewer/router.py`: `attachments.open(actor, id, max_bytes=
  get_settings().dicom_max_stored_bytes)`; the 400 problem documented in the route's `responses=`.
- `backend/modules/dicom_viewer/dicom_viewer/dicom.py`: `_check_declared_decoded_size` (header read with
  `stop_before_pixels=True`; `Rows`, `Columns`, `NumberOfFrames` default 1, `SamplesPerPixel` default 1,
  `BitsAllocated` rounded up to bytes; missing, non-numeric or non-positive refused) runs before the full
  read; the full read and `pixel_array` are inside a `try` and any exception is a problem.
- `backend/modules/dicom_viewer/tests/test_size_bounds.py` (new, 6 tests); `docs/.../TS-019` (new).
- Problem types reused: the existing 400 `validation-error` (`ValidationProblem`); the limit is named in the
  detail and the `errors[].rule` is `dicom_decoded_size_exceeded` or `dicom_decode_failed`. The stored
  refusal is `AttachmentService.open`'s existing 400. No new problem type, no new dependency, no NumPy.
- OpenAPI: the module router is not in the core export; `export_openapi` output is byte-identical to the
  committed `openapi.json`, so no contract regeneration.
- Module boundary: the module now imports `app.core.config` (allowed by
  `backend/tests/modules/test_module_boundary.py`, which forbids only `app.db` and
  `app.core.object_storage`); TASK-223 must allow or replace this when it tightens the rule.

### Acceptance criteria

- SR-017 AC 6: stored bound checked from the record before any read (TC-019.1); declared decoded bound
  checked before `pixel_array` (TC-019.2); RFC 7807 responses; a failing decode returns a problem and no
  bytes (TC-019.3); an object at both bounds is not refused (TC-019.4; SR-026 AC 3 context only).
- Bounds are exactly 150 MiB and 1 GiB. No new dependency.

### Verification

- `uv run pytest -q modules/dicom_viewer/tests`: 31 passed (25 existing + 6 new).
- Negative controls: removing `max_bytes=` from the router fails `test_stored_size_over_bound_refused_before_read`;
  removing the `_check_declared_decoded_size` call fails the three TC-019.2 tests. Both restored.
- `uv run pytest -q` (backend): see Report below; `ruff check`, `ruff format --check`, `mypy app` clean.

### Open points for QA and the human

- **SOUP-015 relied-on text** (approved record, not edited): add that the module path reads the header
  without pixel data (`dcmread(..., stop_before_pixels=True)`) to refuse an over-size object. Needs the
  human's permission to edit. **ADD-015** (approved) still says "CR-006 (planned, D-2; TASK-218)"; its
  wording can become "implemented" at the human's approval. RISK-003 / RISK-007 rows keep "none yet" until
  TS-019 is approved.
- A real render and the 10-second SR-026 AC 3 budget are not verified: NumPy is absent (PRB-048, P-6).
- `BitsAllocated` = 1 is rounded up to 1 byte per pixel (conservative; over-estimates packed bitmaps).
- An unparsable header or a body that is not DICOM reports `dicom_decode_failed` (400), not a separate type.

## QA review (qa-engineer, 2026-11-13) — CHANGES REQUESTED

Run by QA: backend `uv run pytest -q` 1622 passed, 10 skipped, 0 failed; `uv run pytest modules/dicom_viewer/tests`
31 passed; `ruff check`, `ruff format --check` (app, modules), `mypy app` clean; OpenAPI export byte-identical;
**`python3 -m unittest discover -s infra/tests`: 178 run, 1 FAILED**; `traceability-check` (fallback) on CR-006,
TASK-218, TS-019, PRB-006, SOUP-015 and neighbours (71 records): 0 errors (W1 SR-026; W5 approved records →
`in_review` SOUP/TS records).

1. **[HIGH] The new settings are not wired into Compose; `infra/tests` fails (CI red).**
   `test_compose_settings_coverage.SettingsReachTheServices.test_every_setting_is_in_some_python_service_or_excepted`:
   "in no Python service's environment: ['DICOM_MAX_DECODED_BYTES', 'DICOM_MAX_STORED_BYTES']". In the
   deployed stack the values can then not be set from `infra/.env`, although `.env.example` documents them.
   → As for `ATTACHMENT_MAX_BYTES` in TASK-135: add `DICOM_MAX_STORED_BYTES: ${DICOM_MAX_STORED_BYTES:-157286400}`
   and `DICOM_MAX_DECODED_BYTES: ${DICOM_MAX_DECODED_BYTES:-1073741824}` to the `backend` service's
   `environment:` in `infra/docker-compose.yml` (the only service that runs the module router), and run
   `infra/tests` before handoff (add it to this task's verification list).
2. **[LOW] The stored-size refusal has no `errors[].rule`, unlike the two decode refusals.** It is
   `AttachmentService.open`'s plain `ValidationProblem`; a client cannot tell it from other 400s except by
   the detail. → Optional: `errors=[ProblemDetail(field="study", rule="dicom_stored_size_exceeded", ...)]`
   in `open(max_bytes=)` (or in the router), and TC-019.1 asserting the rule.

Assessed, no change needed: SR-017 AC 6 is met. Both bounds are checked before any pixel decode (the
stored one from the record before any store read, the declared one from a `stop_before_pixels` header read
before `pixel_array`), and a failed decode returns a problem and no image. The raw path (`frame` absent)
decodes nothing, so the decoded bound does not apply to it, and no frontend calls the route. Reusing the
400 `validation-error` type with a rule satisfies SR-017's "RFC 7807 error" and keeps one problem type for
the client. `BitsAllocated` = 1 counted as 1 byte over-estimates packed bitmaps by 8×, which is the safe
direction. The stored bound equals `attachment_max_bytes` today but is not redundant: it guards objects
stored before CR-006 and is a separate setting for the module path, which holds the whole object in memory.
That is fine. The module importing `app.core.config` is allowed by today's boundary test; it is TASK-223's
to allow or replace. TS-019 states honestly that the decode is stubbed and that a real render and the
SR-026 AC 3 budget are not verified (PRB-048). SOUP-015 1.2's relied-on text matches the code
(`dcmread(..., stop_before_pixels=True)`, the five attributes, refusal before pixel data); it needs the
human's approval.

For TASK-225 (approved records, not edited): ADD-015 "CR-006 (planned, D-2; TASK-218)" → implemented;
RISK-003 and RISK-007 DICOM-bounds rows → verification "TS-019 TC-019.1–4" (and the stored-size rule, if
finding 2 is taken).

## Round 2 (Software Developer, 2026-11-13)

- HIGH: `infra/docker-compose.yml` `backend` service now sets `DICOM_MAX_STORED_BYTES` and
  `DICOM_MAX_DECODED_BYTES` with the defaults 157286400 and 1073741824, next to `ATTACHMENT_MAX_BYTES`. The
  worker does not use the DICOM settings, so it is unchanged.
- LOW: the router turns `open()`'s size refusal into the same 400 problem with `errors[0].rule`
  `dicom_stored_size_exceeded` (documented in `responses=`); `test_stored_size_over_bound_refused_before_read`
  asserts it; TS-019 TC-019.1 text updated.
- Verified: `python3 -m unittest discover -s infra/tests` 178 OK; backend 1622 passed, 10 skipped;
  `modules/dicom_viewer/tests` 31 passed; ruff and mypy clean.

## QA review round 2 (qa-engineer, 2026-11-13) — APPROVED

Run by QA: backend `uv run pytest -q` 1622 passed, 10 skipped, 0 failed; `uv run pytest modules/dicom_viewer/tests`
31 passed; `infra/tests` 178 OK; `ruff check`, `ruff format --check` (app, modules), `mypy app` clean; OpenAPI
export byte-identical; `traceability-check` (fallback, 71 records) 0 errors. Finding 1 closed: `backend` sets
both settings with defaults next to `ATTACHMENT_MAX_BYTES`. The Celery services do not import the DICOM module
(`backend/app/workers/`) and the settings have defaults, so they need neither. Finding 2 closed: the router maps
`open()`'s `ValidationProblem` to rule `dicom_stored_size_exceeded`. `AttachmentIntegrityError` and
`NotFoundError` are not `ValidationProblem` subclasses, so the 502 and 404 paths are unchanged. TC-019.1
asserts the rule. The "ADD-015 consistent" box is ticked on the understanding that the wording change from
"planned" to "implemented" is TASK-225's. PRB-006 `investigating → resolved`.

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect) for PRB-006 (D-2).
- 1.1 (2026-11-13) — Implemented and verified in the working tree (Software Developer); TS-019 created. `draft → in_review`.
- 1.2 (2026-11-13) — QA review: CHANGES REQUESTED (1 HIGH: Compose wiring, `infra/tests` red; 1 LOW); `in_review → draft`.
- 1.3 (2026-11-13) — Round 2 (Software Developer): see "Round 2". `draft → in_review`.
- 1.4 (2026-11-13) — QA review round 2: APPROVED; checkboxes ticked; `in_review → approved`.
