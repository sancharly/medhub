---
id: PLAN-001
type: lifecycle-plan
title: Software development plan (IEC 62304, software safety class B)
status: approved
version: "3.0"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-21"
plan_kind: development
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-21"
approved_digest: 4b9bbdcfc084671846bf725c18ded6be76a2476a6f0cc8da1d9eadb15ff07557
approval_note: self-approved
links: []
tags:
  - regulatory
  - class:B
---

# PLAN-001 — Software development plan

## Purpose

Define the plan followed to develop MedHub: the activities of each stage, the records those
activities produce, and the gates that show an activity was executed, under
IEC 62304:2006+A1:2015 §5.1. Version 3.0 supersedes [ADD-002](../design-outputs/architecture/ADD-002-software-development-plan.md)
(v2.0), which itself replaced the narrative `docs/software-development-plan.md` (v1.0). The other
lifecycle activities have their own plans:

| Plan | `plan_kind` | Clause |
|---|---|---|
| [PLAN-002 Maintenance](PLAN-002-maintenance-plan.md) | `maintenance` | §6.1 |
| [PLAN-003 Configuration management](PLAN-003-configuration-management-plan.md) | `configuration-management` | §8 |
| [PLAN-004 Problem resolution](PLAN-004-problem-resolution-plan.md) | `problem-resolution` | §9 |
| [PLAN-005 Risk management](PLAN-005-risk-management-plan.md) | `risk-management` | §7, ISO 14971 §4.4 |

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
classification and its rationale are recorded in `docs/medtrace.yml` (`safety_class`,
`classification_rationale`), which the plugins read first, and mirror the
`software-safety-class` key in [`../../CLAUDE.md`](../../CLAUDE.md). It is reviewed whenever
risk analysis finds a hazard the class does not cover (§4.3 c); a reclassification changes this plan.

## Tooling and process source

Agents and skills come from the [agentic-os](https://github.com/sancharly/agentic-os) plugins
(`core-engineering`, `medical-records`, `web-fullstack`, `design-studio`), enabled in
`.claude/settings.json`. The project configuration block in `CLAUDE.md` declares
`sdlc-extensions: [medical-records:iec62304-sdlc]`, so the lite spec-and-plan pipeline runs with the
IEC 62304 overlay on top: the stages, records and gates below. `/ship-feature` drives a feature
end to end, delegates each stage to the matching agent, and creates the feature branch when run on
the default branch.

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
| SOUP | `soup` | `soup/` | Plan (dependency change) |
| TS | `test-specification` | `design-outputs/tests-specifications/` | Build |
| TP / TR | `test-plan` / `test-report` | `test-plans-reports/plans|reports/` | Release |
| REL | `release` | `releases/` | Release |
| PRB / CR | `problem-report` / `change-request` | `problem-reports/` / `change-requests/` | Any stage (§9) |
| PLAN | `lifecycle-plan` | `plans/` | Process changes only |

IDs are permanent, statuses come from the record type's set only, and traceability lives in
`links` — never in prose and never in a hand-maintained matrix. Templates for a type live in
`docs/templates/<type>.md`. Under the IEC 62304 overlay a feature's plan *is* its TASK records:
no free-standing `docs/plans/<feature>.md` file is written, because `docs/plans/` holds only
`lifecycle-plan` records.

## Stages

```
Specify ─→ [GATE] ─→ Risk ─→ Plan ─→ [GATE] ─→ Build ⇄ Review ─→ Release ─→ [GATE]
```

### Specify — requirements analysis

The Product Owner turns inputs (user feedback, industry needs, the application
[goals](../design-inputs/goals.md), intended use, regulation) into design inputs: User Needs,
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
([PLAN-005](PLAN-005-risk-management-plan.md)), and control measures in ISO 14971 priority order.
Class B applies §7.1–7.3 to every feature; §7.4.1 change analysis applies to every change, including
the answer "no impact" with its reasoning.

**Outputs:** RISK records; risk-control SRs (§5.2.3) with `mitigates` links. **Gate:** no
safety-relevant SR without a RISK assessment; residual risk accepted by the human, never by an
agent.

### Plan — architecture and design

The Software Architect turns approved SRs into architecture: ADD records per software item, the
arc42 narrative in [`../design/`](../design/) (sections 1–8 and 10–12; section 9 is the ADR
log), UML diagrams in [`../specifications/`](../specifications/), the decomposition into
software items and units (§5.4.1 — class B stops at units), and the interfaces between items. SOUP
changes are recorded with `soup-management`, one `soup` record per component in
[`../soup/`](../soup/). Work is broken into TASK records rather than checkboxes.

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

On APPROVED the orchestrator commits the task: one commit per QA-approved task, which also carries
the task's records — the TASK and TS updates and any RISK, SOUP or PRB record created or changed
for it. Agents never commit, and nothing is pushed without the human's confirmation.

**Gate:** zero `traceability-check` errors for the feature's records.

### Release (§5.8)

Before the release tag: a test plan (TP) and test reports (TR) with `test-plan-and-report-writer`,
system testing of every SR (§5.7), regression for changed items, the SOUP versions frozen at the
built versions, the evaluation of residual anomalies (§5.8.2–5.8.3), and one `release` record
(`REL-###` in `docs/releases/`) with `release_version`. Its body lists the verification summary,
every PRB not `closed`/`rejected` with its evaluation, and each SOUP item with its built version.
The release records get their own commit, made before the tag; once tagged, `git_tag` is set.

**Gate** — all must hold before the tag is created and the REL leaves `draft`:

- no `critical` PRB open that was created on or before the release;
- no SOUP item with a missing anomaly review, or one older than `soup_anomaly_max_age_days`
  (365 in `docs/medtrace.yml`);
- every SR verified by a TR;
- `traceability-check` reports no errors in release scope.

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

## Definition of done for a pull request

- [ ] Requirements exist as approved UN/NFR/RR/SR records for the change
- [ ] Risk analysis performed for the change (§7.4.1), with RISK records for safety-relevant findings
- [ ] Architecture and task records defined and approved, arc42 and ADRs updated where affected
- [ ] SOUP records added or updated for every dependency the change adds, upgrades or removes
- [ ] Software units implemented, with unit and integration tests written and passing
- [ ] Test specifications exist for the SRs the change touches
- [ ] Code review performed and approved by the QA Engineer, one commit per approved task
- [ ] `traceability-check` reports zero errors for the change's records
- [ ] Defects found on the way are recorded as PRBs, not silently fixed

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

Class B consequences checked by `traceability-check`: every SR is covered by an ADD, and every
SOUP item is linked from an ADD and considered by a RISK.

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
| 2.0 | 2026-09-17 | Promoted to ADD-002; stages, records, gates and roles aligned with the `medical-records:iec62304-sdlc` overlay |
| 3.0 | 2026-10-21 | Re-issued as a `lifecycle-plan` record for medical-records 0.3.2; maintenance, configuration management and problem resolution split into PLAN-002..004; release record and gate, SOUP records and per-task commits added |
