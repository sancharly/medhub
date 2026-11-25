---
id: "TASK-234"
type: task
title: "Refuse unsupported transfer syntaxes and bound Deflated inflation before any decode"
status: approved
version: "1.3"
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

- `cd backend && uv run pytest tests/modules -q` and `uv run pytest modules/dicom_viewer/tests -q --import-mode=importlib` (two calls: both conftests are `tests.conftest`, so one call stops at collection; CI runs them separately); whole backend suite as in TASK-233;
  `uv run ruff check . && uv run black --check . && uv run mypy app`.
- Mutation checks, recorded: (a) allow-list replaced by "accept all" → TC-019.6 fails; (b) the Deflated
  bound removed → the bomb test fails (with the low test bound, not an OOM); (c) transfer syntax read
  from `ds.file_meta` after a full `dcmread` → the pin test fails; (d) order swapped (declared size before
  syntax) → the order test fails.
- `git diff --exit-code backend/openapi/openapi.json` after `uv run python -m app.export_openapi --output openapi/openapi.json`
  (the module router is not in the core export; expected no diff).
- `traceability-check` on TASK-234, TS-019, CR-008: 0 errors. `graphify update .`.

## Acceptance criteria

- [x] Any transfer syntax outside D-3 (a), and a missing one, is refused from the file meta information
  before any parse or decode, naming the UID, with no pixel bytes (SR-017 AC 10; TC-019.6).
- [x] A Deflated object inflating above the decoded bound is refused without inflating in full, a corrupt
  deflate stream is `dicom_decode_failed` (SR-017 AC 6; TC-019.7).
- [x] The order stored size → syntax → (inflated size) → declared size → decode is asserted and the
  PRB-006 tests stay green (TC-019.8, TC-019.1 to TC-019.4).

## Definition of Done

- [x] Tests written first and seen failing; suites, Ruff, Black, mypy green; mutation checks recorded
- [x] TS-019 updated; `traceability-check` 0 errors; `graphify update .` run

## Implementation record

Implemented 2026-11-25 (Software Developer role).

- Files: new `backend/app/modules/dicom_support.py` (`read_transfer_syntax`, `check_inflated_size`,
  `InflatedSizeExceeded`, `DeflateStreamError`, `CHUNK_SIZE` 64 KiB; the only place using pydicom's private
  `_read_file_meta_info`); `dicom_viewer/dicom.py` (`SUPPORTED_FRAME_TRANSFER_SYNTAXES`,
  `_check_transfer_syntax`, `_check_inflated_size`, order in `stream_dicom`); `router.py` (400 description);
  `tests/modules/test_module_boundary.py` (allow-list entry); new `fixtures.py`, `test_transfer_syntax.py`,
  `tests/modules/test_dicom_support.py`; `test_size_bounds.py` (order test). TS-019 1.3 (TC-019.6 to TC-019.8).
- Tests first: against `HEAD` `dicom.py` the new module tests fail at import (`SUPPORTED_FRAME_TRANSFER_SYNTAXES`
  missing). Fixtures round-trip through `pydicom.dcmread(...).pixel_array` equal to the expected NumPy array for
  Implicit, Explicit LE, Deflated and Explicit BE (8/16 bit, signed, multi-frame, RGB).
- Mutation checks (module suite, 49 tests): (a) allow-list "accept all": 5 failed (4 refusal cases + order test);
  (b) Deflated bound removed: 2 failed (bomb test, with the 1 MiB bound; corrupt-stream test); (c) syntax read
  from `ds.file_meta` after a full `dcmread`: 8 failed (refusal, missing-syntax, pin, bomb, corrupt);
  (d) declared size before syntax: 8 failed (order test among them). Restored: 49 passed.
- Verification: `pytest modules/dicom_viewer/tests` 49 passed; `pytest tests/modules` 117 passed; whole backend suite
  1763 passed, 10 skipped, coverage 95.22% (gate 85%; `dicom_support.py` 100%); `ruff check .`, `black --check .`,
  `mypy app` clean; OpenAPI export: no diff; `graphify update .` run.
