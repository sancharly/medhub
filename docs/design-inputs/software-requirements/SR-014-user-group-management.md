---
id: "SR-014"
type: software-requirement
title: "User group management"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "UN-009"
    relation: derives_from
tags: []
---

## Summary

The system shall allow a system administrator to create user groups and to assign users to groups both automatically by user type and manually.

## Description

This requirement implements group management. A system administrator can create groups, and users are placed into groups automatically based on their user type (for example, all doctors) and can additionally be added to or removed from groups manually. Groups are the unit to which module enablement is applied.

## Acceptance Criteria

1. A system administrator can create and name a user group.
2. The system can assign users to a group automatically based on their user type.
3. A system administrator can manually add or remove a user from a group.
4. The set of groups a user belongs to is retrievable for use in module-access decisions.

## Origin Requirement

Derived from: User Need UN-009 "System administrator manages user groups and module enablement".

## Risk Analysis

### Rationale

Groups let the organization provision modules to the right users at scale while keeping access controlled.

### Potential Risks

- Security risk: incorrect group membership could grant unintended module access.
- Operational risk: inability to manage groups blocks configuration.

### Control Measures

- Restrict group management to system administrators (via SR-005); derive automatic membership from user type (SR-004).
- Module enablement applied per group by SR-015.
