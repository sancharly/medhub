# Remediation Plan — Code Review 2026-07

Source: `docs/reports/CODE-REVIEW-2026-07.md`. New tasks TASK-135..148 (all `status: draft`);
existing draft tasks referenced by ID. Ordering: severity first, then dependency edges, then
effort batching. Effort: S ≤ ½ day · M ≤ 2 days · L > 2 days. One branch/PR per task, per
`TASK-TEMPLATE.md` conventions.

## Phase R0 — Regulatory blockers (start immediately; independent of code phases)

| Order | Task | Sev | Effort | Deps | Origin |
|-------|------|-----|--------|------|--------|
| R0.1 | TASK-116 clinical data re-keying (SR-024 erasure) | High | M | — | known-planned (only open prior-audit remediation) |
| R0.2 | TASK-147 ISO 14971 risk register bootstrap | High | L | — | **new finding** |
| R0.3 | TASK-148 fix dangling matrix remediation IDs | Low | S | before TASK-114 | **new finding** |
| R0.4 | TASK-114 traceability matrix completion (+ test-spec records in `tests-specifications/`) | High | L | R0.2, R0.3, test tail R4 | known-planned |

## Phase R1 — Backend security/robustness (parallelizable, all independent)

| Order | Task | Sev | Effort | Deps | Origin |
|-------|------|-----|--------|------|--------|
| R1.1 | TASK-137 client IP in authz/consent audit | Med | M | — | new |
| R1.2 | TASK-138 PII scrubbing in worker logs | Med | S | — | new |
| R1.3 | TASK-141 worker reliability (session leak, retry parity, silent enqueue) | Med | M | — | new |
| R1.4 | TASK-139 CSRF exemption exact-match | Med | S | — | new |
| R1.5 | TASK-140 auth config hygiene (dead signing key, required lockout) | Low | S | — | new |

## Phase R2 — Performance / architecture

| Order | Task | Sev | Effort | Deps | Origin |
|-------|------|-----|--------|------|--------|
| R2.1 | TASK-135 true streaming attachment upload/download | **High** | M | — (schedule first in R2) | new |
| R2.2 | TASK-136 align async handlers with sync IO stack | Med | M | after TASK-135 (same router) | new |
| R2.3 | TASK-145 route-based code splitting | Low | S | before TASK-112 | new |

Note: TASK-135 is High — it may run in parallel with R0/R1 from day one; it sits in R2 only
because TASK-136 must queue behind it.

## Phase R3 — Frontend correctness / guards

| Order | Task | Sev | Effort | Deps | Origin |
|-------|------|-----|--------|------|--------|
| R3.1 | TASK-144 useMe hook, session TTL reconciliation, module-cache invalidation | Med | M | — | new |
| R3.2 | TASK-143 unify API client upload + ProblemError guard | Low | S | — | new |
| R3.3 | TASK-100/101 frontend module registry + nav gating | Med | L | — | known-planned |
| R3.4 | TASK-142 route-level role guards | Med | S | benefits from R3.3 nav config | new |
| R3.5 | TASK-102/103 DICOM viewer | Med | L | R3.3 | known-planned |

## Phase R4 — Verification tail (gates release)

| Order | Task | Sev | Effort | Deps | Origin |
|-------|------|-----|--------|------|--------|
| R4.1 | TASK-146 frontend unit-test gaps | Med | M | after R3.1/R3.2 | new |
| R4.2 | TASK-110 integration tests (seven runtime flows) | High | L | R1–R3 landed | known-planned |
| R4.3 | TASK-111 system E2E (Playwright) | High | L | R4.2 | known-planned |
| R4.4 | TASK-112 performance validation vs budgets | Med | M | R2.3 | known-planned |
| R4.5 | TASK-113 security review — include review residuals: admin `list_all` projection check, CSRF route inventory, `X-Forwarded-For` trust chain | High | M | R1 landed | known-planned + checklist |
| R4.6 | TASK-115 deploy/run docs + first-sysadmin bootstrap; populate `docs/releases/` | Med | M | last | known-planned |

## Critical path

TASK-116 → TASK-147 → (TASK-148) → TASK-114 → R4 test tail → TASK-113 → TASK-115.
Code fixes (R1/R2/R3) are wide and parallel; the schedule is dominated by the regulatory and
verification tail, not by the code findings.

## Process action (no task file)

Tighten the Definition-of-Done convention: a task may be marked Completed only when its acceptance
criteria name the verifying test(s) by path — response to the TASK-125 verification-integrity
finding (see report §Verification-process integrity).
