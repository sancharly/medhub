---
id: "SR-018"
type: software-requirement
title: "DICOM viewer controls"
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

The DICOM viewer module shall provide level/contrast adjustment, zoom in/out, pan, and slice navigation for volumetric studies.

## Description

This requirement implements the minimum interactive controls of the DICOM viewer. While viewing an image the user can adjust the window level/contrast, zoom in and out, pan across the image, and, for volumetric multi-slice studies, navigate between slices. Controls update the displayed image consistently and predictably.

## Acceptance Criteria

1. The user can adjust window level/contrast and the displayed image updates accordingly.
2. The user can zoom in and zoom out, and the image scales accordingly.
3. The user can pan the image to view areas outside the current viewport when zoomed.
4. For a volumetric multi-slice study, the user can navigate forward and backward through slices, and the displayed slice changes accordingly.
5. Controls behave consistently across the supported browsers (NFR-001).

## Origin Requirement

Derived from: User Need UN-011 "Viewing DICOM medical images" and Non-Functional Requirement NFR-005 "Medical device regulatory compliance (MDR and FDA)".

## Risk Analysis

### Rationale

These controls are explicitly required for the first prototype and are necessary for clinicians to inspect images adequately.

### Potential Risks

- Safety risk: a control that misrepresents the image (e.g., wrong slice shown for the indicated index) could cause misinterpretation.
- Usability risk: unintuitive controls could hinder inspection.

### Control Measures

- Verify each control's behavior against expected output during system testing, including slice-index correctness.
- Ensure consistent behavior across target browsers (SR-019).
