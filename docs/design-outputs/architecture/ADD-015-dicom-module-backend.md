---
id: ADD-015
type: architecture-doc
title: DICOM Module (backend) (SI-MOD-DICOM-BE)
status: in_review
version: "1.5"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-11-26"
links:
  - target: SR-016
    relation: implements
  - target: SR-017
    relation: implements
  - target: SR-026
    relation: implements
  - target: RISK-003
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: SR-028
    relation: implements
  - target: SOUP-015
    relation: relates_to
  - target: SOUP-037
    relation: relates_to
tags:
  - software-item:SI-MOD-DICOM-BE
  - class:B
  - layer:backend
---

# ADD-015 — DICOM Module (backend) (SI-MOD-DICOM-BE)

## Responsibility

Authorized DICOM byte/frame endpoints behind the module contract

## Software units (IEC 62304 §5.4.1)

- `U-DICOMBE-Studies` — authorized DICOM byte/frame endpoint via platform services (SR-016, SR-017).
  **CR-006 (D-2; TASK-218, implemented):** before any pixel data is decoded, the unit refuses an object over
  150 MiB stored (checked from the attachment record through `open(..., max_bytes=)`, ADD-012, before
  the store is read) or whose header-declared decoded size (rows × columns × frames × samples ×
  bytes per sample, read with `stop_before_pixels`, SOUP-015) exceeds 1 GiB, with an RFC 7807 problem;
  a decode that fails part-way returns a problem and no image (SR-017 AC 6; SR-026 AC 3; RISK-003,
  RISK-007).
  **CR-008 (TASK-234, TASK-235; implemented).** With `frame=N` the unit checks, in this order and before any
  decode: the frame number (negative: refused); the stored size (as above); the content type (`validate_dicom_content_type`: an attachment whose type is not
  `application/dicom` is refused, with or without `frame`); the transfer syntax, read from
  the file meta information only (group 0002; SOUP-015), against the allow-list below, refusing any other
  UID, or none, with an RFC 7807 400, rule `dicom_transfer_syntax_unsupported`, naming the UID when it is a
  well-formed one; for Deflated Explicit VR Little Endian only, the inflated size, with a bounded
  decompressor, refused above `dicom_max_decoded_bytes` with rule `dicom_decoded_size_exceeded` (a corrupt
  deflate stream is `dicom_decode_failed`; pydicom inflates without a limit); the declared decoded size
  (as above); then the decode with `pixel_array`, whose result must match the header (below) (SR-017 AC 6,
  AC 10; RISK-003, RISK-007). A frame number past the last frame is refused after the decode, when the
  frame count is known to match. Without `frame` it returns the stored object unchanged as
  `application/dicom` for any syntax (AC 8). The platform helper that reads the syntax and bounds the
  inflation is `app.modules.dicom_support` (ADD-014); the frame path and upload validation share it.

  | Supported for `?frame=` (CR-008 D-3 (a)) | UID | Decoded by |
  |---|---|---|
  | Implicit VR Little Endian | `1.2.840.10008.1.2` | pydicom native handler + NumPy |
  | Explicit VR Little Endian | `1.2.840.10008.1.2.1` | pydicom native handler + NumPy |
  | Deflated Explicit VR Little Endian | `1.2.840.10008.1.2.1.99` | bounded inflation (module), then pydicom native handler + NumPy |
  | Explicit VR Big Endian (retired) | `1.2.840.10008.1.2.2` | pydicom native handler + NumPy |
  | RLE Lossless | `1.2.840.10008.1.2.5` | pydicom RLE handler + NumPy |

  All five are lossless. Every other syntax (JPEG Baseline, Extended and Lossless, JPEG-LS, JPEG 2000,
  HTJ2K, MPEG and HEVC video, private or unknown UIDs) is refused on the frame path; no decoder plugin
  is installed.

  **Frame response (CR-008 D-4).** Status 200, `Content-Type: application/octet-stream`: the samples of
  frame N as `pixel_array` returns them, serialised with `ndarray.tobytes()` (C order, no header, no
  padding). Layout: rows × columns × samples per pixel, samples interleaved per pixel whatever the Planar
  Configuration, in the server's native byte order (little-endian on the x86-64 and aarch64 images; the
  array of an Explicit VR Big Endian object is converted to native order before it is written), one sample
  of `ceil(BitsAllocated / 8)` bytes, unsigned when Pixel Representation is 0 and two's-complement signed
  when 1. Samples are served as stored: no rescale, windowing or photometric conversion, so YCbCr
  (YBR_FULL, YBR_FULL_422) stays YCbCr and is not converted to RGB. A YBR_FULL_422 object is upsampled to 3
  interleaved samples per pixel, the Cb and Cr of each pixel pair repeated for both pixels. A decoded array
  whose shape or size does not match the header's Rows, Columns, Samples per Pixel and Number of Frames
  (absent means 1) is refused with `dicom_decode_failed`, never guessed. Data after the last frame, shorter
  than one frame, is ignored (accepted residual, TASK-235 QA: the bytes served are exactly the frame the
  header describes). A negative or out-of-range frame number is refused with a 400 problem. A consumer
  reads Rows, Columns, Samples per Pixel, Bits Allocated, Pixel Representation and Photometric
  Interpretation from the whole object (AC 8). The route's `responses=` documents the same; the module
  router is not part of the core OpenAPI export, so no generated type changes.

  **Upload path (TASK-240, PRB-094).** `U-ATT-Upload` (ADD-012) applies the same bounded inflation to a
  Deflated upload before validation reads it; it applies no syntax allow-list. Accepted residual: a Deflated
  upload (or frame-path object) within the bound is still inflated whole by pydicom, up to about 1 GiB
  (RISK-007; CR-008 Q-2).

  **Installation (CR-008 D-1, D-2; ADR-0024; TASK-233).** The module is the uv workspace member
  `medhub-dicom-viewer` (`backend/modules/dicom_viewer/`), declared by `medhub-backend` and locked in
  `backend/uv.lock`. It declares its own runtime dependencies, `pydicom` (SOUP-015) and `numpy`
  (SOUP-037). The production image installs it non-editable (`uv sync --frozen --no-dev --no-editable`)
  and does not copy its source. Its discovery is checked in the module suite (TS-010 TC-010.8) and in the
  Docker Build job (TS-013 TC-013.15, TASK-236) (SR-017 AC 7, SR-028).

