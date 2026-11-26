---
id: SOUP-015
type: soup
title: pydicom
status: approved
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-11-26"
manufacturer: pydicom contributors
soup_version: 3.0.2
anomaly_review: "2026-11-25"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-26"
approved_digest: 7f6096ec6738dc9524d2664ab37949bd173bd2c7e10e3f133d74f8f68ddfdd80
approval_note: self-approved
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-015 — pydicom 3.0.2

> Safety-relevant: rendering correctness feeds RISK-003.

## Functional and performance requirements

DICOM parsing, metadata extraction and validation on upload, and pixel/frame access for the DICOM endpoint (SR-013, SR-017).

**Relied on for pixel decoding (CR-008, D-3 (a), SR-017 AC 9 and AC 10; TASK-234, TASK-235).** For the
five transfer syntaxes the frame path supports — Implicit VR Little Endian (`1.2.840.10008.1.2`),
Explicit VR Little Endian (`1.2.840.10008.1.2.1`), Deflated Explicit VR Little Endian
(`1.2.840.10008.1.2.1.99`), Explicit VR Big Endian (`1.2.840.10008.1.2.2`) and RLE Lossless
(`1.2.840.10008.1.2.5`) — `Dataset.pixel_array` decodes with pydicom's own handlers and NumPy only
([SOUP-037](SOUP-037-numpy.md)), no plugin, and returns exactly the stored sample values: shape
(rows, columns[, samples]) for one frame and (frames, rows, columns[, samples]) for several, in native
byte order. A decode error raises; it never returns a partly filled array. Also relied on: the file
meta information (group 0002, including `TransferSyntaxUID`) can be read without reading or inflating
the data set, so the module checks the transfer syntax before anything else is parsed. In 3.0.2 the
public `read_file_meta_info()` takes a file path only; for in-memory bytes the module uses the public
`pydicom.filereader.read_preamble(fp, False)` followed by the private `_read_file_meta_info(fp)`
(`filereader.py` lines 645 and 732 at `v3.0.2`), which read the preamble and group 0002 and stop. The
reliance on a private function is pinned by a test that fails if it changes (TASK-234, TC-019.6), and is
re-checked at every pydicom upgrade. The frame path
never relies on pydicom to refuse an unsupported syntax: the module's allow-list does (AC 10).

**Not relied on, and guarded instead.** pydicom 3.0.2 inflates the whole data set of a Deflated Explicit
VR Little Endian file in memory with one unbounded `zlib.decompress` while reading it
(`src/pydicom/filereader.py`, lines 891-906 at tag `v3.0.2`), also with `stop_before_pixels=True`. The
frame path therefore bounds the inflated size itself before calling `dcmread` on a deflated object
(TASK-234, TS-019 TC-019.7), and upload validation in the host (`app/attachments/dicom_validation.py`)
does the same with the shared helper `app.modules.dicom_support` (TASK-240, TS-007 TC-007.18; PRB-094).

## Required hardware and software environment

Python 3.12. Pixel-data access (`Dataset.pixel_array`, used by the frame endpoint) requires NumPy,
and compressed transfer syntaxes other than RLE Lossless also need a decoding plugin (Pillow, pylibjpeg or
GDCM). From CR-008 (TASK-233) NumPy 2.5.5 ([SOUP-037](SOUP-037-numpy.md)) is declared by the DICOM viewer
module (`backend/modules/dicom_viewer/pyproject.toml`) and locked in `backend/uv.lock`, so the production
image has it. No decoding plugin is installed, by decision (CR-008 D-3 (a)): every syntax that would need
one is refused before decoding. Metadata parsing needs no other package. pydicom is declared both by the
host (upload validation) and by the module; the lock resolves one version.

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for pydicom 3.0.2, the version `backend/uv.lock` resolves. Priority item: rendering correctness feeds RISK-003. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and https://github.com/pydicom/pydicom/security/advisories; NVD; https://pydicom.github.io/pydicom/stable/release_notes/index.html; https://pydicom.github.io/pydicom/stable/tutorials/installation.html

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `pydicom` 3.0.2.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `pydicom@3.0.2`.
- pydicom repository advisories — https://github.com/pydicom/pydicom/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `pydicom`.
- Release notes — https://pydicom.github.io/pydicom/stable/release_notes/index.html and https://github.com/pydicom/pydicom/releases/tag/v3.0.2 (2026-03-19). 3.0.2 is the latest release.
- Installation and pixel-data guides — https://pydicom.github.io/pydicom/stable/tutorials/installation.html and https://pydicom.github.io/pydicom/stable/guides/user/image_data_handlers.html.

