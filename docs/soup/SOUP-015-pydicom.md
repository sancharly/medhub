---
id: SOUP-015
type: soup
title: pydicom
status: approved
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-23"
manufacturer: pydicom contributors
soup_version: 3.0.2
anomaly_review: "2026-10-22"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-23"
approved_digest: b86493c5cdec03b6bb7ebfc822fbf0f7669cdeffea679d8a76c0b3352eb3826a
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

## Required hardware and software environment

Python 3.12. Pixel-data access (`Dataset.pixel_array`, used by the frame endpoint) requires NumPy,
and compressed transfer syntaxes also need a decoding plugin (Pillow, pylibjpeg or GDCM). None of
these is declared in `backend/pyproject.toml` or locked in `backend/uv.lock`, so the production
image has none (see the anomaly-list review of 2026-10-22). Metadata parsing needs no other package.

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
without NumPy.

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

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 3.0.2 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): no upstream anomaly applies to 3.0.2 (CVE-2026-32711 is fixed in it); found that NumPy, which pixel-data access needs, is not installed, so the `?frame=` path cannot decode (MedHub-affecting: PRB-046, minor; the module itself is not installed anywhere: PRB-048, major, found by QA); environment section corrected. Record 1.0 → 1.1; approval record removed for re-review.
