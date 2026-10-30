# Gap report — 2026-10-30

Scope: whole project  ·  Records scanned: 350  ·  Errors: 0  ·  Warnings: 50  ·  Safety class: B

Generated with the `medical-records:traceability-check` fallback procedure (0.3.2) as a throwaway parser (no MedTrace tooling in the repository). `modified_after_approval` is not computed: only the MedTrace app can compute `approved_digest`. The parser applies the E1..E10 checks, W1..W7 and the class-B gated rules, and skips obsolete records for the coverage rules, as the 2026-10-22 run did.

Run for CR-003 TASK-168 (Checkpoint B, AC-19), on branch `bug/soup-upgrades` at commit `d57ec72` plus the TASK-168 record changes (TASK-168 `in_review`; TS-013, CR-003, PRB-045 and PRB-049 text edits; this report). Compared with [gap-report-2026-10-22](gap-report-2026-10-22.md): the W5 count falls from 87 to 40 because the 2026-10-23 design review approved the CR-001 records. The 40 now come from CR-003: the records it put back to `in_review`.

## Triage

| Check | Count | Disposition |
|---|---|---|
| W5 | 40 | Expected under CR-003 AC-19: approved records link to records that CR-003 holds at `in_review` until the human approves them. SOUP-021 (7), SOUP-003 (5), SOUP-011 (4), SOUP-019 (4), RISK-011 (5), TS-001..013 (13, all from TP-001), ADD-023 (1, from TASK-166). One W5 is pre-existing: TASK-132 → TASK-101 (draft), in the 2026-10-21 and 2026-10-22 reports. They clear when the human approves the CR-003 records |
| W6 | 1 | Intended (CR-003 decision D-6): TASK-165 keeps its `relates_to` link to SOUP-033, now `obsolete`. TASK-165 is the only non-obsolete record that links SOUP-033 |
| W1 / W2 / W7 | 3 / 4 / 1 | Pre-existing, unchanged since 2026-10-22: SR-017, SR-018, SR-026 have no TS; SR-017, SR-018, SR-019, SR-026 have no TR; TASK-073 implements SR-017. Not in CR-003's scope (SR-017 relates to PRB-048) |
| W3 | 1 | Unchanged: RISK-012 has no incoming `mitigates`; its controls are planned under CR-002 (human decision, 2026-10-22) |
| `soup_anomaly_review_stale` | 0 | CR-003 AC-19 met: every non-obsolete SOUP record has an `anomaly_review` within 365 days (SOUP-003, 011, 019, 021: 2026-10-29; the other 29 non-obsolete: 2026-10-22). SOUP-018 and SOUP-033 are `obsolete` and are skipped |
| `soup_without_risk`, `soup_unintegrated` | 0 | The transient `soup_without_risk` finding on SOUP-033 (seen in the QA runs of TASK-161..164) is gone: SOUP-033 is `obsolete` since TASK-165 |
| `risk_not_acceptable`, `risk_unscored` | 0 | RISK-010 (3 × 2) and RISK-012 (4 × 2) are `alarp`, both with an "ALARP justification" section; every `acceptability` equals the value `risk_matrix` derives from the residual scores |
| `risk_control_unverified` | 0 | Reached through SR-028 / TR-001 and the other SRs' TRs, as in 2026-10-22. TR-001 is the migration-baseline report and predates CR-001 and CR-003: the controls these CRs re-implemented still need the release test report |
| `release_tag_missing`, E10 | 0 | No `release` element exists. No `critical` PRB is open |

Observations for the human (not findings):

- RISK-010 is `approved` (1.4, self-approved 2026-10-29, `approved_digest` cedf412b…022d). The CR-003 plan expected it at `in_review` (AC-19); the approval was recorded before TASK-168 confirmed the PRB-035 statement. The file has not changed since the approval commit (3443d03), and TASK-168 changes nothing in it. The parser cannot compute the digest.
- The records cite CR-002 in prose (RISK-010, CR-001, CR-003). No CR-002 record exists yet. Those are text references, not links, so there is no E7 finding.

## Record inventory