### Findings

**No upstream anomaly applies to 3.0.2.** The one advisory, GHSA-v856-2rf8-9f28 / CVE-2026-32711
(high): a crafted DICOMDIR's `ReferencedFileID` can point outside the File-set root (path
traversal). It affects 2.0.0-rc.1 to 3.0.1 and is fixed in 3.0.2, which is the whole content of the
3.0.2 release. NVD lists only that CVE. The release notes list no known issues for 3.0.x.

**Finding about MedHub's environment (not an upstream defect).** pydicom's installation guide says
NumPy is required to manipulate pixel data, and lists it as optional. pydicom 3.0.2 declares no
runtime dependencies in `backend/uv.lock`, and neither `backend/pyproject.toml` nor the
`dicom_viewer` module declares NumPy. The production image therefore has no NumPy. The pixel-data
guide also says compressed transfer syntaxes (JPEG, JPEG-LS, JPEG 2000) need further plugins
(Pillow, pylibjpeg, GDCM), none of which is installed. This was established from the lock file and
the published documentation and not executed: under the review rules nothing from pydicom is run.

### MedHub use and judgement

Upload validation calls `pydicom.dcmread(..., stop_before_pixels=True)`
(`app/attachments/dicom_validation.py`) and reads metadata only. It needs no NumPy and is
unaffected. The frame endpoint, `GET /studies/{id}?frame=N`
(`modules/dicom_viewer/dicom_viewer/dicom.py`), calls `ds.pixel_array`, which cannot decode
without NumPy. Before that call (CR-006 TASK-218, SR-017 AC 6) the module reads the header only,
with `pydicom.dcmread(..., stop_before_pixels=True)`, and computes the declared decoded size from
Rows, Columns, SamplesPerPixel, BitsAllocated and NumberOfFrames; a missing or non-positive value,
or a size above `dicom_max_decoded_bytes`, is refused before any pixel data is read. Relied on: a
header-only read returns those attributes without touching the pixel data element. Verified by
`modules/dicom_viewer/tests/test_size_bounds.py` (TS-019).

Today that endpoint is unreachable. The QA review of TASK-154 found that the `dicom_viewer`
module is installed in no environment, so its router is never mounted and the request gets a
404 ([PRB-048](../problem-reports/PRB-048-dicom-viewer-module-not-installed.md), major). Once the
module is installed, a `?frame=` request will fail with a server error and return no image. Its
unit tests mock `stream_dicom` and put the module on `sys.path` themselves, so the suite shows
neither defect. Once the module is installed, the endpoint without `?frame=` returns the stored
DICOM unchanged. The frontend does not request `?frame=` (checked 2026-10-22).

Hazard relevance: the failure is loud. No wrong or misattributed image is shown, so no new
hazardous situation arises under RISK-003, whose "fails loudly" protective control (SR-031,
TASK-135, PRB-006) is on the same path. It does affect MedHub's behaviour: the per-frame pixel
access that SR-017 relies on this item for cannot work in a real deployment. Raised as
[PRB-046](../problem-reports/PRB-046-dicom-frame-path-lacks-numpy.md) (minor, 2026-10-22). It
becomes reachable only once PRB-048 is resolved. No RISK change. The fix (declare
NumPy, and decide which transfer syntaxes the frame path supports) is a dependency addition and a
separate CR. It should be planned together with PRB-048 (installing the module) and
PRB-006's decode bound.

