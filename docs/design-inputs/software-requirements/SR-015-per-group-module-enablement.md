---
id: SR-015
type: software-requirement
title: Per-group module enablement
status: approved
version: "1.2"
author: Carlos Santiago Liceras
created: "2026-07-07"
updated: "2026-11-13"
approved_by: Carlos Santiago Liceras
approved_on: "2026-11-13"
approved_digest: e4b72a5361f2e50aad624e772e0cdf0be62eb0620a3bc4d14f152800a880b6e6
approval_note: self-approved
links:
  - target: UN-009
    relation: derives_from
  - target: UN-010
    relation: derives_from
  - target: RISK-004
    relation: mitigates
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
5. A change of a module's enablement for a group is reflected in the module-dependent parts of the user interface of every affected user (for example the DICOM viewer link on an attachment) without a page reload, no later than 60 seconds after the change or the user's next navigation to the affected view, whichever comes first, including for a user who did not make the change (CR-006 D-4).

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

## Version history

- 1.1 (2026-11-13) — Content change, so the approval is cleared and the record returns to review (CR-006, GitHub sancharly/medhub#28). Added AC 5 (the client reflects an enablement change without a reload). Reason: the client cached the module list indefinitely, so a viewer stayed hidden after being enabled or offered after being disabled (PRB-015; RISK-004).
- 1.2 (2026-11-13) — Traceability change at the CR-006 Risk gate R-3: added the `mitigates` link to RISK-004. Returned to review for the human's re-approval; AC text unchanged.
