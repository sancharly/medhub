---
id: "UN-009"
type: user-need
title: "System administrator manages user groups and module enablement"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links: []
tags: []
---

## Summary

A system administrator needs to define user groups and control which modules are enabled for which groups so that functionality is provisioned appropriately across the organization.

## Description

A system administrator configures the platform for the organization. They need to organize users into groups, automatically by user type (for example, all doctors) and manually for specific subsets, and to decide which optional modules (plugins) are available to each group. This lets the organization roll out capabilities such as the DICOM viewer to the right clinicians while keeping the platform manageable and access controlled.

## Acceptance Criteria

1. A system administrator can create user groups.
2. Users can be assigned to groups automatically based on their user type and can also be added to groups manually.
3. A system administrator can enable or disable specific modules for specific user groups.
4. A user gains access to a module only when that module is enabled for a group to which the user belongs.

## Risk Analysis

### Rationale

Derived from the MedHub goals "User groups" (groups defined by the system administrator, auto by user type or manual) and "Modules access" (users access modules enabled by the system administrator for their group).

### Potential Risks

- Security risk: mis-provisioning could enable powerful modules for users who should not have them.
- Operational risk: inability to manage groups/modules prevents the organization from configuring the platform.

### Control Measures

- Group management and per-group module enablement are specified in software requirements traced to this need.
- Module access checks are enforced at runtime per the modular-architecture software requirements (UN-010).
