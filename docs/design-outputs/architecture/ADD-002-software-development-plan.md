---
id: "ADD-002"
type: architecture-doc
title: "Software development plan (IEC 62304, software safety class B)"
status: in_review
version: "2.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-09-17"
links:
  - target: "SR-028"
    relation: implements
  - target: "ADD-001"
    relation: relates_to
tags: ["sdp", "regulatory", "class:B"]
---

# Software Development Plan

## Purpose

Define the plan followed to develop MedHub: the activities of each stage, the records those
activities produce, and the gates that show an activity was executed, under
IEC 62304:2006+A1:2015. Version 2.0 supersedes `docs/software-development-plan.md` (v1.0) and is
itself a controlled record.

## Scope and product description

MedHub is a web application that acts as a hub for patients and healthcare providers, centralizing
personal health information (PHI) and medical activity in one place. Doctors upload patient clinical
data after visits or procedures; patients access that information and can share it with different
specialists. The modular architecture allows new plugins to add functionality, with the goal of
becoming the central hub for clinical activity in a hospital or medical center regardless of
specialty.

**Software safety class: B** (IEC 62304 §4.3). A failure — data attributed to the wrong patient, an
incorrect DICOM render, a stale consent state — can contribute to a wrong clinical decision, so
non-serious injury is possible while serious injury is not a foreseeable direct result. The
classification rationale is recorded in `docs/medtrace.yml` and mirrors the
`software-safety-class` key in [`../../../CLAUDE.md`](../../../CLAUDE.md). It is reviewed whenever
risk analysis finds a hazard the class does not cover (§4.3 c); a reclassification changes this plan.

## Tooling and process source

