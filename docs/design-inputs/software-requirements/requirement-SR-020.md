# SR-020 Responsive layout across devices

## Summary

The system shall present a responsive layout that adapts to desktop, tablet, and phone viewports so core workflows remain usable on each.

## Description

This requirement implements device compatibility. The interface uses responsive design to reflow content for desktop, tablet, and phone widths. Primary content does not require horizontal scrolling, and interactive controls remain reachable and adequately sized on small screens. Core workflows are operable on each form factor.

## Acceptance Criteria

1. The layout adapts at defined breakpoints for phone, tablet, and desktop without horizontal scrolling of primary content.
2. Core workflows (login, profile, clinical entry view/create, appointment view, DICOM viewer) are operable on a representative phone, tablet, and desktop.
3. Interactive controls meet a minimum touch target size and are not clipped on small screens.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-003 "Device and responsive compatibility".

## Risk Analysis

### Rationale

A responsive interface lets patients and mobile clinicians use the platform and prevents small-screen usability errors.

### Potential Risks

- User risk: an unusable mobile layout excludes users.
- Safety risk: clipped/unreachable controls could cause errors.

### Control Measures

- Implement and verify responsive breakpoints; test core workflows on representative device sizes.

## Status

Approved

## Version History

Version 1.0 - Initial creation
