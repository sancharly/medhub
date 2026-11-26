---
id: "PRB-046"
type: problem-report
title: "DICOM frame extraction cannot work in the production image: NumPy is not declared"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-11-26"
criticality: minor
links: []
tags: ["soup", "configuration-management", "dicom"]
---

# PRB-046 — DICOM frame extraction cannot work in the production image: NumPy is not declared

## Observed

- `GET /studies/{id}?frame=N` calls `stream_dicom`. At
  `backend/modules/dicom_viewer/dicom_viewer/dicom.py:28` that function reads `ds.pixel_array`
  from pydicom 3.0.2 ([SOUP-015](../soup/SOUP-015-pydicom.md)).
- pydicom's published installation and pixel-data guides say NumPy is required to manipulate
  pixel data, and they list it as optional. Compressed transfer syntaxes (JPEG, JPEG-LS,
  JPEG 2000) also need a decoder plugin (Pillow, pylibjpeg or GDCM).
- pydicom 3.0.2 declares no runtime dependencies in `backend/uv.lock`. Neither
  `backend/pyproject.toml` nor the `dicom_viewer` module declares NumPy or a decoder plugin.
- The production image is built with `uv sync --frozen --no-dev`, so it contains no NumPy. Once
  the frame path is reachable, it cannot succeed there.
- **Today the path is not reachable at all.** The `dicom_viewer` module is installed in no
  environment, so its router is never mounted and `GET /studies/{id}?frame=N` returns 404
  ([PRB-048](PRB-048-dicom-viewer-module-not-installed.md), found by the QA review of TASK-154).
  This report describes the defect that will surface once PRB-048 is resolved.
- The unit tests mock `stream_dicom` and put the module on `sys.path` themselves, so the suite
  shows neither defect. The frontend does not
  request `?frame=` (checked 2026-10-22).
- These findings come from the lock file and the published documentation. Nothing was executed,
  because the review rules forbid running the dependency.

## Impact

The per-frame pixel access that SR-017 relies on SOUP-015 for cannot work in a real deployment.
Today the request gets a 404 because the module is not installed (PRB-048). Once it is installed,
the request will fail with a server error and return no image. Once the module is installed, the
endpoint without `?frame=` returns the stored DICOM unchanged. The frontend calls neither: its
"view" link uses the core `/attachments/{id}` URL (`AttachmentItem.tsx:32-34`,
`frontend/src/api/client.ts:166-167`) and is hidden today (PRB-048). Upload validation
(`backend/app/attachments/dicom_validation.py`, `stop_before_pixels=True`) needs no NumPy and is
unaffected.

## Safety evaluation

The failure is loud. No wrong or partially decoded image is shown, so no new hazardous situation
arises under RISK-003. That is the same path, and the same "fails loudly" protective control,
that PRB-006 relies on (SR-031, TASK-135), so RISK-003 is not re-scored. Without the frame
endpoint, per-frame access is unavailable. The full study can still be downloaded through the
core attachment endpoint (RISK-007 at most). No
data integrity, misattribution or clinical decision is affected, so the criticality is `minor`.

Released versions (§9.3): no `release` record exists (`docs/releases/` is absent), so no released
version in use is affected and no notification is needed.

## Proposed resolution

In a separate CR, planned together with PRB-048 (install the module) and PRB-006 (the decode
bound on the same path):

- Declare NumPy as a runtime dependency.
- Decide which transfer syntaxes the frame path supports. Either declare the decoder plugins they
  need (each a new SOUP record), or reject unsupported syntaxes with a clear error.
- Add a test that runs the real `stream_dicom` on uncompressed and, if supported, compressed
  fixtures, plus a production-image import check like TS-013 TC-013.8.
- Update SOUP-015 and add SOUP records for the new items.

## Resolution

Resolved in CR-008 (the `resolves` link is on CR-008), verified in the working tree on 2026-11-26 (TASK-239, branch `bug/dicom-module-install`, head 5bd10e7 plus the task's working-tree changes).

What changed:
- **TASK-233**: NumPy 2.5.5 is a declared runtime dependency of the module and is in the lock and the image (SOUP-037); the real decode runs in the module suite and in the image.
- **TASK-234** (D-3 (a), SR-017 AC 10): the frame path reads the transfer syntax from the file meta information and serves only Implicit and Explicit VR Little Endian, Deflated Explicit VR Little Endian, Explicit VR Big Endian and RLE Lossless; any other UID, or none, is refused with a 400 `dicom_transfer_syntax_unsupported` before any decode; Deflated objects are inflated with a bounded decompressor (`backend/app/modules/dicom_support.py`).
- **TASK-235** (D-4, SR-017 AC 9): a frame is returned as `application/octet-stream` in the documented ADD-015 layout; the whole object stays `application/dicom` and byte-identical.
- **TASK-238**: documentation of the supported syntaxes and layout.

Verification (2026-11-26):
- Module suite 84 passed (TS-019 TC-019.6 to TC-019.11 and TC-019.13: real decodes of generated objects compared with the known values, five syntaxes, single and multi frame, 8-bit, signed 16-bit and RGB; trailing bytes under one frame ignored, a whole extra frame refused).
- Negative control: with the allow-list removed the TC-019.6 tests fail (rule `dicom_decode_failed` instead of `dicom_transfer_syntax_unsupported`); restored, they pass.
- Started stack (TS-019 TC-019.5, backend frame part): a 4-frame 16-bit uncompressed object uploaded by a doctor; `GET .../studies/{id}` answered 200 `application/dicom` with a SHA-256 equal to the upload; `?frame=0` and `?frame=3` answered 200 `application/octet-stream` with bytes equal to the known values (78 ms and 16 ms); `?frame=4` answered 400 "Frame 4 out of range; this DICOM has 4 frames."; a JPEG Baseline object with `?frame=0` answered 400 `dicom_transfer_syntax_unsupported`, and its whole-object GET returned the stored bytes. The "first rendered image within 10 s" part of TC-019.5 stays deferred to #29 (SR-026 AC 3).
- Hosted CI: the Docker Build job (including the TASK-236 image check) and the full workflow run only after the human approves a push; their result is verified on hosted CI after push and is not claimed here.

## Source

Raised by TASK-154, the first SOUP anomaly-list review (CR-001 AC-12, backend slice), on
2026-10-22. The evidence is in SOUP-015's "Anomaly list review" section. Outside CR-001 (A-4).

## Note (2026-11-15, CR-006 TASK-226)

SR-026 AC 3 (the first rendered DICOM image within 10 s) is not verified by CR-006 and stays unverified until this problem report and PRB-048 are both resolved: on a started stack the viewer route is not mounted and the decode cannot run (TS-018 TC-018.11, TS-019 TC-019.5). CR-006 verifies the stored and decoded size bounds only (TASK-218, TS-019 TC-019.1 to TC-019.4); the deferral follows D-20 and is for the human to confirm.

## Version history

- 1.2 (2026-11-26) — Resolved (TASK-239, CR-008): fix and verification recorded in "Resolution". The human closes the PRB in MedTrace after the merge.
