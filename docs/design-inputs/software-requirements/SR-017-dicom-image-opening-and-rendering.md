---
id: SR-017
type: software-requirement
title: DICOM image opening and rendering
status: in_review
version: "1.7"
author: Carlos Santiago Liceras
created: "2026-07-07"
updated: "2026-11-25"
links:
  - target: RR-009
    relation: satisfies
  - target: RISK-003
    relation: mitigates
  - target: RISK-007
    relation: mitigates
  - target: UN-011
    relation: derives_from
  - target: NFR-005
    relation: derives_from
tags:
  - control:design
  - control:information
---

## Summary

The DICOM viewer module shall open and correctly render DICOM images (CT, MRI, X-ray), including multi-slice volumetric studies, for authorized users.

## Description

This requirement implements the core of the DICOM viewer. The module reads DICOM files (from clinical-entry attachments or otherwise authorized sources), parses the relevant DICOM metadata, and renders the image faithfully, applying the correct default window/level, pixel scaling, and slice ordering for volumetric series. Only users with the module enabled and authorized to the underlying data can open images.

The module is available only if it is installed: it must be present, and discovered by the host, in every environment built from the repository, including the production image (ADR-0005). The module endpoint serves the stored DICOM object unchanged, or, on request, the decoded pixel data of one frame. Per-frame decoding is supported for an explicit list of transfer syntaxes (CR-008 D-3); any other transfer syntax is refused before decoding, so an object the module cannot decode faithfully is never returned partly or wrongly decoded.

## Acceptance Criteria

1. The module opens a valid DICOM file and displays the image.
2. CT, MRI, and X-ray modalities are supported.
3. For a multi-slice (volumetric) series, the slices are loaded and ordered correctly.
4. The image is rendered with correct pixel scaling and a sensible default window/level derived from the DICOM data.
5. Only a user with the DICOM viewer enabled (SR-015) and authorized to the source data (SR-005) can open the image.
6. The DICOM module refuses, before decoding any pixel data, an object whose stored size exceeds the configured maximum stored size or whose declared decoded size (rows x columns x frames x samples per pixel x bytes per sample) exceeds the configured maximum decoded size, with an RFC 7807 error. A decode that fails part-way returns an error and no image. The maxima are 150 MiB stored and 1 GiB decoded (CR-006 D-2); the attachment upload maximum of SR-013 is raised to match.
7. In every environment built from the repository manifests and lock file (the development environment, the CI test environment and the production backend image), the DICOM viewer module is installed, its `medhub.modules` entry point `dicom-viewer` is discovered at start-up, and its router is mounted: a request to `GET /api/v1/modules/dicom-viewer/studies/{attachment_id}` reaches the module and is answered by its authentication or authorization checks (401 or 403 when they fail), never 404 for a missing route. A production image in which the entry point is not discovered fails the build pipeline.
8. Without the `frame` parameter, the module endpoint returns, to an enabled and authorized user, the stored DICOM object byte-for-byte as `application/dicom`, whatever its transfer syntax, subject to the stored-size bound of AC 6.
9. With `frame=N`, for an object whose transfer syntax is one of the supported transfer syntaxes (CR-008 D-3: Implicit VR Little Endian, Explicit VR Little Endian, Deflated Explicit VR Little Endian, Explicit VR Big Endian and RLE Lossless, pending approval) and 0 ≤ N < number of frames, the endpoint returns status 200 with exactly the decoded pixel values of frame N, for single-frame and multi-frame objects, in the media type and layout fixed by CR-008 D-4 (never labelled `application/dicom` unless it is a DICOM object). N at or beyond the number of frames is refused with an RFC 7807 error.
10. With `frame=N`, an object whose transfer syntax is not supported, or that declares no transfer syntax, is refused before any pixel data is decoded with an RFC 7807 error whose rule is `dicom_transfer_syntax_unsupported` and whose message names the transfer syntax UID. The response contains no pixel data. No request on the frame path answers with partial pixel data or a 5xx for a decode problem: a decode that fails is the AC 6 error.
11. No control in the user interface is labelled or presented as opening the DICOM viewer unless it opens the in-app viewer, and every attachment keeps its Download link. Any control that opens the viewer obtains the study only through the module endpoint (AC 8, AC 9), never through the core attachment URL.

## Origin Requirement

Derived from: User Need UN-011 "Viewing DICOM medical images" and Non-Functional Requirement NFR-005 "Medical device regulatory compliance (MDR and FDA)".

## Risk Analysis

### Rationale

Correct rendering of medical images is safety-critical; as a viewing function it is subject to MDR/FDA expectations.

### Potential Risks

- Safety risk: incorrect scaling, wrong default window, or mis-ordered slices could cause misinterpretation and a clinical error.
- Security risk: unauthorized image access exposes clinical data.
- Safety risk: an object in a transfer syntax the module cannot decode faithfully is decoded wrongly or partly and returned as if it were the image, or raw pixel data is mislabelled as a DICOM object (RISK-003).
- Availability: the module is not installed in a deployed environment, so the function is silently absent (PRB-048; RISK-007).

### Control Measures

- Use a vetted DICOM parsing/rendering approach; verify rendering correctness with reference images during system testing.
- Gate access via SR-005/SR-015; viewer controls provided by SR-018.
- Explicit allow-list of transfer syntaxes checked from the header before decoding (AC 10), and a correctly labelled frame response (AC 9); verified by real decodes on fixtures in TS-019 (CR-008, Plan stage names the test cases).
- Automated check that the production image discovers the module (AC 7), and module tests run against the installed package (CR-008 D-6, D-7).

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-003 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.2 (2026-09-17) — Added `satisfies` link to RR-009 (regulatory requirements
  extracted from the NFRs with clause citations). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.3 (2026-10-21) — Tagged `control:design`, `control:information` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.4 (2026-11-13) — Content change, so the approval is cleared and the record returns to review (CR-006, GitHub sancharly/medhub#28). Added AC 6 (size and decoded-size bound before decoding; a failed decode never renders). Reason: the frame endpoint decoded any object without a bound, so a crafted or very large study could exhaust the API process, and a partial decode must fail loudly (PRB-006; RISK-007, RISK-003).
- 1.5 (2026-11-13) — AC 6 values set by decision D-2 of CR-006: 150 MiB stored, 1 GiB decoded. Stays `in_review`.
- 1.6 (2026-11-13) — Traceability change at the CR-006 Risk gate R-3: added the `mitigates` link to RISK-007. Returned to review for the human's re-approval; AC text unchanged.
- 1.7 (2026-11-25) — Content change, so the approval is cleared and the record returns to review (CR-008, GitHub sancharly/medhub#35). Added AC 7 (module installed and discovered in every environment, including the production image), AC 8 (whole-object path), AC 9 (frame decode for the supported transfer syntaxes), AC 10 (loud refusal of the other transfer syntaxes before decoding) and AC 11 (no user-interface control claims to open a viewer that does not exist; the viewer uses only the module endpoint); Description and Risk Analysis extended. Reason: the module was installed in no environment (PRB-048) and its frame path could not decode (PRB-046). AC 9 and AC 10 name the transfer syntaxes and the frame media type pending CR-008 D-3 and D-4.
