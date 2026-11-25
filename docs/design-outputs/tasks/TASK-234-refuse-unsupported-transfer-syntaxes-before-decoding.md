---
id: "TASK-234"
type: task
title: "Refuse unsupported transfer syntaxes and bound Deflated inflation before any decode"
status: draft
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-25"
updated: "2026-11-25"
links:
  - target: "SR-017"
    relation: implements
  - target: "RISK-003"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
  - target: "CR-008"
    relation: relates_to
  - target: "PRB-046"
    relation: relates_to
  - target: "PRB-006"
    relation: relates_to
  - target: "TASK-233"
    relation: relates_to
  - target: "ADD-015"
    relation: relates_to
  - target: "SOUP-015"
    relation: relates_to
  - target: "TS-019"
    relation: relates_to
  - target: "TS-010"
    relation: relates_to
  - target: "ADD-014"
    relation: relates_to
  - target: "TASK-240"
    relation: relates_to
tags: ["cr:CR-008", "control:design", "control:protective", "backend"]
---

# TASK-234 — Refuse unsupported transfer syntaxes and bound Deflated inflation before any decode

- **Software items / units:** `U-DICOMBE-Studies` (`backend/modules/dicom_viewer/dicom_viewer/dicom.py`,
  `router.py`; ADD-015); new shared host helper `backend/app/modules/dicom_support.py` (SI-MODHOST,
  ADD-014), also used by TASK-240 for upload validation (CR-008 D-B).
- **PRB:** PRB-046. **CR:** CR-008 (D-3 (a); decision D-A). Keeps PRB-006's bounds (CR-006) intact.
- **Depends on:** TASK-233 (NumPy and pydicom installed for real fixtures).
- **Size:** M (`dicom.py`, `router.py`, new `backend/app/modules/dicom_support.py` with
  `backend/tests/modules/test_dicom_support.py`, `backend/tests/modules/test_module_boundary.py` allow-list,
  new `backend/modules/dicom_viewer/tests/fixtures.py`, new `tests/test_transfer_syntax.py`,
  `tests/test_size_bounds.py` order assertions; records).

## Objective

With `frame=N`, before any data set is parsed or any pixel data decoded:

1. stored size (unchanged, router);
2. **transfer syntax**, read from the file meta information only, must be one of the five UIDs of
   CR-008 D-3 (a) (ADD-015 table); otherwise 400 `application/problem+json`, `errors[0].rule`
   `dicom_transfer_syntax_unsupported`, message naming the UID (`… transfer syntax 1.2.840.10008.1.2.4.50
   is not supported for frame decoding …`), or saying the object declares none; no pixel bytes (SR-017 AC 10);
3. **Deflated only:** inflated size checked with a bounded decompressor; above `dicom_max_decoded_bytes()`
   → the AC 6 problem, rule `dicom_decoded_size_exceeded`; the decompressor never holds more than the
   bound plus one chunk;
4. declared decoded size (unchanged, CR-006);
5. decode.

Without `frame` nothing changes (AC 8). A file with no preamble or unreadable file meta information is
refused with `dicom_transfer_syntax_unsupported` ("declares no transfer syntax"), not guessed.

## Design

**Shared helper (CR-008 D-B).** The two pydicom-facing checks live in the host, not in the module, so that
upload validation (TASK-240) uses the same code: `backend/app/modules/dicom_support.py`, with no FastAPI
or problem types (callers map its exceptions to their own problems):

- `read_transfer_syntax(fp: BinaryIO) -> str | None` — the file-meta read below; leaves `fp` at offset 0;
  `None` when there is no preamble, no readable group 0002 or no (0002,0010).
- `check_inflated_size(fp: BinaryIO, limit: int) -> None` — for a Deflated object, the bounded count
  below, reading `fp` in 64 KiB chunks from the end of group 0002; raises `InflatedSizeExceeded` above
  `limit` and `DeflateStreamError` on a corrupt stream; leaves `fp` at offset 0. Memory: one input chunk
  plus at most `max_length` output bytes per call.

