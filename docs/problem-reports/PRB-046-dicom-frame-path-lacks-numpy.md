---
id: "PRB-046"
type: problem-report
title: "DICOM frame extraction cannot work in the production image: NumPy is not declared"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-22"
updated: "2026-10-22"
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

## Source

Raised by TASK-154, the first SOUP anomaly-list review (CR-001 AC-12, backend slice), on
2026-10-22. The evidence is in SOUP-015's "Anomaly list review" section. Outside CR-001 (A-4).
