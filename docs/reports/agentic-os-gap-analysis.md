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

### Disposition detail

| # | What was done |
|---|---|
| G1 | `## Project configuration` in `CLAUDE.md`: overlay on, class B, `docs-root`, `arc42-root`, `arc42-sections`. **fixed** |
| G2 | `medtrace.yml` set to class B, `no_soup: false`, rationale drafted from the intended use. **partial** — the rationale needs human approval |
| G3 | SDP promoted to [ADD-002](../design-outputs/architecture/ADD-002-software-development-plan.md) with the stage overlay, gates, class B tailoring table, §6/§8/§9 sections and the agent role map; the old path is a pointer. **fixed** |
| G4 | [ADD-004](../design-outputs/architecture/ADD-004-soup-list.md) lists every component at its locked version; anomaly review explicitly pending (TASK-154); pinning findings raised as PRB-001 and PRB-002. **partial** — the review itself is outstanding |
| G5 | [ADD-003](../design-outputs/architecture/ADD-003-risk-management-plan.md) with the owner-approved 5×5 bands, plus RISK-001..011 and `mitigates` links from 42 SRs and TASKs. **partial** — residual-risk acceptance is a human decision |
| G6 | TS-001..013, TP-001 and [TR-001](../test-plans-reports/reports/TR-001-verification-report-migration-baseline.md) from a real run: 29 of 39 SRs verified, the other 10 named with the reason. **partial** — by evidence, not by omission |
| G7 | ADD-005..ADD-023, one per software item, with units, `implements` links and pointers to the arc42 narrative. **fixed** |
| G8 | All 8 E8 errors fixed by promoting the SR each task actually implements. **fixed** |
| G9 | 30 problem reports opened (PRB-003..032) for every still-open defect, with the source documents annotated and the already-fixed findings named. **fixed** |
| G10 | RR-001..010 with clause citations, and `satisfies` links from the 22 SRs that realize them. **fixed** |
| G11 | `traceability-matrix.md` deleted; its data folded into the ADDs; TASK-114 and TASK-148 marked `obsolete`. **fixed** |
| G12 | `implementation-plan/README.md` rewritten around the records, `docs/templates/task.md` created, stale paths in TASK-092/116 fixed, phase tags normalized. **fixed** |
| G13 | `medtrace-migration-prompt.md` and the empty `exports/`, `releases/` folders removed. **fixed** |
| G14 | `arc42-sections: 1-8, 10-12` declared; §9 documented as the ADR log in `docs/design/README.md`. **fixed** |

## Result

The record set went from **8 errors / 248 warnings** to **0 errors / 95 warnings**, with 272 records
scanned (from 181). The remaining warnings are all expected and none of them is a defect in the
records:

| Check | Count | Why it is open |
|---|---|---|
| W5 | 72 | An `approved` record links to an `in_review` one — the new risk, regulatory, architecture and verification records await the owner's approval. Clears on approval. |
| W2 | 10 | The 10 SRs TR-001 names as unverified: blocked real-database cases, the unimplemented DICOM viewer, the browser matrix and performance validation. |
| W7 | 9 | Approved tasks whose SR has no TS yet — the same SR-017, SR-018 and SR-026 group. |
| W1 | 3 | SR-017, SR-018 and SR-026 have no test specification because the features and the performance run do not exist yet. |
| W6 | 1 | TASK-148 links to TASK-114; both are `obsolete`, so the link is history, not a dangling reference. |

## What the human still owns

1. Approve the class B rationale in `docs/medtrace.yml`.
2. Approve ADD-002, ADD-003, ADD-004 and the ADD-005..023 set (`in_review → approved`).
3. Approve RR-001..010 and accept the residual risk of RISK-001..011 — no agent may do this.
4. Approve TS-001..013, TP-001 and TR-001.
5. Decide the order in which the 30 problem reports are resolved; each fix goes through a change
   request that links `resolves` → its PRB.

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

## Plugin update — 2026-10-21

The project's plugins moved to core-engineering 0.4.0, medical-records 0.3.2, web-fullstack 0.2.0
and design-studio 0.2.0. The record contract changed between medical-records 0.2.0 (what the
September work was written against) and 0.3.2. The new gap report is
[gap-report-2026-10-21.md](gap-report-2026-10-21.md).

| Contract change (0.2.0 → 0.3.2) | What was done |
|---|---|
| New `lifecycle-plan` type with `plan_kind`; class B needs development, maintenance, configuration-management, problem-resolution and risk-management plans | PLAN-001..005 in `docs/plans/`; ADD-002 and ADD-003 marked `obsolete` with pointers |
| New `soup` type, one record per runtime component, linked from the ADD that uses it and from a RISK; development tooling is not SOUP | SOUP-001..035 at their locked versions, linked from ADD-005..023 and RISK-001..011; ADD-004 marked `obsolete` |
| RISK scores move into frontmatter, `acceptability` is derived from `risk_matrix`, ALARP needs a justification, controls are tagged by type | RISK-001..011 migrated with the approved scores unchanged; five ALARP justifications written; 42 SRs/TASKs tagged `control:*` |
| The risk matrix is read from `medtrace.yml`; without it a ratio rule applies that differs from the approved bands | Approved bands encoded as `risk_matrix`. The table in the approved plan set S1×P5 to ALARP although the score bands make it acceptable; the table was kept and the exception is written down in PLAN-005 |
| `criticality` moves to the type-specific position after `updated` | All PRB records reordered |
| `traceability-check` adds type-specific field checks (E4) and class-gated rules | Parser rewritten; the result is below |

Corrections found while moving the data: `fhir.resources` is locked at 8.2.0 (ADD-004 had recorded
`fhir-core`'s 1.1.8), and `fakeredis` is a test fake declared as a runtime dependency —
**PRB-033**. TASK-147 (risk register bootstrap) was handed to review.

### Result

**313 records, 0 errors, 133 warnings and class-gated findings.**

| Finding | Count | Why it is open |
|---|---|---|
| W5 | 72 | Approved records linking to records that await the owner's approval |
| `soup_anomaly_review_stale` | 35 | No SOUP item has an anomaly review yet — TASK-154. Blocks release, not development |
| W2 / W1 / W7 | 10 / 3 / 9 | The SRs TR-001 does not verify: Docker-blocked cases, the DICOM viewer, the browser matrix, performance |
| `risk_control_unverified` | 2 | TASK-113 and TASK-137 implement risk controls whose SRs no test report reaches yet |
| `soup_unintegrated` | 1 | SOUP-018 `fakeredis`: no item uses it (PRB-033) |
| `sr_without_architecture` | 1 | SR-028 (traceable, version-controlled records) was covered by ADD-002/003, which are now plans. It is a process requirement that no software item implements; see the note below |

**Owner decisions (2026-10-21).** SR-028 was restated as the regulatory requirement **RR-011**
(SR-028 and TS-013 are now `obsolete`), which removes `sr_without_architecture`. PLAN-005's band
summary was aligned with `risk_matrix`, which governs. After those changes: **314 records, 0
errors**. New, expected findings: W4 on RR-011 (satisfied by the plans, not by an SR), W6 on
TASK-001/005/147/154 (process tasks still implementing the obsolete SR-028 — the contract requires a
TASK to implement an SR and none fits process work), and `risk_control_unverified` on TASK-111 and
TASK-154 (their only verified SR was SR-028).