A module may import it only through the module-boundary allow-list: add
`"app.modules.dicom_support": frozenset({"read_transfer_syntax", "check_inflated_size",
"InflatedSizeExceeded", "DeflateStreamError", "DEFLATED_EXPLICIT_VR_LITTLE_ENDIAN"})` to
`ALLOWED_PLATFORM_NAMES` in `backend/tests/modules/test_module_boundary.py` (SR-016 AC 3; ADD-014 is
updated by TASK-238). The module wraps its bytes in `io.BytesIO`.

- `_check_transfer_syntax(data) -> str` (module): `fp = io.BytesIO(data)`;
  `pydicom.filereader.read_preamble(fp, False)` then `pydicom.filereader._read_file_meta_info(fp)`; take
  `TransferSyntaxUID` from that `FileMetaDataset` only — never `Dataset.original_encoding` or anything pydicom
  infers. Constant `SUPPORTED_FRAME_TRANSFER_SYNTAXES` (a `frozenset` of the five UID strings, from
  `pydicom.uid`). The private `_read_file_meta_info` is a deliberate reliance recorded in SOUP-015 1.3;
  a test pins it (below). Alternative if review rejects the private call: parse group 0002 by hand
  (always Explicit VR Little Endian) — more code, no SOUP reliance; ask before switching.
- `_check_inflated_size(data, meta_end)` for `1.2.840.10008.1.2.1.99`: `zlib.decompressobj(-zlib.MAX_WBITS)`
  over `data[meta_end:]`, `decompress(chunk, max_length)` in a loop that counts output bytes, discards
  them and stops as soon as the count exceeds `dicom_max_decoded_bytes()`; a `zlib.error` is
  `dicom_decode_failed`. Only when within the bound does pydicom read the object.
- `stream_dicom` calls them in the order of the Objective; `_check_declared_decoded_size` and the decode
  are unchanged in this task (TASK-235 changes the response).
- `router.py`: the 400 `responses=` description lists rule `dicom_transfer_syntax_unsupported`.

## Steps

Test first: steps 1 and 2 against `HEAD` + TASK-233; the refusal and bomb tests must fail.

1. `tests/fixtures.py`: helpers that build Part-10 objects in memory with pydicom and NumPy
   (`pydicom.Dataset`, `FileMetaDataset`, `dcmwrite(..., enforce_file_format=True)`): given transfer syntax,
   rows, columns, frames, samples per pixel, bits allocated, pixel representation, returns bytes and the
   expected NumPy array. A compressed-syntax object may carry arbitrary pixel bytes (refused from the
   header). A deflate bomb: valid file meta with the Deflated UID followed by a raw-deflate stream of
   zeros that inflates above the configured bound (set `dicom_max_decoded_bytes` low, e.g. 1 MiB, through
   the existing settings fixture, so the test stays small and fast).
