---
id: "SR-026"
type: software-requirement
title: "Performance budgets for routine operations"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "NFR-008"
    relation: derives_from
tags: []
---

## Summary

The system shall meet defined response-time budgets for routine interactive operations and for initial DICOM image display under normal load.

## Description

This requirement implements the performance NFR with concrete, testable budgets. Routine operations complete within 3 seconds, saving a clinical entry (excluding upload time) within 3 seconds, and initial DICOM image rendering within 10 seconds for a typical study, all under normal load.

## Acceptance Criteria

1. Page navigation and data-listing operations (profile, appointments, clinical entries) complete within 3 seconds under normal load.
2. Saving a clinical entry (excluding large file upload time) completes within 3 seconds under normal load.
3. Opening a DICOM image presents an initial rendered image within 10 seconds under normal load for a typical study.
4. These budgets are verified by performance/system tests.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-008 "Performance and responsiveness".

## Risk Analysis

### Rationale

Concrete budgets make the performance NFR testable and protect clinical-workflow efficiency.

### Potential Risks

- User/operational risk: slow responses disrupt clinical and administrative workflows.

### Control Measures

- Define performance budgets and verify with automated performance/system tests; defer heavy operations to preserve responsiveness.
