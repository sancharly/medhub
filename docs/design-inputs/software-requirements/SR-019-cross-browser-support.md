---
id: "SR-019"
type: software-requirement
title: "Cross-browser support"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "NFR-001"
    relation: derives_from
tags: []
---

## Summary

The system shall function correctly on the current stable releases of Safari, Firefox, Chrome, and Edge.

## Description

This requirement implements browser compatibility. All core workflows and modules, including the DICOM viewer, render and operate correctly on the four target browsers. The application relies on standards-based web technologies and provides fallbacks where a capability differs between browsers.

## Acceptance Criteria

1. Authentication, profile, role-specific data/modules, appointment scheduling, clinical entries, and the DICOM viewer operate without functional errors on the current stable Safari, Firefox, Chrome, and Edge.
2. Layout renders without broken or overlapping elements on each of the four browsers.
3. A documented cross-browser test pass is executed and recorded for each release.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-001 "Browser compatibility".

## Risk Analysis

### Rationale

Browser-specific defects would exclude users and could cause misreading of clinical information.

### Potential Risks

- User/operational risk: a defect on one browser locks out a user segment.

### Control Measures

- Use standards-based technologies; run cross-browser system tests on the four targets before release.
