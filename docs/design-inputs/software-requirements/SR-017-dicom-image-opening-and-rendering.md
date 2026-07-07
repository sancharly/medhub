---
id: "SR-017"
type: software-requirement
title: "DICOM image opening and rendering"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "UN-011"
    relation: derives_from
  - target: "NFR-005"
    relation: derives_from
tags: []
---

## Summary

The DICOM viewer module shall open and correctly render DICOM images (CT, MRI, X-ray), including multi-slice volumetric studies, for authorized users.

## Description

This requirement implements the core of the DICOM viewer. The module reads DICOM files (from clinical-entry attachments or otherwise authorized sources), parses the relevant DICOM metadata, and renders the image faithfully, applying the correct default window/level, pixel scaling, and slice ordering for volumetric series. Only users with the module enabled and authorized to the underlying data can open images.

## Acceptance Criteria

1. The module opens a valid DICOM file and displays the image.
2. CT, MRI, and X-ray modalities are supported.
3. For a multi-slice (volumetric) series, the slices are loaded and ordered correctly.
4. The image is rendered with correct pixel scaling and a sensible default window/level derived from the DICOM data.
5. Only a user with the DICOM viewer enabled (SR-015) and authorized to the source data (SR-005) can open the image.

## Origin Requirement

Derived from: User Need UN-011 "Viewing DICOM medical images" and Non-Functional Requirement NFR-005 "Medical device regulatory compliance (MDR and FDA)".

## Risk Analysis

### Rationale

Correct rendering of medical images is safety-critical; as a viewing function it is subject to MDR/FDA expectations.

### Potential Risks

- Safety risk: incorrect scaling, wrong default window, or mis-ordered slices could cause misinterpretation and a clinical error.
- Security risk: unauthorized image access exposes clinical data.

### Control Measures

- Use a vetted DICOM parsing/rendering approach; verify rendering correctness with reference images during system testing.
- Gate access via SR-005/SR-015; viewer controls provided by SR-018.
