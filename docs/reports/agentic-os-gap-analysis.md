# agentic-os migration — documentation gap analysis

**Date:** 2026-09-17 · **Branch:** `doc/agentic-os-migration` · **Baseline:** [gap-report-2026-09-17.md](gap-report-2026-09-17.md)

MedHub's agents and skills used to be copies inside `.claude/`; they now come from the
[agentic-os](https://github.com/sancharly/agentic-os) plugins. This report compares the existing
documentation with what those plugins require — mainly `medical-records` (the
`medical-records:iec62304-sdlc` overlay at **software safety class B**) and `core-engineering` —
and records what is fixed in this branch.

## Artifact migration

| Plugin (agentic-os @ `e1495f1`) | Replaces |
|---|---|
| `core-engineering` 0.2.0 | agents `product-owner`, `software-architect`, `software-developer`, `qa-engineer`, `document-writer`; skills `arc42`, `architecture-designer`, `commit-message`, `planning-and-task-breakdown`, `plantuml`, `requirements-writer`, `spec-driven-development`. The `process-manager` agent is replaced by the `ship-feature` skill |
| `medical-records` 0.2.0 | `design-record-structure`, `problem-report-resolution`, plus the new `iec62304-sdlc`, `regulated-requirements`, `risk-management`, `soup-management`, `test-plan-and-report-writer` and `traceability-check` |
| `web-fullstack` 0.1.0 | `api-designer`, `fastapi-patterns`, `frontend-design`, `frontend-patterns`, `react-patterns`, `react-performance`, `react-testing` |
| `design-studio` 0.1.0 | `banner-design`, `brand`, `design`, `design-system`, `slides`, `ui-styling`, `ui-ux-pro-max` |

No local copy held a MedHub-specific customization worth keeping: the project's `plantuml` still
carried Qt/QML rules from another project, and `design-record-structure` / `arc42` hard-coded paths
that are now project configuration (`docs-root`, `arc42-root`, `arc42-sections` in `CLAUDE.md`).

## What already matched the plugins

The MedTrace migration did most of the structural work. All **181 records** pass
`design-record-structure`: valid frontmatter in the exact field order, IDs as `<PREFIX>-<###>` with
no letter suffixes, no duplicate IDs, each record in its type's folder, statuses only from the
canonical set, and **no dangling links**. Every SR has a `derives_from` link and a Risk Analysis
section, and every UN and NFR is decomposed into at least one SR (no W4 warnings).

## Gaps and disposition

Status: **fixed** in this branch · **partial** (record created, human decision pending) · **open**
(tracked as a record to work later).

| # | Gap | Rule source | Disposition |
|---|---|---|---|
| G1 | No `## Project configuration` block, so no `sdlc-extensions`, `software-safety-class`, `docs-root`, `arc42-root` or `arc42-sections` | agentic-os `CONFIGURATION.md` | **fixed** — block added to `CLAUDE.md`; class B, overlay enabled |
| G2 | `medtrace.yml` declared `safety_class: C` with the rationale "not a medical device", and `no_soup: true` — mutually contradictory and wrong for this stack | `iec62304-sdlc` preconditions | **partial** — set to class B with a drafted rationale and `no_soup: false`; the rationale needs human approval |
| G3 | The SDP was not a record, described the retired `process-manager` role process, and had no Risk stage, Release stage, SOUP, problem resolution (§9), configuration management (§8) or maintenance (§6). Stale links to `../test-specifications` and `non-functional-requirements` | `iec62304-sdlc` §5.1 + stage overlay | see below |
| G4 | No SOUP list. Docker images float (`minio/minio:latest`, `nginx:alpine`, `redis:7-alpine`) and Python/npm manifests use ranges | `soup-management` §8.1.2 | see below |
| G5 | No risk management plan and zero RISK records; risks lived as prose in arc42 §11. Already known and tracked as **TASK-147** | `risk-management`, §7.1–7.3 (class B) | see below |
| G6 | Zero TS/TP/TR records: all 39 SRs unverified (W1/W2), despite 70 backend and 26 frontend test files | `test-plan-and-report-writer`, §5.5–5.7 | see below |
| G7 | One ADD record only (ADD-001). Class B requires architecture records for the 19 software items in `05-building-blocks.md` | `iec62304-sdlc` §5.3 | see below |
| G8 | 8 E8 errors: TASK-140/141/143 have no `implements` link; TASK-003/136/138/146/147 point `implements` at an NFR, and the required link is to an SR | `design-record-structure` | see below |
| G9 | No `problem-reports/` or `change-requests/` folders. The defects in `implementation-plan/AUDIT-FINDINGS.md` and `reports/CODE-REVIEW-2026-07.md` never became PRBs | `problem-report-resolution`, §9 | see below |
| G10 | No regulatory requirements (RR). GDPR, MDR/FDA, IEC 62304 and cybersecurity obligations live inside NFRs with no clause citations | `regulated-requirements` | see below |
| G11 | `design/traceability-matrix.md` duplicates the frontmatter links and is stale (cites the invalid ID `TASK-004a`). Already tracked as **TASK-148** | `traceability-check` supersedes it | see below |
| G12 | `implementation-plan/README.md` points at `phase-*` folders deleted in the MedTrace migration; `TASK-TEMPLATE.md` belongs at `docs/templates/task.md`; TASK-092 and TASK-116 cite deleted paths | `design-record-structure` (templates) | see below |
| G13 | `medtrace-migration-prompt.md` is a spent one-off now covered by `design-record-structure`'s migration rules; `docs/exports/` and `docs/releases/` are empty and outside the taxonomy | — | see below |
| G14 | arc42 section 9 is `adr/README.md`, not a canonical `09-*.md` file | `arc42` `arc42-sections` | **fixed** — `arc42-sections: 1-8, 10-12` declared, with §9 documented as the ADR log |

Remaining dispositions are filled in as each remediation step lands; this file is updated in the
same commit as the work it describes.

## Verified counts (baseline)

| Type | Count | | Type | Count |
|---|---|---|---|---|
| `user-need` | 15 | | `risk` | 0 |
| `nfr` | 9 | | `test-specification` | 0 |
| `regulatory-requirement` | 0 | | `test-plan` | 0 |
| `software-requirement` | 39 | | `test-report` | 0 |
| `architecture-doc` | 1 | | `problem-report` | 0 |
| `task` | 117 | | `change-request` | 0 |

Baseline: **8 errors, 248 warnings** (39 × W1, 39 × W2, 169 × W7 — all three collapse once test
specifications exist — and 1 × W5, TASK-132 approved while linking to the draft TASK-101).

## How the gap report is produced

`medical-records:traceability-check` prescribes a script above ~50 records. The parser used here is
throwaway (kept in the session scratchpad, not committed) and implements checks E1–E10 and W1–W7
from the skill, including the target *type* of every required link. Re-run it before each release
and commit the report to `docs/reports/`.
