---
id: "PRB-028"
type: problem-report
title: "Module version regex accepts trailing garbage"
status: resolved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-02"
criticality: minor
links: []
tags: ["security"]
---

# PRB-028 — Module version regex accepts trailing garbage

## Observed

`app/modules/discovery.py` — `_SEMVER_RE` is not fully anchored, so a version like `1.2.3-evil!` is accepted during module discovery.

## Impact

A module can declare a version the registry cannot compare meaningfully (SR-016); no code execution follows from it, since modules are trusted code at MVP.

## Investigation

Read on 2026-10-31 (CR-004 Plan stage, Software Architect role). **Present as reported.**

- `backend/app/modules/discovery.py:13` compiles `^\d+\.\d+\.\d+` and `discovery.py:29` uses
  `.match`, which anchors only the start. `1.2.3-evil!`, `1.2.3.4` and `1.2.3 ` are accepted.
- No other check of the version follows; the registry stores the string as given.

## Safety evaluation

No hazard at MVP (ADR-0005: modules are reviewed, trusted code).

## Resolution

TASK-200 (CR-004), 2026-11-02: `_SEMVER_RE` in `backend/app/modules/discovery.py` is now the module contract's
version rule (SR-016 AC 1: the semver.org expression, ASCII only, no leading zeros, optional pre-release and build) and `_is_valid_manifest` uses `fullmatch`,
so `1.2.3x`, `1.2.3 `, `1.2.3\n`, `1.2.3-evil!`, `1.2.3.4`, `01.2.3`, `v1.2.3`, `1.0.0-01`, `1.0.0-a..b`, `1.2.3` followed by a non-ASCII digit and an empty version are
rejected with the existing warning and skip. Verified by TS-010 TC-010.5
(`TestModuleVersionShape`, 9 accepted, 23 rejected and a timing case); with `fullmatch` put back to `match`, 16 cases fail, and with `\d` instead of `re.ASCII` 3 fail. The bundled
`dicom-viewer` version (`0.1.0`) still passes. QA approved TASK-200 on 2026-11-02 (round 2); status `resolved` (CR-004 D-8). `closed` is a human step at release.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Security, Low.

## Version history

- 1.1 (2026-10-31) — CR-004 Plan stage (Software Architect role): `## Investigation` added from the current tree (§9.2); Resolution points at the planned tasks. Status and criticality unchanged.
- 1.2 (2026-11-02) — TASK-200: `## Resolution` written; status left `open` pending QA approval (D-8).
- 1.3 (2026-11-02) — TASK-200 round 2: Resolution follows QA round 1 (ASCII digits, strict identifiers, wording).
- 1.4 (2026-11-02) — QA round 2 approved TASK-200: status `resolved` (CR-004 D-8).
