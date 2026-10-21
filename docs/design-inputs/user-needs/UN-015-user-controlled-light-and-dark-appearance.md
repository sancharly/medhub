---
id: "UN-015"
type: user-need
title: "User-controlled light and dark appearance"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-17"
updated: "2026-07-17"
links: []
tags: []
---

## Summary

A MedHub user needs to choose between a light and a dark appearance of the application — and have that choice remembered — so that the interface remains comfortable and readable in their working environment, whether a bright office, a dim reading room, or nighttime use at home.

## Description

MedHub users work in very different lighting conditions: administrative staff and clinicians in bright clinical or office environments, doctors reviewing images in dimmed rooms, and patients often using the platform on personal devices in the evening. A single fixed appearance forces some users into an uncomfortable or fatiguing presentation. Users need the application to offer an equivalent light and dark appearance, to start from a sensible default that matches the appearance their device is already configured for, and to let them switch explicitly at any time without hunting through settings. Once a user has chosen, the application should respect that choice on subsequent visits. Both appearances must be equally legible and complete — dark mode is a first-class presentation of the same interface, not a degraded variant.

## Acceptance Criteria

1. A user can switch the entire application between a light and a dark appearance from an easily discoverable control.
2. A user who has never chosen an appearance sees the application in the mode matching their device/operating-system preference.
3. Once a user explicitly chooses an appearance, the application presents that appearance on subsequent sessions without the user having to choose again.
4. Every screen and workflow is fully usable and legible in both appearances.

## Risk Analysis

### Rationale

Derived from stakeholder feedback requesting a theme-mode switch as part of the UI refresh. Appearance control in differing ambient-light conditions is a comfort and readability need that supports safe, low-error use of clinical workflows (complements NFR-009 usability and NFR-003 device compatibility).

### Potential Risks

- **User risk:** an interface that is uncomfortable in the user's lighting conditions causes eye strain and discourages careful review of clinical information.
- **Usability risk:** if one appearance is incomplete or low-contrast, users in that mode may misread statuses or miss controls.
- **Privacy/context risk:** none identified; the appearance preference carries no clinical or personal health information.

### Control Measures

- Both appearances are defined from the same design system so neither is a degraded variant (see decomposing software requirements).
- Contrast and legibility in both appearances are verified against recognized accessibility criteria.
- The preference default follows the device setting, minimizing surprise for users who never interact with the control.