Class B requires decomposition down to software units, not per-unit detailed design
(§5.4.2–5.4.4 are class C). Each unit above is independently unit-testable and is the granularity
at which unit verification records (TS) are written.

## Requirements implemented

Software requirements: SR-016, SR-017 (AC 6 to AC 10); SR-026 (AC 3, added by CR-006); SR-028 (installation from the lock, CR-008).
Non-functional requirements constraining this item: —.

## Interfaces

Provided and consumed interfaces are specified in
[12-interfaces.md](../../design/12-interfaces.md); the runtime interactions this item takes part in
are in [06-runtime-views.md](../../design/06-runtime-views.md) and the sequence diagrams under
[`../../specifications/`](../../specifications/).

## Architecture narrative

This record is a summary and traceability anchor, not the narrative. The design itself is in the
arc42 sections — [05 building blocks](../../design/05-building-blocks.md) for the decomposition,
[04 solution strategy](../../design/04-solution-strategy.md),
[08 cross-cutting concepts](../../design/08-cross-cutting-concepts.md) and, for deployment,
[07 deployment view](../../design/07-deployment-view.md). Governing decisions: [ADR-0001](../../design/adr/), [ADR-0005](../../design/adr/), [ADR-0008](../../design/adr/), [ADR-0024](../../design/adr/0024-backend-modules-installed-as-uv-workspace-members.md) (installation as a workspace member, CR-008).

## Risk relevance

Participates in RISK-003, RISK-007 (see `docs/risks/`); the control measures are carried by the SRs and TASKs listed there. SOUP used: pydicom ([SOUP-015](../../soup/SOUP-015-pydicom.md)) and NumPy ([SOUP-037](../../soup/SOUP-037-numpy.md)).

## Version history

- 1.1 (2026-11-13) — CR-006 Plan stage (Software Architect role): stored and decoded size bounds before decode (SR-017 AC 6) marked "CR-006 (planned)"; `implements` SR-026 added. Content change, so the 1.0 approval record is cleared and the record returns to review.
- 1.2 (2026-11-14) — TASK-225 (Document Writer): the "CR-006 (planned, D-2; TASK-218)" marker is removed; the stored and decoded size bounds are implemented as described (TS-019). Wording only. Content change on an approved record, so the 1.1 approval record is cleared and the record returns to review.
- 1.3 (2026-11-25) — CR-008 Plan stage (Software Architect role): installation as a uv workspace member with module-owned dependencies (ADR-0024), the transfer-syntax allow-list and check order, bounded inflation of Deflated objects, and the `application/octet-stream` frame layout, marked "CR-008 (planned)"; `implements` SR-028 and `relates_to` SOUP-037 added; the "NumPy is not installed" sentence removed. Content change, so the 1.2 approval record is cleared and the record returns to review.
- 1.4 (2026-11-25) — CR-008 TASK-238 (Document Writer): the "CR-008 (planned)" marker is removed; the check order, allow-list, installation and frame layout are described as built. Frame response corrected to the implementation (samples as stored, no YCbCr conversion; YBR_FULL_422 upsampled; interleaved in native byte order; header match check; trailing data; frame range), upload-path inflation (TASK-240) and its residual added. Content change, so the record stays `in_review` for the human's approval.
- 1.5 (2026-11-26) — CR-008 TASK-239 (TASK-238 QA-5): the check order names `validate_dicom_content_type` after the stored size. Wording only. Still `in_review`.
