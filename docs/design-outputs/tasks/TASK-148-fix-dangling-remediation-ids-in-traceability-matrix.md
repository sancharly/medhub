---
id: "TASK-148"
type: task
title: "Fix dangling remediation IDs in the traceability matrix"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-028"
    relation: implements
  - target: "TASK-114"
    relation: relates_to
tags: ["phase:review-2026-07", "severity:low", "regulatory"]
---

- **Phase:** Review 2026-07 — regulatory blockers
- **Implements:** SR-028 (traceable, version-controlled development records)
- **Depends on:** — (do before TASK-114 completes the matrix)
- **Branch:** `doc/fix-matrix-remediation-ids`
- **Status:** Not started
- **Source:** `docs/reports/CODE-REVIEW-2026-07.md` — finding Y (Low)

## Objective

The "Audit remediation note" table in `docs/design/traceability-matrix.md` references remediation
tasks by their original working IDs (`TASK-024a`, `TASK-029a`, `TASK-044a`, `TASK-069a`, …), but the
files on disk were renumbered to TASK-116…TASK-134 (each carries an `original-id:` tag). No
`*a.md` files exist — every remediation reference in the matrix is a dangling link. In an audit,
the primary traceability artifact points at records that do not resolve.

## Implementation detail

- Build the `a`-ID → real-ID map from the `original-id:` tags in TASK-116..134 frontmatter
  (`grep -l original-id docs/design-outputs/tasks`).
- Rewrite the matrix remediation table to the real TASK IDs (keep original IDs in parentheses if
  historical context is wanted).
- Add/extend a link-check script (or use the MedTrace tooling) that fails on any `TASK-\d+[a-z]`
  or otherwise unresolvable ID in `docs/` — prevents recurrence.

## Acceptance criteria

- [ ] Every task reference in `traceability-matrix.md` resolves to an existing file.
- [ ] Link check runs in CI (or documented manual gate) and fails on dangling design-record IDs.

## Definition of Done

- [ ] Matrix updated; link check green
- [ ] TASK-114 executor notified (scope touches the same file)