| Type | Count |
|---|---|
| `user-need` | 15 |
| `nfr` | 9 |
| `regulatory-requirement` | 11 |
| `software-requirement` | 39 |
| `architecture-doc` | 24 |
| `task` | 132 |
| `test-specification` | 13 |
| `risk` | 12 |
| `test-plan` | 1 |
| `test-report` | 2 |
| `soup` | 35 |
| `problem-report` | 50 |
| `change-request` | 2 |
| `lifecycle-plan` | 5 |
| `release` | 0 |
| `source-ref` | 0 |

## Errors

None.

## Warnings and class-gated findings

| Check | Count |
|---|---|
| W1 | 3 |
| W2 | 4 |
| W3 | 1 |
| W5 | 40 |
| W6 | 1 |
| W7 | 1 |

| Check | Element | File | Problem |
|---|---|---|---|
| W1 | SR-017 | `docs/design-inputs/software-requirements/SR-017-dicom-image-opening-and-rendering.md` | no TS verifies this SR |
| W1 | SR-018 | `docs/design-inputs/software-requirements/SR-018-dicom-viewer-controls.md` | no TS verifies this SR |
| W1 | SR-026 | `docs/design-inputs/software-requirements/SR-026-performance-budgets-for-routine-operations.md` | no TS verifies this SR |
| W2 | SR-017 | `docs/design-inputs/software-requirements/SR-017-dicom-image-opening-and-rendering.md` | no TR verifies this SR |
| W2 | SR-018 | `docs/design-inputs/software-requirements/SR-018-dicom-viewer-controls.md` | no TR verifies this SR |
| W2 | SR-019 | `docs/design-inputs/software-requirements/SR-019-cross-browser-support.md` | no TR verifies this SR |
| W2 | SR-026 | `docs/design-inputs/software-requirements/SR-026-performance-budgets-for-routine-operations.md` | no TR verifies this SR |
| W3 | RISK-012 | `docs/risks/RISK-012-object-store-compromised-or-unpatchable.md` | no incoming mitigates |
| W5 | ADD-005 | `docs/design-outputs/architecture/ADD-005-api-layer-routers.md` | approved, links to SOUP-003 (in_review) |
| W5 | ADD-006 | `docs/design-outputs/architecture/ADD-006-authentication-and-session.md` | approved, links to SOUP-011 (in_review) |
| W5 | ADD-006 | `docs/design-outputs/architecture/ADD-006-authentication-and-session.md` | approved, links to SOUP-021 (in_review) |
| W5 | ADD-012 | `docs/design-outputs/architecture/ADD-012-attachment-service.md` | approved, links to RISK-011 (in_review) |
| W5 | ADD-012 | `docs/design-outputs/architecture/ADD-012-attachment-service.md` | approved, links to SOUP-019 (in_review) |
| W5 | ADD-016 | `docs/design-outputs/architecture/ADD-016-persistence.md` | approved, links to RISK-011 (in_review) |
| W5 | ADD-016 | `docs/design-outputs/architecture/ADD-016-persistence.md` | approved, links to SOUP-011 (in_review) |
| W5 | ADD-017 | `docs/design-outputs/architecture/ADD-017-async-worker.md` | approved, links to SOUP-021 (in_review) |
| W5 | RISK-001 | `docs/risks/RISK-001-unauthorized-clinical-data-disclosure.md` | approved, links to SOUP-003 (in_review) |
| W5 | RISK-005 | `docs/risks/RISK-005-account-takeover.md` | approved, links to SOUP-021 (in_review) |
| W5 | RISK-005 | `docs/risks/RISK-005-account-takeover.md` | approved, links to SOUP-003 (in_review) |
| W5 | RISK-007 | `docs/risks/RISK-007-clinical-information-unavailable.md` | approved, links to SOUP-019 (in_review) |
| W5 | RISK-007 | `docs/risks/RISK-007-clinical-information-unavailable.md` | approved, links to SOUP-021 (in_review) |
| W5 | RISK-009 | `docs/risks/RISK-009-notification-not-delivered.md` | approved, links to SOUP-021 (in_review) |
| W5 | RISK-010 | `docs/risks/RISK-010-unreviewed-soup-change.md` | approved, links to SOUP-003 (in_review) |
| W5 | RISK-010 | `docs/risks/RISK-010-unreviewed-soup-change.md` | approved, links to SOUP-011 (in_review) |
| W5 | RISK-010 | `docs/risks/RISK-010-unreviewed-soup-change.md` | approved, links to SOUP-019 (in_review) |
| W5 | RISK-010 | `docs/risks/RISK-010-unreviewed-soup-change.md` | approved, links to SOUP-021 (in_review) |
| W5 | SR-001 | `docs/design-inputs/software-requirements/SR-001-browser-accessible-web-application-over-https.md` | approved, links to RISK-011 (in_review) |
| W5 | SR-022 | `docs/design-inputs/software-requirements/SR-022-encryption-in-transit-and-at-rest.md` | approved, links to RISK-011 (in_review) |
| W5 | TASK-132 | `docs/design-outputs/tasks/TASK-132-clinical-entries-view-completeness-remediation.md` | approved, links to TASK-101 (draft) |
| W5 | TASK-161 | `docs/design-outputs/tasks/TASK-161-move-redis-to-7-4-12-on-debian-12.md` | approved, links to SOUP-021 (in_review) |
| W5 | TASK-163 | `docs/design-outputs/tasks/TASK-163-upgrade-cryptography-with-known-answer-test.md` | approved, links to RISK-011 (in_review) |
| W5 | TASK-163 | `docs/design-outputs/tasks/TASK-163-upgrade-cryptography-with-known-answer-test.md` | approved, links to SOUP-011 (in_review) |
| W5 | TASK-164 | `docs/design-outputs/tasks/TASK-164-upgrade-anyio-and-urllib3.md` | approved, links to SOUP-003 (in_review) |
| W5 | TASK-164 | `docs/design-outputs/tasks/TASK-164-upgrade-anyio-and-urllib3.md` | approved, links to SOUP-019 (in_review) |
| W5 | TASK-166 | `docs/design-outputs/tasks/TASK-166-correct-add-023-api-client-description.md` | approved, links to ADD-023 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-001 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-002 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-003 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-004 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-005 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-006 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-007 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-008 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-009 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-010 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-011 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-012 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-013 (in_review) |
| W6 | TASK-165 | `docs/design-outputs/tasks/TASK-165-remove-unused-openapi-fetch.md` | links to SOUP-033 (obsolete) |
| W7 | TASK-073 | `docs/design-outputs/tasks/TASK-073-dicom-module-backend-authorized-bytes.md` | approved TASK; implemented SR-017 has no TS |

