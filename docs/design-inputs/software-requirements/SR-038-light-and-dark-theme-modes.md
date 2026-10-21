---
id: "SR-038"
type: software-requirement
title: "Light and dark theme modes with accessible contrast"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-17"
updated: "2026-07-17"
links:
  - target: "UN-015"
    relation: derives_from
  - target: "UN-014"
    relation: derives_from
  - target: "NFR-009"
    relation: derives_from
  - target: "NFR-003"
    relation: derives_from
tags: []
---

## Summary

The system shall provide two complete theme modes — light and dark — built from the same design-token structure (SR-037), with every existing screen fully rendered and meeting WCAG 2.1 AA contrast in both modes.

## Description

The design-token foundation defines two value sets over the same token structure: a light mode and a dark mode. Both modes express the same MedHub identity — identical layout, typography scale, spacing, radii, and component appearance — differing only in token values such as surface colors, text colors, and shadow treatment. Dark mode is a first-class presentation: every screen, component state, status indicator, and overlay must be fully styled in both modes, with no unthemed surfaces or illegible text. Text and interactive elements meet WCAG 2.1 Level AA contrast in both modes, and the responsive behavior required by NFR-003 is preserved regardless of mode.

## Acceptance Criteria

1. Light and dark modes are defined as two value sets over the same design-token structure (SR-037); no component defines mode-specific layout or behavior, only token-driven appearance.
2. Every existing screen, dialog, and component state (default, hover/focus, disabled, error, empty, loading) renders fully styled in both modes, with no unthemed surfaces, invisible text, or residual colors from the other mode, verified by visual review of every existing screen in each mode.
3. In both modes, text contrast meets WCAG 2.1 Level AA: at least 4.5:1 for normal text and 3:1 for large text, and at least 3:1 for icons and interactive component boundaries required for identification, verified with a contrast-measurement tool on the token palette and spot-checked on rendered screens.
4. Semantic status indications (success/warning/error/info) are distinguishable in both modes and do not rely on color alone to convey state.
5. Responsive layouts (SR-020 / NFR-003 breakpoints for phone, tablet, desktop) render correctly in both modes.

## Origin Requirement

Derived from: User Need UN-015 "User-controlled light and dark appearance", User Need UN-014 "Professional, modern, and elegant MedHub visual identity", NFR-009 "Usability", and NFR-003 "Device and responsive compatibility".

## Risk Analysis

### Rationale

A dark mode that is incomplete or low-contrast is worse than no dark mode: users in that mode may misread clinical statuses, miss controls, or encounter illegible content. Deriving both modes from one token structure guarantees parity and confines mode differences to reviewable token values.

### Potential Risks

- **Safety/usability:** insufficient contrast or color-only status coding in one mode could cause misreading of clinical information (e.g., appointment or consent state).
- **Regression:** components styled outside the token system could render unreadably in one mode without being noticed.
- **Compatibility:** mode-specific styling bugs could differ across breakpoints or browsers.

### Control Measures

- Measured WCAG 2.1 AA verification of the palette in both modes (criterion 3) and non-color-only status coding (criterion 4).
- Exhaustive two-mode visual review of all screens and component states (criterion 2).
- Single token structure for both modes (criterion 1) prevents structural divergence; responsive verification in both modes (criterion 5).
