---
id: "SR-037"
type: software-requirement
title: "Design-token-based theming foundation"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-17"
updated: "2026-07-17"
links:
  - target: "UN-014"
    relation: derives_from
  - target: "NFR-009"
    relation: derives_from
tags: []
---

## Summary

The system shall define the application's visual appearance through a single centralized set of design tokens — covering color, typography, spacing, corner radii, and elevation/shadows — and all existing screens and shared components shall derive their visual styling from these tokens.

## Description

The MedHub visual identity is expressed as a design-token foundation: named, centrally defined values for the color palette (including one primary accent color and semantic status colors), the typography scale, the spacing scale, corner radii, and elevation/shadow styles. Screens and components consume tokens instead of hard-coding visual values, so the identity is applied uniformly and future adjustments propagate everywhere from one place. The token set defines a unique MedHub identity: calm and restrained, with a single strong accent, inspired by — but visually distinct from — the reference material provided by stakeholders. This is a frontend-only restyling of the existing application: it introduces no new product functionality, requires no backend or API changes, and must not alter the behavior of any existing workflow.

## Acceptance Criteria

1. A single centralized design-token definition specifies: the color palette (surfaces, text, one primary accent, semantic status colors for success/warning/error/info), the typography scale (font family, sizes, weights), the spacing scale, corner radii, and elevation/shadow styles.
2. All existing screens and shared components obtain their colors, typography, spacing, radii, and shadows from the design tokens; no screen defines ad-hoc hard-coded values for these tokenized attributes.
3. Equivalent elements are styled identically across all existing screens (e.g., all data tables, all status indicators, all primary actions share one appearance), verified by visual review of every existing screen.
4. Design review confirms the resulting identity is professional, modern, and elegant, and is distinct from the stakeholder reference material and from unstyled framework defaults.
5. No functional regression: all existing automated frontend tests pass, and every existing workflow behaves identically before and after the restyle. No backend or API change is introduced.

## Origin Requirement

Derived from: User Need UN-014 "Professional, modern, and elegant MedHub visual identity" and NFR-009 "Usability" (consistent navigation and terminology across modules and screens).

## Risk Analysis

### Rationale

A token-based foundation is the mechanism that makes a broad visual refresh consistent and maintainable. Without it, per-screen styling drifts, producing exactly the inconsistency UN-014 seeks to eliminate and increasing the chance that a future change misses screens.

### Potential Risks

- **Regression:** touching the styling of every screen risks breaking layout or hiding controls in edge cases.
- **Usability:** an over-designed palette or typography could reduce readability of clinical content.
- **Maintainability:** partial adoption (some screens tokenized, some not) would leave a permanently inconsistent interface.

### Control Measures

- Full-coverage visual review of every existing screen (criterion 3) and regression run of the existing automated test suite (criterion 5).
- Restrained palette with a single accent and semantic status tokens (criterion 1) keeps emphasis on clinical content.
- Criterion 2 forbids ad-hoc values, preventing partial adoption from persisting.
