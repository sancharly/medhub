---
id: "UN-001"
type: user-need
title: "Web-based access to the health hub"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links: []
tags: []
---

## Summary

A user needs to access the MedHub platform and its medical activities through a standard web browser, without installing dedicated software.

## Description

Doctors, patients, administrative personnel, and system administrators operate from varied environments (hospital workstations, clinics, home, the field). They need a single point of access to centralized health information and medical activities that works from a common web browser so that onboarding is frictionless and no client-side installation or maintenance is required. The platform should be reachable as a web application regardless of the user's operating system.

## Acceptance Criteria

1. A user can reach and use the application by navigating to a URL in a web browser, with no additional software installation required.
2. The core activities of every user type (authentication, profile access, and their type-specific modules/data) are operable through the browser interface.
3. No platform-specific desktop or mobile application is required to perform the core workflows.

## Risk Analysis

### Rationale

Derived from the MedHub goal "Web application": the application shall have a web interface accessible from a web explorer. A browser-based hub lowers adoption barriers and centralizes maintenance.

### Potential Risks

- Operational risk: if browser access is unreliable, clinical workflows that depend on the hub are disrupted.
- User risk: inconsistent behavior across environments could erode trust in the tool.

### Control Measures

- Implement and verify the application as a web application served over HTTP(S) (see SR traced to this need).
- Cross-browser and responsive behavior are controlled by NFR-001 (browser compatibility) and NFR-003 (device compatibility).
