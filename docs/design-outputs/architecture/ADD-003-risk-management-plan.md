---
id: "ADD-003"
type: architecture-doc
title: "Risk management plan (ISO 14971 x IEC 62304 §7)"
status: obsolete
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
links:
  - target: "SR-028"
    relation: implements
  - target: "ADD-002"
    relation: relates_to
tags: ["risk-plan", "regulatory", "class:B"]
---

> **Obsolete (2026-10-21).** Superseded by [PLAN-005](../../plans/PLAN-005-risk-management-plan.md). Since medical-records 0.3.2,
> lifecycle plans are `lifecycle-plan` records in `docs/plans/`, not `architecture-doc` records.
> This element is kept, unchanged below, because design-record IDs are never deleted or reused.

# Risk management plan

> **Acceptability criteria approved by Carlos Santiago Liceras on 2026-09-17** (ISO 14971 §4.4 —
> a human decision, recorded here rather than invented per hazard). The record itself stays
> `in_review` until the owner sets `approved`; individual residual-risk acceptances remain separate
> human decisions recorded in each RISK record.

## Scope and responsibilities

Covers the MedHub software (software safety class B, see
[ADD-002](ADD-002-software-development-plan.md)) and the hazards to which it can contribute
through the information it stores, renders and discloses. MedHub does not control therapy or
actuate hardware; its contribution to harm is through **wrong, missing, delayed, or wrongly
disclosed clinical information**.

| Activity | Owner |
|---|---|
| Hazard identification, analysis, control design | `software-architect` agent with the human |
| Implementation and verification of controls | `software-developer`, `qa-engineer` agents |
| Risk acceptability criteria (this plan) and residual-risk acceptance | **the human owner only** |
| Post-release monitoring (problem reports, SOUP anomalies) | Software Architect role, reviewed at each release |

Risk records live in `docs/risks/` as `risk` elements per `design-record-structure`, one per
hazardous situation, and are the risk management file together with this plan, the SOUP list
([ADD-004](ADD-004-soup-list.md)) and the test reports that verify the controls.

## Method

1. Identify the software items involved (from ADD/TASK records or the diff).
2. Analyse each item's contribution to a hazardous situation (§7.1.1): incorrect or missing
   function, wrong timing, corrupted or misattributed data, interface or SOUP failure, foreseeable
   misuse, and security threats that can lead to harm.
3. Write the chain as a sequence: **Hazard → Sequence of events → Hazardous situation → Harm**.
4. Estimate severity of the harm and probability of the hazardous situation.
5. Design controls in ISO 14971 priority order: inherent safety by design → protective measures →
   information for safety. Every software control becomes an SR with `mitigates` → the RISK.
6. Verify each control by naming the TS/TR that proves it works. A control with no verification is
   not a control.
7. Evaluate residual risk and the risks introduced by the controls themselves; present both to the
   human for acceptance, and record the decision and its date in the RISK record.

### Probability for software failures

Software failure probability cannot be estimated from failure rates. Following the IEC 62304 §4.3
convention, the probability of the **software failure itself is taken as 1** (assume the fault
occurs). What is estimated is the probability of the *hazardous situation leading to harm*
(P2): whether a clinician acts on the wrong information before another safeguard catches it.
Scores therefore combine severity with P2, and the P1 column of a RISK record records the
assumption rather than a number.

## Severity scale (5 levels, matching `severity_max: 5`)

| # | Level | Definition for MedHub |
|---|---|---|
| 5 | Catastrophic | Contributes to death or irreversible serious injury (e.g. a wrong-patient image drives a wrong intervention) |
| 4 | Serious | Contributes to serious injury or a condition needing medical intervention to prevent it |
| 3 | Moderate | Contributes to non-serious injury, a wrong but recoverable clinical decision, or care delayed enough to worsen outcome |
| 2 | Minor | Temporary discomfort, avoidable extra procedure, or a privacy breach with no physical harm |
| 1 | Negligible | Inconvenience only; no clinical or privacy consequence |

Note: class B assumes serious injury is not a foreseeable *direct* result. Severity 4–5 rows are
expected to be rare and, when one appears, trigger a re-examination of the safety class (§4.3 c)
rather than a quiet acceptance.

## Probability (P2) scale (5 levels, matching `probability_max: 5`)

| # | Level | Definition (probability that the hazardous situation leads to the harm) |
|---|---|---|
| 5 | Frequent | Expected in routine use; no other safeguard stands between the fault and the harm |
| 4 | Probable | Likely to reach a clinical decision; only a weak safeguard (a clinician noticing an oddity) |
| 3 | Occasional | Reaches a decision in some workflows; a plausible independent check exists |
| 2 | Remote | Requires an unusual combination of conditions, or an independent check normally catches it |
| 1 | Improbable | Requires several independent failures; strong safeguards outside the software |

## Risk level and acceptability

Risk level = severity × probability, banded as:

| Band | Score | Meaning | Required action |
|---|---|---|---|
| **Unacceptable** | ≥ 15, or any severity 5 with probability ≥ 2 | Must not ship | Add controls until the band changes; a release is blocked |
| **ALARP** | 6–14, or severity 5 with probability 1 | Acceptable only with controls in place and a documented justification | Controls implemented and verified; residual risk explicitly accepted by the human; benefit/risk argument recorded |
| **Acceptable** | ≤ 5 | Acceptable as is | Record the reasoning; no control required beyond existing practice |

Matrix (S = severity, P = probability; U = unacceptable, A = ALARP, ✓ = acceptable):

| S \ P | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **5** | A | U | U | U | U |
| **4** | ✓ | A | A | U | U |
| **3** | ✓ | A | A | A | U |
| **2** | ✓ | ✓ | A | A | A |
| **1** | ✓ | ✓ | ✓ | ✓ | A |

Overall residual risk acceptability (ISO 14971 §8) is judged by the human at each release, over the
whole register rather than risk by risk.

## Rules

- Severity is never lowered to make a risk acceptable. Only controls that reduce severity or
  probability change an evaluation.
- No agent marks residual risk acceptable; RISK records are left `in_review` for the human.
- A RISK with no `mitigates` link after the Plan stage is a gap (`traceability-check` W3).
- If analysis reveals a hazard the current safety class does not cover, stop and escalate:
  reclassification changes ADD-002 and the whole overlay.
- Security threats are analysed here only insofar as they can lead to harm (including privacy harm);
  the security posture itself is requirements-driven (SR-022, SR-023, SR-030, SR-031).

## Inputs to the register

- arc42 [§11 risks and technical debt](../../design/11-risks-and-technical-debt.md) — the prose
  risks that seed the register.
- The Risk Analysis section of every SR record.
- Audit and review findings: `docs/implementation-plan/AUDIT-FINDINGS.md`,
  `docs/reports/CODE-REVIEW-2026-07.md`, and open problem reports.
- SOUP anomaly reviews ([ADD-004](ADD-004-soup-list.md), TASK-154).
