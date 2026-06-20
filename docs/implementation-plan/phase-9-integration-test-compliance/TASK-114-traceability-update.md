# TASK-114 — Traceability matrix completion (TASK → system-test column)

- **Phase:** 9 — Integration, system testing, compliance hardening
- **Software item / unit:** (process) — completes the requirement→design→task→test record
- **Implements:** SR-028 (AC-2 bidirectional traceability; AC-4 each SR traced to ≥1 system test), NFR-006 (AC-3 requirements traceable through to tests; AC-4 all SRs traced to ≥1 system test before release); ADR-0011 (process controls)
- **Depends on:** **all** prior tasks — the matrix can only be completed once every SR/NFR has its implementing task(s) and verifying test(s); in particular TASK-110 (integration tests) and TASK-111 (system/E2E tests) provide the test column
- **Branch:** `enabler-story/traceability-completion`
- **Status:** Not started

## Objective

Complete [docs/design/traceability-matrix.md](../../design/traceability-matrix.md) by adding the **TASK → system-test** dimension so that every software requirement and NFR traces the full chain **requirement → design (item/ADR/artifact) → implementing TASK → verifying test**. The matrix today carries the architecture-side trace (SR/NFR → software item(s) → ADR(s) → artifact); this task adds the implementation-and-verification columns, closing the IEC 62304 bidirectional-traceability obligation and the "every SR traced to ≥1 system test before release" rule (SR-028.2/4, NFR-006.3/4). It edits one design document plus the per-task matrix rows; it writes no application code.

## Interfaces to honor

- The matrix is the single controlled traceability record (§09 / ADR-0011 process controls); it must remain consistent with the requirement files (`docs/design-inputs/`), the building-block items (§05), the ADRs (`docs/design/adr/`), and the task index ([implementation-plan/README.md](../README.md)).
- The **test** column references the actual verifying tests: the TASK-110 integration tests (§06 flows) and the TASK-111 tagged Playwright system tests (per-SR), plus TASK-112 (SR-026/NFR-008 budgets) and TASK-113 (SR-031/NFR-007 review evidence).
- Each task file's Definition-of-Done already requires "Traceability matrix row updated"; this task is the **final reconciliation** that verifies no row is missing and the test column is complete for **every** SR/NFR.

This task must **not**: invent a test that does not exist (a gap must be filled by adding a test in TASK-110/111, not by a paper entry); alter requirement files, the dev plan, the README, or the template; change the architecture-side columns except to correct a demonstrated inconsistency.

## Implementation detail

- Files to modify:
  - `docs/design/traceability-matrix.md` — extend the SR table (and add/extend the NFR table) with two columns: **TASK(s)** (the implementing task id[s] from the plan) and **System test(s)** (the verifying test reference — integration test name from TASK-110 and/or tagged E2E spec from TASK-111; TASK-112 for SR-026/NFR-008; TASK-113 for SR-031/NFR-007). Confirms the existing requirement → item → ADR → artifact chain is intact for each row.
- Method:
  - Cross-walk all 36 SRs and 9 NFRs against the task index (README "Full task index") so every requirement has at least one implementing TASK, and against the TASK-111 SR-AC→test report so every SR has at least one system test (SR-028.4, NFR-006.4).
  - Resolve any gap by flagging it for the owning task (a missing test is fixed in TASK-110/111, not papered over here).
  - Verify bidirectional links: every SR cites its origin UN/NFR (already in the requirement files) and now points forward to TASK and test (SR-028.2).
- Coverage check: the README "Coverage" note states all 56 units map to a task and all 36 SRs + 9 NFRs are covered; this task is where that claim is **verified** by the completed test column (the README itself is **not** edited).
- The completed matrix is the release-gate artifact: "all software requirements traced to at least one system test before release" (NFR-006.4) is demonstrably true when this table is full and green.

## Tests (write first — TDD, CLAUDE.md §4)

Verification is by an automated consistency check rather than runtime tests:

- `docs/design/check_traceability.py` (or a CI lint step, extending TASK-005) that parses the requirement ids from `docs/design-inputs/`, the task ids from the implementation plan, and the tagged-test report from TASK-111, then asserts: every SR/NFR row exists, every row has ≥1 TASK and ≥1 system test, and no referenced test/task id is dangling (SR-028.4, NFR-006.4). The check fails CI if any requirement lacks a traced system test.
- The check names SR-028 / NFR-006 as the criteria it enforces.

## Acceptance criteria

- [ ] Every SR and NFR row carries its implementing TASK(s) and verifying system test(s) (SR-028.2/4, NFR-006.3/4).
- [ ] Every software requirement is traced to at least one system test that exists (TASK-110/111/112/113) (SR-028.4, NFR-006.4).
- [ ] The requirement → item → ADR → artifact → TASK → test chain is complete and internally consistent.
- [ ] An automated consistency check gates CI and fails on any untraced requirement or dangling reference.
- [ ] Requirement files, dev plan, README, and template are unchanged.

## Definition of Done

- [ ] Lint + type-check pass on the consistency-check script (`ruff`)
- [ ] Consistency check passes in CI — no untraced SR/NFR, no dangling task/test reference
- [ ] OpenAPI regenerated and re-linted (N/A)
- [ ] Audit events: N/A (documentation artifact)
- [ ] Traceability matrix **completed** — this task is the completion; SR-028 / NFR-006 row updated to point at TASK-114 + the check
- [ ] Security review N/A