- Deviations: (1) `DEFLATED_EXPLICIT_VR_LITTLE_ENDIAN` is not in the helper nor in the allow-list: the boundary test
  `test_allowed_name_is_defined_in_its_module` reads `obj.__module__`, which a `str` constant does not have, and the
  module can take the UID from `pydicom.uid`. (2) The pin test lets `read_dataset` run once (it is how pydicom
  reads group 0002) and asserts that one call, with `stop_when`, and no `zlib`/`dcmread` use. (3) TS-019 was
  edited concurrently by TASK-237 (1.2, TC-019.12); this task's change is 1.3 on top. (4) The helper re-reads the
  file meta in `check_inflated_size` instead of taking `meta_end`, so both callers pass only a stream and a limit.
  TASK-240 usage: `if read_transfer_syntax(fp) == "1.2.840.10008.1.2.1.99": check_inflated_size(fp, limit)`.

## QA review — round 1 (2026-11-25): CHANGES REQUESTED

Re-run by QA on the working tree of `bug/dicom-module-install` (HEAD 596502f + this task's changes): module suite
(`--import-mode=importlib`) 49 passed; `pytest tests/modules` 117 passed; whole backend suite with coverage 1763 passed,
10 skipped, 95.22% (`dicom_support.py` 100%); `ruff check .` 0, `ruff format --check` (8 changed files) 0,
`black --check .` 0, `mypy app` 0, `mypy modules/dicom_viewer/dicom_viewer` 0; OpenAPI export: no diff;
`traceability-check` (TASK-234, TS-019, CR-008 and linked records; tag `cr:CR-008`): 0 errors. The order of the checks,
the allow-list, the module-boundary entry and the pin test are correct; the findings below are in the bounded inflation,
the file-meta read and the records.

- **R1-1 [CRITICAL] The bounded inflation loops forever on valid Deflated objects** —
  `backend/app/modules/dicom_support.py:79-90`. A Deflated object ends with one pad byte after the raw-deflate stream
  whenever the stream has odd length (DICOM even-length rule; pydicom writes it). When the call that reaches the end of the
  stream is limited by `max_length`, the pad byte stays in `unconsumed_tail` after `eof`: `pending` is never empty, `out`
  is always `b""`, and `while pending or not decompressor.eof` never ends. QA: 40 valid 256 x 256 Deflated objects built
  with the fixtures: 22 hang (all with a pad byte), 18 pass. Through the router (`?frame=0`, default 1 GiB bound) the
  request never returns; the sync handler spins one threadpool thread at 100 % CPU for ever. Any user who can upload a
  Deflated study can take the API down a thread at a time, and about half of the legitimate Deflated studies can never
  be opened (the RISK-007 harm, introduced by its own control). TASK-240 would inherit it on the upload path. The tests
  miss it because every valid Deflated fixture inflates to less than one 64 KiB chunk, and `generate_uid()` makes the
  encoded length, and so the pad byte, random. → Stop as soon as the stream ends, e.g.
  `if decompressor.eof or (not out and not pending): break` (QA candidate: 40/40 pass, both suites green). Add
  deterministic tests (fixed SOP Instance UID in the fixtures) of valid Deflated objects that inflate to more than one
  chunk, with and without the trailing pad byte: in `test_dicom_support.py` (`check_inflated_size` returns) and on the
  frame path in `test_transfer_syntax.py` (200 and the expected frame; RISK-007 row "a valid deflated object decodes").
- **R1-2 [HIGH] A malformed (0002,0010) gives a 500, not a refusal** — `backend/app/modules/dicom_support.py:59`.
  `meta.get("TransferSyntaxUID")` converts the raw element outside the `try` of `_read_file_meta`, so an unknown VR
  (`ZZ`) raises `NotImplementedError` and a wrong-length VR (`UV`) raises `BytesLengthException`. Both escape
  `_check_transfer_syntax`; the router answers 500 `internal-error`. QA: bytes `preamble + DICM + (0002,0010) VR "ZZ"`
  → 500 through the router; on `HEAD` the same bytes gave 400 `dicom_decode_failed`, so this is a regression. 39 of
  4500 random single-byte mutations of group 0002 hit it. Breaks SR-017 AC 10 ("no 5xx for a decode problem") and the
  task's "unreadable file meta information is refused". → Treat any failure to read or convert the element as "none
  declared" (do the `get` and `str()` inside the guarded block); add the `ZZ` and `UV` cases to
  `test_missing_syntax_preamble_or_file_meta_is_none` and to `test_missing_transfer_syntax_refused`.
- **R1-3 [MEDIUM] The declared UID is echoed without a bound** — `backend/modules/dicom_viewer/dicom_viewer/dicom.py:62-65`.
  The message (problem `detail` and `errors[0].message`) carries whatever group 0002 holds: QA's 4 MiB `OB` value gave an
  8 MiB problem response; non-printable bytes and a `b'1.2\x00'` repr are reflected too. → Name the UID only when it is a
  valid UID (at most 64 characters of digits and dots); otherwise say the object declares an invalid transfer syntax UID,
  with the same rule. Test both.
- **R1-4 [MEDIUM] TS-019 1.3 Scope and Preconditions are stale** —
  `docs/design-outputs/tests-specifications/TS-019-dicom-image-opening-and-rendering.md` (Scope, Preconditions and
  environment, Verification results). Preconditions still say branch `fix/review-2026-07-reliability`, "NumPy is not
  installed in any environment" and `pixel_array` is a stub, while TC-019.6 to TC-019.8 use real NumPy fixtures
  (`fixtures.py`, TASK-233); Verification results point only at TASK-218. Raised by the TASK-237 QA too, for TC-019.12:
  Scope and Preconditions must also name SR-017 AC 11, SI-FE-CORE `AttachmentItem` and the frontend environment (Node 24,
  `frontend/package-lock.json`, Vitest with MSW), and the TC-019.12 row must name the two `ClinicalEntriesPage.test.tsx`
  tests instead of "(two DICOM cases)". → Update those sections; add the R1-1 and R1-2 cases to TC-019.6 and TC-019.7.
- **R1-5 [LOW] TASK-240 still imports a name the helper does not define** —
  `docs/design-outputs/tasks/TASK-240-bound-deflated-inflation-in-dicom-upload-validation.md` step 2
  (`DEFLATED_EXPLICIT_VR_LITTLE_ENDIAN` from `app.modules.dicom_support`). Deviation 1 is right for the module: the
  allow-list entry is exactly the four names the module imports, and `test_allowed_name_is_defined_in_its_module` cannot
  hold a `str` (no `__module__`). But host code is not boundary-checked, so the reason does not apply to TASK-240. →
  Software Architect: revise TASK-240 to take the UID from `pydicom.uid`, or have the helper define the constant without
  allow-listing it. Otherwise the helper API (`read_transfer_syntax(fp)`, `check_inflated_size(fp, limit)`, two
  exceptions, `fp` left at 0) fits TASK-240 steps 1-2.
- **R1-6 [LOW] No test bounds the input read** — `backend/app/modules/dicom_support.py:81`. Mutant
  `chunk = fp.read()` (whole remaining input at once) survives both suites. Harmless on the frame path (the bytes are
  already in memory) but TASK-240 may pass a spooled upload stream. → In `test_bomb_stops_within_the_bound_plus_one_chunk`,
  spy on `fp.read` and assert every read is at most `CHUNK_SIZE`.
- **R1-7 [LOW] Verification command does not run as written** — this task, Verification bullet 1:
  `pytest tests/modules modules/dicom_viewer/tests` in one call stops at collection with pluggy "Plugin already
  registered" (both conftests are `tests.conftest`). It happens on `HEAD` too and CI runs the two suites in separate steps
  (`ci.yml` lines 110 and 116), so it is not a code defect. → Write it as two invocations.

QA mutations (scratch copy, module suite / host helper tests; the 1 module failure always present there is the
installed-distribution guard): (a) allow-list accepts everything: 6 / 0 failed; (b) Deflated check call removed: 3 / 0;
helper bound removed: hangs (R1-1); `max_length` dropped: 2 / 1; whole input read at once: 0 / 0 (R1-6); helper reads the
syntax from a full `dcmread`: 9 / 3; from `dcmread(stop_before_pixels=True)`: 9 / 0 (the pin is in the module suite, which
CI runs); declared size before syntax: 9 / 0; inflated size after declared size: 3 / 0.

Risk controls: RISK-003 (allow-list before decode) is implemented and tested, except R1-2. RISK-007 (bounded inflation)
bounds bombs as claimed, but R1-1 makes the control itself a cause of unavailability; it is not effective until fixed.

## Implementation record, round 2 (2026-11-25)

Software Developer role, after QA round 1 (R1-5 is left to the Software Architect, TASK-240).

- **R1-1:** `check_inflated_size` now ends when the deflate stream ends (`decompressor.eof`), so the pad byte left in
  `unconsumed_tail` no longer keeps it looping. QA scenario (40 valid 256-wide Deflated objects, columns 256 to 295,
  2 s alarm each): 25 without and 15 with a pad byte, 0 hangs. Fixtures use a fixed SOP Instance UID (reproducible
  length); `build_large_deflated(pad_byte=...)` searches the width for the wanted parity. New tests, which run in a
  thread with a join timeout (no pytest-timeout dependency added; the spinning call is interrupted with an
  asynchronous exception so it does not starve the run): host `test_valid_object_inflating_over_one_chunk_returns`
  (both parities, exact bound, bound - 1) and module `test_valid_deflated_object_over_one_chunk_returns_its_frame`
  (both parities; calls `stream_dicom`, which the router calls, because the HTTP client's worker thread cannot be
  interrupted on a hang).
- **R1-2:** `read_transfer_syntax` converts the element inside its guard; any failure is "none declared". `ZZ` and
  `UV` cases added to `test_missing_syntax_preamble_or_file_meta_is_none` and `test_missing_transfer_syntax_refused`
  (the latter through the router: 400, not 500).
- **R1-3:** `_check_transfer_syntax` names the UID only if it is at most 64 characters of digits and dots, else
  "The DICOM transfer syntax UID is invalid ..." (same rule). `test_invalid_transfer_syntax_uid_is_not_echoed`: 4 MiB
  `OB` value, non-printable bytes, a 65-character UID; the response is under 2 KiB and does not contain the value.
- **R1-4:** TS-019 1.4 (see its history). **R1-6:** the bomb test uses a bomb with a 256 KiB incompressible prefix (so the
  input is longer than a chunk) and a `BytesIO` subclass that records each `read`; each is at most `CHUNK_SIZE`.
  **R1-7:** the verification command above is two calls.
- Verification: module suite 52 passed; `tests/modules` 119 passed; whole backend suite 1765 passed, 10 skipped,
  coverage 95.22% (`dicom_support.py` 100%); `ruff check .`, `black --check .` (295 files), `mypy app` and
  `mypy modules/dicom_viewer/dicom_viewer` clean; OpenAPI export: no diff; `graphify update .` run.
- Mutations: (a) allow-list accepts everything: 6 failed (module suite), 0 host. Helper bound removed: 1 module
  (`test_deflate_bomb_refused_without_full_inflation`) and 4 host (`test_the_bound_is_exact`, both valid-object
  tests, the bomb test) failed. Loop fix reverted: host `[pad_byte]` fails by timeout (1 failed, 12 passed, 10.8 s),
  module `[pad_byte]` fails by timeout (1 failed, 51 passed, 15 s). Unbounded `fp.read()`: host bomb test fails
  (the module suite cannot see it). ZZ/UV guard reverted: 1 module and 1 host failed.

## QA review — round 2 (2026-11-25): APPROVED

Re-run by QA on the working tree of `bug/dicom-module-install`: module suite (`--import-mode=importlib`) 52 passed;
`pytest tests/modules` 119 passed; whole backend suite with coverage 1765 passed, 10 skipped, 95.22%
(`dicom_support.py` 100%); `ruff check .` 0; `ruff format --check` (8 changed files) 0; `black --check .` 0;
`mypy app` 0; `mypy modules/dicom_viewer/dicom_viewer` 0; OpenAPI export: no diff; `traceability-check`
(TASK-234, TS-019, CR-008 and linked records; tag `cr:CR-008`): 0 errors.

- **R1-1 fixed.** QA's 40-object scenario (varied SOP Instance UIDs): 24 with and 16 without a pad byte, 0 hangs. Router
  probe with a pad-byte Deflated object (`?frame=0`, default 1 GiB bound): 200. Loop fix reverted in a scratch copy:
  the host and module `[pad_byte]` tests fail by timeout (about 10 s each) and the run ends normally.
- **Hang-safe tests.** `fixtures.call_with_timeout` joins the thread with a timeout, calls `pytest.fail`, and sends
  `TimeoutError` to the thread with `PyThreadState_SetAsyncExc`. QA probe: a spinning thread is gone 0.5 s after the
  timeout (active threads back to 1). The CPython API and the `c_ulong` thread id are the same on Linux / 3.12. The
  failure is not hidden, because `pytest.fail` runs whether or not the interrupt lands. Nothing leaks: the interrupted
  thread only records the exception and ends.
- **Deviation 1 accepted.** The frame-path pad-byte test calls `stream_dicom`, the function the router calls with the
  stored bytes. Together with the router-level tests of the refusals and QA's router probe (200), this is sufficient
  evidence. A router-level hang test could not be interrupted (the TestClient worker thread) and would stall CI.
- **R1-2 fixed.** Fuzz of group 0002 (3000 Explicit VR LE and 1500 Deflated single-byte mutants plus 10 hand cases):
  0 non-problem exceptions. Router probe with VR `ZZ`: 400 `dicom_transfer_syntax_unsupported`.
- **R1-3 fixed.** A UID is named only when it is at most 64 characters of digits and dots (`fullmatch`); otherwise
  "transfer syntax UID is invalid", with the same rule. QA's 4 MiB `OB` probe: 407-byte response.
- **R1-4 fixed.** TS-019 1.4 Scope, Preconditions and Verification results are current. The two
  `ClinicalEntriesPage.test.tsx` names match the file (lines 277 and 320). NumPy 2.5.5 matches SOUP-037.
- **R1-6 fixed.** Mutant `fp.read()` now fails the host bomb test. **R1-7 fixed.** QA removed a stray backtick in the
  Verification bullet (record-only edit).
- **R1-5** stays with TASK-240 (orchestrator), as directed. It does not block this task.

QA mutations (scratch copy; module / host failures, excluding the installed-distribution guard): R1-1 reverted 1 / 1
(timeout); R1-2 reverted 1 / 1; UID echo unguarded 1 / 0; length check removed 1 / 0; whole input read 0 / 1; allow-list
accepts everything 6 / 0; Deflated check call removed 2 / 0.

Risk controls: RISK-003 (allow-list from the file meta only, before any decode) and RISK-007 (bounded inflation,
which now terminates on valid objects) are implemented and verified by TC-019.6 to TC-019.8.

Observations (not blocking): pydicom's own `warn_and_log` writes an invalid UI value (up to 64 KiB) to the log. This
is SOUP behaviour, not changed here. The TS-019 unit-acceptance paragraph could also state the end-of-stream and
UID-echo rules; the TC rows already do.

## Version history

- 1.0 (2026-11-25) — Created at the CR-008 Plan stage (Software Architect role). `draft`.
- 1.1 (2026-11-25) — CR-008 D-B (Software Architect role): the transfer-syntax read and the bounded
  inflation move to a shared host helper, `app.modules.dicom_support`, allow-listed for modules, so that
  TASK-240 reuses it for upload validation. Objective and checks unchanged. `draft`.
- 1.2 (2026-11-25) — Implemented (Software Developer role). `in_review`.
- 1.2 (2026-11-25, QA) — Round 1 CHANGES REQUESTED (R1-1 CRITICAL, R1-2 HIGH, R1-3 and R1-4 MEDIUM, R1-5 to R1-7 LOW). Status `draft`.
- 1.3 (2026-11-25) — QA round 1 fixes (R1-1 to R1-4, R1-6, R1-7); R1-5 left to the Software Architect. `in_review`.
- 1.3 (2026-11-25, QA) — Round 2 APPROVED; R1-1 to R1-4, R1-6 and R1-7 fixed; R1-5 carried to TASK-240. Status `approved`.
