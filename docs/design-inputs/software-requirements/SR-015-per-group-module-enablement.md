---
id: "SR-015"
type: software-requirement
title: "Per-group module enablement"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "UN-009"
    relation: derives_from
  - target: "UN-010"
    relation: derives_from
tags: []
---

## Summary

The system shall allow a system administrator to enable or disable modules for specific user groups, and shall grant a user access to a module only when it is enabled for a group the user belongs to.

## Description

This requirement implements module provisioning. A system administrator selects a module and the groups for which it is enabled. A user sees and can use a module only if at least one of their groups has that module enabled. Disabling removes access. This applies to the DICOM viewer and any future module.

## Acceptance Criteria

1. A system administrator can enable a module for one or more user groups.
2. A system administrator can disable a previously enabled module for a group.
3. A user can access a module only if it is enabled for at least one group they belong to.
4. When a module is disabled for all of a user's groups, the user can no longer access it.

## Origin Requirement

Derived from: User Need UN-009 "System administrator manages user groups and module enablement" and UN-010 "Extensible platform through modules/plugins".

## Risk Analysis

### Rationale

Controlled per-group enablement ensures powerful modules reach only intended users, supporting least privilege.

### Potential Risks

- Security risk: a module enabled for the wrong group exposes functionality/data inappropriately.
- Operational risk: misconfiguration could withhold needed modules from clinicians.

### Control Measures

- Restrict enablement to system administrators; enforce module-access checks at runtime via SR-005 and SR-016.
- Cover enable/disable transitions with tests.