Agents and skills come from the [agentic-os](https://github.com/sancharly/agentic-os) plugins
(`core-engineering`, `medical-records`, `web-fullstack`, `design-studio`), enabled in
`.claude/settings.json`. The project configuration block in `CLAUDE.md` declares
`sdlc-extensions: [medical-records:iec62304-sdlc]`, so the lite spec-and-plan pipeline runs with the
IEC 62304 overlay on top: the stages, records and gates below. `/ship-feature` drives a feature
end to end and delegates each stage to the matching agent.

## Design records

Every design element is one Markdown file with YAML frontmatter, per the
`medical-records:design-record-structure` contract (MedTrace-compatible). `docs-root` is `docs/`.

| Record | Type | Folder | Produced in |
|---|---|---|---|
| UN | `user-need` | `design-inputs/user-needs/` | Specify |
| NFR | `nfr` | `design-inputs/system-requirements/non-functional/` | Specify |
| RR | `regulatory-requirement` | `design-inputs/system-requirements/regulatory/` | Specify |
| SR | `software-requirement` | `design-inputs/software-requirements/` | Specify, Risk (controls) |
| RISK | `risk` | `risks/` | Risk |
| ADD | `architecture-doc` | `design-outputs/architecture/` | Plan |
| TASK | `task` | `design-outputs/tasks/` | Plan |
| TS | `test-specification` | `design-outputs/tests-specifications/` | Build |
| TP / TR | `test-plan` / `test-report` | `test-plans-reports/plans|reports/` | Release |
| PRB / CR | `problem-report` / `change-request` | `problem-reports/` / `change-requests/` | Any stage (§9) |

IDs are permanent, statuses come from the record type's set only, and traceability lives in
`links` — never in prose and never in a hand-maintained matrix. Templates for a type live in
`docs/templates/<type>.md`.

## Stages

```
Specify ─→ [GATE] ─→ Risk ─→ Plan ─→ [GATE] ─→ Build ⇄ Review ─→ Release ─→ [GATE]
```

### Specify — requirements analysis

The Product Owner turns inputs (user feedback, industry needs, the application
[goals](../../design-inputs/goals.md), intended use, regulation) into design inputs: User Needs,
non-functional requirements and regulatory requirements, decomposed into software requirements with
`regulated-requirements`. A **User Need** is a qualitative statement of a problem, desire or
challenge faced by an end user (clinician, patient, administrative personnel) without dictating the
solution. **Non-functional requirements** describe how the system performs rather than what it does.
A **Regulatory Requirement** states an obligation imposed by a regulation, standard or the intended
use, citing the exact clause.

Software requirements are verified to: implement their user needs, NFRs and RRs; not contradict each
other (§5.2.6); be unambiguous; allow objective acceptance criteria; be uniquely identified; and be
traceable upward. The §5.2.2 content checklist (a–l, including security, usability, data definition,
IT-network and regulatory categories) is walked per feature, with "not applicable" decisions
recorded.

**Outputs:** UN, NFR, RR and SR records. **Gate:** every SR carries a `satisfies`/`derives_from`
link, and a human moves the records `in_review → approved`. Authors never approve their own records.

### Risk — hazard analysis (§7, ISO 14971)

The Software Architect, with the human, analyses the change with `risk-management`: which software
items contribute to a hazardous situation, the Hazard → Sequence of events → Hazardous situation →
Harm chain, severity and probability per the risk management plan
([ADD-003](ADD-003-risk-management-plan.md)), and control measures in ISO 14971 priority order.
Class B applies §7.1–7.3 to every feature; §7.4.1 change analysis applies to every change, including
the answer "no impact" with its reasoning.

**Outputs:** RISK records; risk-control SRs (§5.2.3) with `mitigates` links. **Gate:** no
safety-relevant SR without a RISK assessment; residual risk accepted by the human, never by an
agent.

### Plan — architecture and design

The Software Architect turns approved SRs into architecture: ADD records per software item, the
arc42 narrative in [`../../design/`](../../design/) (sections 1–8 and 10–12; section 9 is the ADR
log), UML diagrams in [`../../specifications/`](../../specifications/), the decomposition into
software items and units (§5.4.1 — class B stops at units), and the interfaces between items. SOUP
changes are recorded with `soup-management` in the SOUP list
([ADD-004](ADD-004-soup-list.md)). Work is broken into TASK records rather than checkboxes.

**Outputs:** ADD records, TASK records, ADRs, updated arc42 sections and diagrams; an updated SOUP
list. **Gate:** every TASK `implements` ≥1 SR, every ADD `implements` ≥1 SR, and a human approves.

### Build — implementation and unit verification

The Software Developer implements one TASK at a time from the records, tests first. Coding standards
and the conventions in `docs/templates/task.md` apply. Class B requires unit verification (§5.5)
with acceptance criteria, and integration of the modified units with interface verification (§5.6).
Test specifications are written with `test-plan-and-report-writer`.

**Outputs:** source code, configuration, build/install/deploy instructions (git); TS records.
A TASK moves `draft → in_review` on handoff — never straight to `approved`. Any defect found outside
the current task becomes a PRB instead of a silent fix.

### Review — QA

The QA Engineer reviews the implementation against the records, coding standards and security
expectations, and runs `traceability-check` over the feature's records. **APPROVED** moves the TASK
and its TS to `approved`; **CHANGES REQUESTED** returns the TASK to `draft` with the findings in its
body. Any traceability error is CHANGES REQUESTED. After three rounds on the same task, escalate to
the human.

**Gate:** zero `traceability-check` errors for the feature's records.

### Release (§5.8)

Before a release tag: a test plan (TP) and test report (TR) with `test-plan-and-report-writer`,
system testing of every SR (§5.7), regression for changed items, the SOUP list frozen at the built
versions, and evaluation of residual anomalies (§5.8.2–5.8.3) recorded in the TR.

**Gate:** every SR verified by a TR or dispositioned as an accepted residual anomaly; no `critical`
PRB open that was created before the release; the release's build is reproducible and archived
(§5.8.5–5.8.7).

## Testing levels

| Level | Clause | Class B | Evidence |
|---|---|---|---|
| Unit verification | §5.5 | required | automated unit tests, review, static analysis (`ruff`, `mypy`, `eslint`, `tsc`) |
| Integration | §5.6 | required | integration tests across integrated items and interfaces |
| System | §5.7 | required | tests of every SR on the integrated system, including E2E |
| Regression | §5.6.6, §5.7.3 | required | re-run after every change |

Tests are automated wherever possible and live in the repository (`backend/tests/`,
`frontend/src/**/*.test.ts*`, E2E suites); TS/TP/TR records state what is verified, how, and what
happened, referencing the automated tests by path and name. Manual test execution is recorded in a
TR. All acceptance criteria of a linked SR map to at least one test case.

## Problem resolution (§9)

Defects — reported by users, found in review, or found during verification — are recorded as PRB
records with an honest `criticality` and resolved through a CR that links `resolves` → PRB, using
`problem-report-resolution`. Problems found during formal verification are never fixed on the fly
without a PRB. Trends across problem reports are reviewed at each release (§9.8).

## Configuration management (§8) and Git Flow

Code, documentation and design records live in one git repository; everything a stage produces is
version-controlled. SOUP items are identified with title, manufacturer and exact version in the SOUP
list (§8.1.2), pinned by the lock files.

One branch per unit of work, named `feature/…`, `user-story/…`, `enabler-story/…`, `bug/…` or
`doc/…`, merged to `main` through a pull request. Automated test reports produced by CI need not be
committed. Commits follow the `commit-message` skill.

**Definition of done for a pull request:**

- [ ] Requirements exist as approved UN/NFR/RR/SR records for the change
- [ ] Risk analysis performed for the change (§7.4.1), with RISK records for safety-relevant findings
- [ ] Architecture and task records defined and approved, arc42 and ADRs updated where affected
- [ ] Software units implemented, with unit and integration tests written and passing
- [ ] Test specifications exist for the SRs the change touches
- [ ] Code review performed and approved by the QA Engineer
- [ ] `traceability-check` reports zero errors for the change's records
- [ ] Defects found on the way are recorded as PRBs, not silently fixed

## Maintenance (§6)

This plan is a living document, updated as the process evolves; a change to it is a new `version`
and a new review. Released software is maintained through the same process: feedback and problems
enter as PRBs, are evaluated for safety impact, and are implemented as CRs through the stages above.
SOUP anomaly lists and security advisories are monitored per the SOUP list's monitoring section
(§6.1 f), at most 365 days between reviews (`soup_anomaly_max_age_days` in `docs/medtrace.yml`).

## Class B tailoring (Table A.1)

| Clause | Activity | Applies |
|---|---|---|
| 5.1 | Development plan; integration planning §5.1.5 | this document |
| 5.2 | Software requirements, incl. risk-control requirements §5.2.3 | required |
| 5.3 | Architectural design, SOUP functional/performance and HW/SW requirements §5.3.3–5.3.4 | required |
| 5.3.5 | Segregation for risk control | class C only — not applicable |
| 5.4 | Detailed design down to software units (§5.4.1) | required; §5.4.2–5.4.4 per-unit detail not required |
| 5.5 | Unit verification process, criteria and verification (§5.5.2–5.5.3) | required; §5.5.4 additional criteria class C only |
| 5.6 | Integration and integration testing | required |
| 5.7 | Software system testing | required |
| 5.8 | Release: verification complete, anomalies evaluated, versions archived, build reproducible | required |
| 6 | Maintenance plan and modification process | required |
| 7.1–7.3 | Contribution to hazards, risk controls, verification of controls | required |
| 7.4 | Risk analysis of changes | required |
| 8 | Configuration management incl. SOUP identification | required |
| 9 | Problem resolution | required |

## Roles

| Role | Agent | Owns |
|---|---|---|
| Product Owner | `product-owner` | UN, NFR, RR, SR records |
| Software Architect | `software-architect` | RISK, ADD, TASK records, ADRs, arc42, SOUP |
| Software Developer | `software-developer` | code, unit/integration tests, TS records |
| QA Engineer | `qa-engineer` | review verdicts, approvals, traceability gate |
| Document Writer | `document-writer` | arc42 and ADD consistency, user documentation |
| Human (Carlos Santiago) | — | all `approved` transitions, risk acceptability and residual-risk acceptance, safety classification, release decision |

## Version history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-06 | Initial plan as a narrative document (`docs/software-development-plan.md`) |
| 2.0 | 2026-09-17 | Promoted to a design record; stages, records, gates and roles aligned with the `medical-records:iec62304-sdlc` overlay; added the Risk and Release stages, class B tailoring table, SOUP, problem resolution, configuration management and maintenance |