2. `backend/tests/modules/test_dicom_support.py` (host unit tests of the helper, on streams): supported,
   unsupported and missing UID; offset restored to 0; a bomb stops within the bound plus one chunk; a
   corrupt stream raises `DeflateStreamError`; a valid deflated object within the bound passes. The
   boundary test (`test_allowed_name_is_defined_in_its_module`) covers the new allow-list entry.
   `tests/test_transfer_syntax.py`:
   - `test_unsupported_transfer_syntax_refused_before_decode` (parametrised: JPEG Baseline
     `1.2.840.10008.1.2.4.50`, JPEG 2000 `1.2.840.10008.1.2.4.90`, HTJ2K `1.2.840.10008.1.2.4.201`, a private
     UID `1.2.3.4`): 400 problem, rule `dicom_transfer_syntax_unsupported`, message contains the UID, body
     not `application/dicom`, `pydicom.dcmread` and `Dataset.pixel_array` never called (spy).
   - `test_missing_transfer_syntax_refused`: file meta without (0002,0010), and bytes with no preamble:
     refused with the rule and "declares no transfer syntax".
   - `test_supported_syntaxes_pass_the_check` (the five UIDs): the check returns the UID (no decode asserted
     here).
   - `test_file_meta_read_does_not_parse_the_data_set`: pins the private-API reliance: for a Deflated
     object, `zlib.decompress` is not called by the transfer-syntax check (spy on `zlib.decompress` and on
     `pydicom.filereader.read_dataset`).
   - `test_deflate_bomb_refused_without_full_inflation`: 400, rule `dicom_decoded_size_exceeded`; the
     counted output stops at most one chunk above the bound; `pydicom.dcmread` never called.
   - `test_corrupt_deflate_stream_is_decode_failed`: 400, rule `dicom_decode_failed`, no image.
   - `test_whole_object_path_unchanged_for_unsupported_syntax`: no `frame` → 200, `application/dicom`, body
     byte-identical (AC 8 guard for this task's change).
3. `tests/test_size_bounds.py`: `test_check_order_stored_then_syntax_then_declared_then_decode`: an object
   that is over the stored bound and unsupported gets `dicom_stored_size_exceeded`; unsupported and over the
   declared bound gets `dicom_transfer_syntax_unsupported`; supported and over the declared bound gets
   `dicom_decoded_size_exceeded`; TC-019.1 to TC-019.4 unchanged and green.
4. Implement (Design). Then the negative controls of Verification.
5. Records (same commit): **TS-019** (approved 1.1 → 1.2, `in_review`, remove the approval record): new
   **TC-019.6** (step 2 refusal, missing-UID and pin tests; SR-017 AC 10), **TC-019.7** (bomb and corrupt
   deflate; SR-017 AC 6), **TC-019.8** (order, step 3; AC 6, AC 10); extend the unit acceptance criteria
   (allow-list from the file meta only; order; bounded inflation; no guessing); version-history line.
   RISK-003 and RISK-007 rows already name these TCs as planned: replace "planned, TASK-234" with the
   executed result in TASK-239, not here.

## Verification

- `cd backend && uv run pytest tests/modules modules/dicom_viewer/tests -q`; whole backend suite as in TASK-233;
  `uv run ruff check . && uv run black --check . && uv run mypy app`.
- Mutation checks, recorded: (a) allow-list replaced by "accept all" → TC-019.6 fails; (b) the Deflated
  bound removed → the bomb test fails (with the low test bound, not an OOM); (c) transfer syntax read
  from `ds.file_meta` after a full `dcmread` → the pin test fails; (d) order swapped (declared size before
  syntax) → the order test fails.
- `git diff --exit-code backend/openapi/openapi.json` after `uv run python -m app.export_openapi --output openapi/openapi.json`
  (the module router is not in the core export; expected no diff).
- `traceability-check` on TASK-234, TS-019, CR-008: 0 errors. `graphify update .`.

## Acceptance criteria

- [ ] Any transfer syntax outside D-3 (a), and a missing one, is refused from the file meta information
  before any parse or decode, naming the UID, with no pixel bytes (SR-017 AC 10; TC-019.6).
- [ ] A Deflated object inflating above the decoded bound is refused without inflating in full, a corrupt
  deflate stream is `dicom_decode_failed` (SR-017 AC 6; TC-019.7).
- [ ] The order stored size → syntax → (inflated size) → declared size → decode is asserted and the
  PRB-006 tests stay green (TC-019.8, TC-019.1 to TC-019.4).

## Definition of Done

- [ ] Tests written first and seen failing; suites, Ruff, Black, mypy green; mutation checks recorded
- [ ] TS-019 updated; `traceability-check` 0 errors; `graphify update .` run

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role). `draft`.
- 1.1 (2026-11-25) — CR-008 D-B (Software Architect role): the transfer-syntax read and the bounded
  inflation move to a shared host helper, `app.modules.dicom_support`, allow-listed for modules, so that
  TASK-240 reuses it for upload validation. Objective and checks unchanged. `draft`.
