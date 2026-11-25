---
id: SOUP-037
type: soup
title: NumPy
status: in_review
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-11-25"
updated: "2026-11-25"
manufacturer: NumPy Developers (NumFOCUS fiscally sponsored project)
soup_version: 2.5.5
anomaly_review: "2026-11-25"
links:
  - target: ADD-015
    relation: relates_to
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-037 — NumPy 2.5.5

> Safety-relevant: the decoded frame bytes of the DICOM module are NumPy array bytes (RISK-003).

## Functional and performance requirements

Used only by the DICOM viewer module (SI-MOD-DICOM-BE, [ADD-015](../design-outputs/architecture/ADD-015-dicom-module-backend.md)),
indirectly through pydicom ([SOUP-015](SOUP-015-pydicom.md)): `Dataset.pixel_array` returns a NumPy
`ndarray`, and the frame endpoint returns `pixel_array[N].tobytes()` (SR-017 AC 9, CR-008 D-3, D-4).
Relied on:

- an `ndarray` built by pydicom's native and RLE Lossless decoders holds exactly the stored sample
  values, with the dtype pydicom derives from BitsAllocated and PixelRepresentation;
- indexing the first axis of a multi-frame array selects one frame without copying other frames;
- `ndarray.tobytes()` with the default `order="C"` returns the samples in C (row-major) order, in the
  array's byte order, with no header or padding. The module passes no `order` argument; the
  `order="K"` behaviour discussed in numpy/numpy#16569 is not used.

Performance: one frame of a study within the 1 GiB decoded bound (SR-017 AC 6) is decoded and
serialised in memory; no NumPy threading or BLAS function is used.

Not relied on: anything else in NumPy. MedHub code imports `numpy` only in tests (fixture generation,
CR-008 TASK-235) and in the Docker Build import check (TASK-236).

## Required hardware and software environment

CPython 3.12 to 3.15 (`Requires-Python >=3.12`, PyPI metadata of 2.5.5); MedHub runs 3.12.15
(`python:3.12.15-slim`). Binary wheels: the image uses
`numpy-2.5.5-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl` (glibc 2.28 or later), and
macOS and Linux aarch64 wheels exist for development. The wheel bundles OpenBLAS 0.3.34 (not used by
MedHub). No other runtime dependency. Licence: BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0
(PyPI `License-Expression`).

**Declared by** `backend/modules/dicom_viewer/pyproject.toml` (`numpy>=2.5`, module-owned, CR-008 D-2,
ADR-0024) and **locked** at 2.5.5 in `backend/uv.lock` by TASK-233. Version determined on 2026-11-25 by
resolving the CR-008 workspace layout with uv against the current `backend/uv.lock` in a scratch copy
(no package installed or executed): uv added `medhub-dicom-viewer 0.1.0` and `numpy 2.5.5` and changed
no other locked version. 2.5.5 is the latest release on PyPI on that date (released 2026-11-15).

## Anomaly list review

**Reviewed 2026-11-25** for NumPy 2.5.5 (Software Architect role, CR-008 Plan stage). Published
information only: nothing was installed from, fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and https://github.com/numpy/numpy/security/advisories; NVD; https://github.com/numpy/numpy/releases/tag/v2.5.5; https://github.com/numpy/numpy/issues

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query`, `numpy` 2.5.5: no vulnerability.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=numpy@2.5.5`:
  none. All `pip`/`numpy` advisories listed (8) affect versions below 1.22 (newest: CVE-2021-34141,
  `< 1.22`).
- NumPy repository security advisories — `GET https://api.github.com/repos/numpy/numpy/security-advisories`:
  none published.
- NVD keyword `numpy`, published 2026-08-01 to 2026-11-25: 9 CVEs, none in NumPy itself (NLTK,
  OpenEXR, vLLM, MONAI's `NumpyReader`, asteval, ESPectre, PyTables). The earlier 2026 windows could
  not be read (NVD rate limit); OSV and the GitHub Advisory Database, which carry the NumPy CVEs, cover
  all versions.
- Release notes of 2.5.5 (2026-11-15): a bug-fix release; supports Python 3.12 to 3.15. Fixes in string
  dtypes, `ufunc.at`, `ndarray.take` with a zero-size axis, sorting and datetime error paths, random
  generators, and `np.negative` with strided input. One compatibility note: casting structured or
  subarray dtypes to `StringDType` now raises. The notes mention "the eMudhra compromise fixes" without
  detail in the release body; none of the listed pull requests touches array construction from
  buffers, integer dtypes, byte order, indexing or `tobytes`.
- Open issues labelled "00 - Bug" mentioning `tobytes`, `frombuffer` or `byteswap` (GitHub search,
  2026-11-25): 17 hits, the newest relevant one numpy/numpy#32298 (unpickled arrays on free-threaded
  builds; MedHub does not pickle arrays and runs the default GIL build). #16569 concerns
  `tobytes(order="K")`, which the module does not use.

### Findings

**No known anomaly in NumPy 2.5.5 affects the functions MedHub relies on.** No hazard-relevant
anomaly is handed to `risk-management`. The integer-sample path that a wrong decode would need
(construction, indexing, `tobytes`) is covered by the real-decode tests of TS-019 (TC-019.9, TASK-235),
which compare the returned bytes with known sample values for every supported transfer syntax.

**Note.** 2.5.5 was 10 days old at the review. A defect found in it after release would appear as a
2.5.6; the monitoring below picks it up.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before every
release and at most 365 days apart (`soup_anomaly_max_age_days`), by the Software Architect role with the
human accountable. A new patch release of the 2.5 series is reviewed for fixes in the relied-on functions
above. Hazard-relevant anomalies go to `risk-management` (RISK-003); defects affecting MedHub become PRBs.

## Change log

- 2026-11-25 — Record created at 2.5.5, the version uv resolves for the CR-008 workspace (D-1, D-2): new
  runtime dependency of the DICOM viewer module, needed by `pydicom` pixel decoding for the transfer
  syntaxes of D-3 (a) (PRB-046). First anomaly-list review. Impact analysis: RISK-003 1.6 and RISK-007
  1.21 (CR-008 Risk stage). Locked by TASK-233.
- 2026-11-25 — Locked by TASK-233: `uv lock` resolved 2.5.5 (as determined at Plan), `backend/uv.lock` adds only `medhub-dicom-viewer 0.1.0` and `numpy 2.5.5`; no other locked version changed. `soup_version` unchanged, no re-review needed.
