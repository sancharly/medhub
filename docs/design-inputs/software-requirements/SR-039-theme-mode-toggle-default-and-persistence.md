---
id: "SR-039"
type: software-requirement
title: "Theme mode toggle, system default, and persistence"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-17"
updated: "2026-07-17"
links:
  - target: "UN-015"
    relation: derives_from
  - target: "NFR-009"
    relation: derives_from
tags: []
---

## Summary

The system shall provide a visible theme-mode toggle in the application chrome that switches between light and dark mode (SR-038), shall default to the user's operating-system color-scheme preference until the user makes an explicit choice, and shall persist the explicit choice across sessions.

## Description

A theme-mode toggle control is permanently visible in the application chrome (the persistent header/navigation area) wherever that chrome is shown, so users can switch modes at any point in any workflow without navigating to a settings page. Until the user has made an explicit choice, the application resolves its mode from the operating-system/browser color-scheme preference. Once the user activates the toggle, that explicit choice takes precedence over the system preference and is persisted on the client so it is applied automatically on subsequent visits from the same browser. Switching is immediate and non-disruptive: no page reload, no loss of in-progress form input, no navigation change. The preference is a purely presentational, client-side setting; storing it requires no backend or API change and involves no personal health information.

## Acceptance Criteria

1. A theme-mode toggle control is visible in the application chrome on every screen that displays the chrome, and is operable by keyboard and labeled for assistive technologies.
2. Activating the toggle switches the entire application between light and dark mode immediately, without a page reload, without losing in-progress user input, and without changing the current screen.
3. For a user who has never made an explicit choice, the application starts in the mode indicated by the operating-system/browser color-scheme preference, and follows that preference if it changes while no explicit choice exists.
4. Once the user makes an explicit choice, that mode is applied regardless of the system preference and persists across page reloads and new sessions in the same browser on the same device.
5. The current mode is applied consistently on all screens, including screens shown before authentication.
6. The preference is stored client-side only; no backend or API change is required, and no personal or clinical data is written as part of the preference.

## Origin Requirement

Derived from: User Need UN-015 "User-controlled light and dark appearance" and NFR-009 "Usability" (discoverable, consistent controls).

## Risk Analysis

### Rationale

The toggle is the user-facing control that makes UN-015 real. Its placement in the persistent chrome makes appearance control discoverable without training (NFR-009), and the system-preference default gives correct behavior to users who never notice the control.

### Potential Risks

- **Usability:** a hidden or ambiguous toggle leaves users stuck in an uncomfortable mode; a disruptive switch (reload, lost input) could discard in-progress clinical or scheduling data entry.
- **Consistency:** if some screens ignore the stored preference, users experience jarring mode flips mid-workflow.
- **Expectation mismatch:** the preference is per browser/device, so a user may see different modes on different devices.

### Control Measures

- Toggle is always visible in the chrome and switching is non-disruptive by acceptance criteria 1–2, verified in system testing.
- Criterion 5 requires uniform application of the mode across all screens.
- The per-device behavior is inherent to client-side persistence (criterion 6, which also keeps the change frontend-only); cross-device roaming of the preference is intentionally out of scope and recorded as such.