### Review of 2026-11-25 (CR-008 Plan stage)

Re-reviewed because CR-008 makes pixel decoding a relied-on function. Same sources as above, on
2026-11-25:

- OSV.dev `pydicom` 3.0.2: no vulnerability. GitHub Advisory Database `pydicom@3.0.2`: none. pydicom
  repository advisories: only GHSA-v856-2rf8-9f28 (CVE-2026-32711), fixed in 3.0.2.
- NVD keyword `pydicom`: CVE-2026-32711 and CVE-2026-48705 (published 2026-11-05). CVE-2026-48705 is a
  MONAI defect (`PydicomReader._get_affine()` trusting non-finite spacing and orientation values, fixed in
  MONAI 1.6.1); it is not a pydicom defect and MedHub does not use MONAI. Not applicable.
- PyPI: 3.0.2 is still the latest release.
- Open issues labelled `bug` mentioning pixel data: pydicom/pydicom#2260 (different pixel arrays after
  JPEG 2000 Lossless compression with an embedded overlay). JPEG 2000 is refused by the frame path
  (D-3 (a)); not applicable.
- Published source, read only (tag `v3.0.2`, `src/pydicom/filereader.py`): the Deflated data set is
  inflated in full with `zlib.decompress(zipped, -zlib.MAX_WBITS)`, with no output limit, during any
  `dcmread` of a deflated file, before `stop_before_pixels` takes effect. A deflate stream reaches
  ratios of about 1000:1, so an object within the 150 MiB stored bound can inflate to far more memory
  than the API container has.

**Findings.** No upstream anomaly applies to 3.0.2. One design property is hazard-relevant for MedHub
(availability, RISK-007; not a pydicom defect): the unbounded inflation above.

- **Frame path (CR-008).** Reachable once the module is installed. Controlled in CR-008: the transfer
  syntax is read from the file meta information first and a deflated data set is inflated with a
  bounded decompressor before pydicom reads it (TASK-234, TC-019.7).
- **Upload validation (host, outside CR-008).** `app/attachments/dicom_validation.py` calls
  `pydicom.dcmread(fp, stop_before_pixels=True)` on every uploaded `application/dicom` file, so a crafted
  deflated file inflates without bound at upload today: PRB-094 (major), taken into CR-008 by the human
  (D-B) and controlled by TASK-240 with the same helper (RISK-007 1.21).

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 3.0.2 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): no upstream anomaly applies to 3.0.2 (CVE-2026-32711 is fixed in it); found that NumPy, which pixel-data access needs, is not installed, so the `?frame=` path cannot decode (MedHub-affecting: PRB-046, minor; the module itself is not installed anywhere: PRB-048, major, found by QA); environment section corrected. Record 1.0 → 1.1; approval record removed for re-review.
- 2026-11-13 — 3.0.2 (unchanged). Relied-on behaviour added: header-only read on the frame endpoint path to bound the decoded size before `pixel_array` (CR-006 TASK-218, SR-017 AC 6, D-2). Record 1.1 → 1.2; approval record removed for re-review.
- 2026-11-25 — 3.0.2 (unchanged). CR-008 Plan stage: relied-on requirements extended to pixel decoding for
  the five transfer syntaxes of D-3 (a) and to the file-meta read of the transfer syntax; NumPy now declared
  by the module (SOUP-037); anomaly list re-reviewed (no upstream anomaly; CVE-2026-48705 is MONAI's); the
  unbounded inflation of Deflated data sets recorded, guarded on the frame path (TASK-234) and in upload
  validation (TASK-240, PRB-094, CR-008 D-B). Record 1.2 → 1.3; approval record removed for re-review.
