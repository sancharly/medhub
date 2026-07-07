---
id: "NFR-009"
type: nfr
title: "Usability"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links: []
tags: []
---

## Summary

The application shall be usable by its target user types with minimal training, presenting clear, consistent, and error-resistant interfaces.

## Description

MedHub serves clinicians, patients, administrative staff, and administrators with differing technical proficiency. The interface must be learnable and consistent so users can complete their core tasks reliably with minimal training, and it must guide users away from errors that could affect data integrity or patient safety. This cross-cutting attribute applies to all user-facing workflows and complements the device-compatibility requirement (NFR-003).

## Acceptance Criteria

1. Each user type can complete its primary core task (e.g., a doctor recording a clinical entry, a patient granting consent, an administrator scheduling an appointment) without written instructions beyond on-screen guidance, in usability evaluation.
2. Navigation and terminology are consistent across modules and screens.
3. Destructive or safety-relevant actions (e.g., revoking access, deleting data) require explicit confirmation.
4. The system presents clear, actionable error messages when an operation fails or input is invalid.

## Risk Analysis

### Rationale

Cross-cutting quality attribute reflecting the platform's goal of providing a seamless experience for patients and healthcare providers, and supporting safe use (IEC 62304 / medical-device usability expectations). Formal usability engineering per IEC 62366 will be expanded post-MVP; the MVP applies basic usability controls.

### Potential Risks

- User risk: a confusing interface causes errors, abandonment, or unsafe workarounds.
- Safety risk: unclear confirmation of destructive actions could cause unintended data loss or access changes.

### Control Measures

- Apply consistent UI patterns, confirmation dialogs for destructive actions, and clear error messaging, verified through usability review and system testing.
- Coordinate with NFR-003 for device-appropriate layouts.
