---
id: RR-009
type: regulatory-requirement
title: Usability engineering for use-related risk
status: approved
version: "1.0"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-21"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: c208278760f2c550dc66779064c1b529f2c7a9c1ebb40480a12f84f2f7a910bf
approval_note: self-approved
links:
  - target: UN-003
    relation: derives_from
tags:
  - iec62366
  - regulatory
---

# RR-009 — Usability engineering for use-related risk

## Summary

The user interface must be designed so that use errors that could lead to harm are anticipated and mitigated.

## Source

IEC 62366-1:2015 §5 (use specification, user interface of primary operating functions, use-related risk analysis); IEC 62304 §5.2.2 f; NFR-009.

## Obligation

The software shall present clinical information unambiguously, require confirmation for destructive or irreversible actions, and use consistent terminology and clear error messages so that a use error does not silently alter or hide clinical data.

## Acceptance criteria

- Destructive actions require an explicit confirmation whose default choice is the safe one.
- Patient and study identity is visible wherever clinical content or imaging is displayed.
- Error messages state what happened and what the user can do; no silent failure.

## Realized by

SR-027, SR-017, SR-020. Problem report: PRB-031. Risks: RISK-002, RISK-003.