## Coverage

One row per SR. TASKs and ADDs are counts of the records that `implements` the SR; TS, TR and RISKs are IDs.

| SR | Status | Satisfies | TASKs | ADDs | TS | TR | RISKs mitigated |
|---|---|---|---|---|---|---|---|
| SR-001 | approved | RR-003, UN-001, NFR-007 | 3 | 3 | TS-011 | TR-001, TR-002 | RISK-005, RISK-010, RISK-011 |
| SR-002 | approved | RR-003, UN-002, NFR-007 | 5 | 2 | TS-001 | TR-001, TR-002 | — |
| SR-003 | approved | UN-002, NFR-004 | 6 | 3 | TS-003 | TR-002 | RISK-002 |
| SR-004 | approved | UN-003 | 3 | 4 | TS-003 | TR-002 | RISK-002 |
| SR-005 | approved | RR-001, UN-003, UN-004, UN-006, NFR-004 | 7 | 2 | TS-002 | TR-001, TR-002 | RISK-001 |
| SR-006 | approved | RR-001, UN-004 | 6 | 3 | TS-002 | TR-001, TR-002 | RISK-001 |
| SR-007 | approved | RR-001, UN-005, NFR-004 | 4 | 3 | TS-002 | TR-001, TR-002 | RISK-001 |
| SR-008 | approved | RR-001, UN-005, NFR-004 | 4 | 3 | TS-002 | TR-001, TR-002 | RISK-001, RISK-004 |
| SR-009 | approved | RR-001, UN-006, NFR-004 | 3 | 2 | TS-002 | TR-001, TR-002 | RISK-001 |
| SR-010 | approved | UN-007 | 4 | 2 | TS-006 | TR-002 | — |
| SR-011 | approved | UN-007 | 3 | 3 | TS-002 | TR-001, TR-002 | RISK-009 |
| SR-012 | approved | UN-008 | 5 | 3 | TS-007 | TR-001, TR-002 | RISK-002 |
| SR-013 | approved | UN-008 | 10 | 2 | TS-007 | TR-001, TR-002 | RISK-002 |
| SR-014 | approved | UN-009 | 6 | 2 | TS-005 | TR-001, TR-002 | — |
| SR-015 | approved | UN-009, UN-010 | 9 | 4 | TS-005 | TR-001, TR-002 | — |
| SR-016 | approved | UN-010 | 10 | 4 | TS-010 | TR-001, TR-002 | — |
| SR-017 | approved | RR-009, UN-011, NFR-005 | 3 | 3 | — | — | RISK-003 |
| SR-018 | approved | UN-011, NFR-005 | 1 | 1 | — | — | RISK-003 |
| SR-019 | approved | RR-010, NFR-001 | 1 | 1 | TS-012 | — | RISK-003 |
| SR-020 | approved | RR-009, NFR-003 | 1 | 1 | TS-012 | TR-001, TR-002 | — |
| SR-021 | approved | NFR-002 | 1 | 2 | TS-008 | TR-002 | RISK-002 |
| SR-022 | approved | RR-003, NFR-004, NFR-007 | 5 | 3 | TS-008 | TR-001, TR-002 | RISK-006, RISK-007, RISK-008, RISK-010, RISK-011 |
| SR-023 | approved | RR-004, NFR-004, NFR-007, NFR-005 | 6 | 2 | TS-009 | TR-002 | RISK-001, RISK-004, RISK-005, RISK-006 |
| SR-024 | approved | RR-002, RR-005, NFR-004 | 8 | 2 | TS-004 | TR-001, TR-002 | RISK-002, RISK-008 |
| SR-025 | approved | RR-003, NFR-007 | 6 | 2 | TS-001 | TR-001, TR-002 | RISK-005, RISK-010 |
| SR-026 | approved | RR-010, NFR-008 | 4 | 3 | — | — | RISK-007 |
| SR-027 | approved | RR-009, NFR-009 | 6 | 1 | TS-012 | TR-001, TR-002 | — |
| SR-028 | approved | RR-006, RR-007, RR-008, RR-010, NFR-005, NFR-006 | 20 | 3 | TS-013 | TR-001, TR-002 | RISK-007, RISK-010 |
| SR-029 | approved | RR-003, NFR-007 | 6 | 1 | TS-001 | TR-001, TR-002 | RISK-005 |
| SR-030 | approved | RR-003, NFR-007 | 10 | 3 | TS-001 | TR-001, TR-002 | RISK-005 |
| SR-031 | approved | RR-003, NFR-007 | 15 | 3 | TS-008, TS-011 | TR-002 | RISK-003, RISK-005 |
| SR-032 | approved | UN-012, UN-003 | 6 | 1 | TS-003 | TR-001, TR-002 | — |
| SR-033 | approved | UN-012, NFR-007 | 7 | 3 | TS-003 | TR-001, TR-002 | RISK-009 |
| SR-034 | approved | RR-002, UN-012, NFR-004, NFR-007 | 8 | 3 | TS-003 | TR-001, TR-002 | — |
| SR-035 | approved | UN-013, UN-007 | 9 | 3 | TS-006 | TR-001, TR-002 | RISK-009 |
| SR-036 | approved | RR-001, UN-013, UN-005, NFR-004 | 6 | 3 | TS-002 | TR-001, TR-002 | RISK-001, RISK-004 |
| SR-037 | approved | UN-014, NFR-009 | 4 | 1 | TS-012 | TR-001, TR-002 | — |
| SR-038 | approved | UN-015, UN-014, NFR-009, NFR-003 | 5 | 1 | TS-012 | TR-001, TR-002 | — |
| SR-039 | approved | UN-015, NFR-009 | 2 | 1 | TS-012 | TR-001, TR-002 | — |
