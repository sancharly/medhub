---
id: "NFR-003"
type: nfr
title: "Device and responsive compatibility"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links: []
tags: []
---

## Summary

The application shall be accessible and usable from desktop browsers as well as from mobile devices (tablets and phones) through a responsive interface.

## Description

Users access MedHub from different devices depending on their context: clinicians and administrators often on desktops, patients and clinicians on the move via tablets and phones. The interface must adapt responsively to the available screen size so that core workflows remain usable across desktop, tablet, and phone form factors. This requirement applies system-wide to all user-facing functionality.

## Acceptance Criteria

1. The interface adapts its layout responsively to desktop, tablet, and phone viewport widths without horizontal scrolling of primary content.
2. Core workflows are operable on a representative phone, a representative tablet, and a desktop.
3. Interactive controls remain reachable and usable (adequate target size, no clipped or inaccessible elements) on small screens.

## Risk Analysis

### Rationale

Derived from the MedHub constraint "Devices compatibility": the application shall be accessible from desktop navigators as well as mobile devices (tablets and phones).

### Potential Risks

- User risk: an unusable mobile layout excludes patients and mobile clinicians from the platform.
- Safety risk: clipped or unreachable controls on small screens could cause errors during clinical use.

### Control Measures

- Responsive design with verified breakpoints for phone, tablet, and desktop.
- System testing of core workflows on representative device sizes.
