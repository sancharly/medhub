# Gap report — 2026-10-22

Scope: whole project  ·  Records scanned: 339  ·  Errors: 0  ·  Warnings: 96  ·  Safety class: B

> Note (2026-10-22, after QA approved TASK-159): re-running gives 98 warnings. The two extra
> are W5 findings from TASK-159 (now `approved`) to RISK-010 and RISK-012 (`in_review`); they
> clear when the human approves those records. Errors remain 0.

Generated with the `medical-records:traceability-check` fallback procedure (0.3.2) as a throwaway parser (no MedTrace tooling in the repository). `modified_after_approval` is not computed: only the MedTrace app can compute `approved_digest`.

Run for CR-001 TASK-159 (AC-18), after the TASK-159 record changes. Compared with
[gap-report-2026-10-21](gap-report-2026-10-21.md): the 35 `soup_anomaly_review_stale` findings are
gone (TASK-154), and so is the `soup_unintegrated` finding (SOUP-018, now `obsolete`; obsolete
records get no coverage findings). The W5 findings are new: they come from records that CR-001
returned to review.

## Triage

| Check | Count | Disposition |
|---|---|---|
| W5 | 87 | Expected. 86 of them are approved records (SRs, ADDs, RISKs, TASK-154/155/156, TP-001) linking to records that CR-001 put back to `in_review`: SOUP-001..017 and SOUP-019..035 (TASK-154), RISK-010 and TS-013 (TASK-159), RISK-012 (new). They clear when the human approves those records. The other one, TASK-132 → TASK-101 (draft), is pre-existing and is in the 2026-10-21 report |
| W1 / W2 / W7 | 3 / 4 / 1 | Pre-existing, unchanged since 2026-10-21. SR-017, SR-018 and SR-026 have no TS; SR-017, SR-018, SR-019 and SR-026 have no TR; TASK-073 implements SR-017. Not in CR-001's scope; SR-017 is related to PRB-048 |
| W3 | 1 | Expected. RISK-012 has no incoming `mitigates`: its controls are planned under CR-002 (human decision, 2026-10-22). No release before CR-002 |
| `soup_anomaly_review_stale` | 0 | CR-001 AC-18 met: every non-obsolete SOUP record has `anomaly_review: 2026-10-22` |
| `risk_not_acceptable` | 0 | RISK-010 (3 × 2) and RISK-012 (4 × 2) are `alarp`, and both have an "ALARP justification" section. Both justifications say the residual is not justified for a release until CR-002 |

`risk_control_unverified` reports nothing. The `mitigates` links of TASK-154..157 reach TR-001
only through SR-028 and SR-013. TR-001 is the migration-baseline report and predates CR-001, so the
CR-001 controls still need the release test report (CR-001 "Verification approach").

Cross-check: the scoped parser used by QA on earlier tasks (`trace.py`), run over the 68 records
CR-001 changed, also reports 0 errors. It differs in one respect: it applies the SOUP rules to the
obsolete SOUP-018 (`soup_unintegrated`, `soup_without_risk`, `soup_anomaly_review_stale`), while
this run skips obsolete records. CR-001 AC-18 scopes the staleness rule to non-obsolete records.

## Record inventory

| Type | Count |
|---|---|
| `user-need` | 15 |
| `nfr` | 9 |
| `regulatory-requirement` | 11 |
| `software-requirement` | 39 |
| `architecture-doc` | 24 |
| `task` | 124 |
| `test-specification` | 13 |
| `risk` | 12 |
| `test-plan` | 1 |
| `test-report` | 2 |
| `soup` | 35 |
| `problem-report` | 48 |
| `change-request` | 1 |
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
| W5 | 87 |
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
| W5 | ADD-005 | `docs/design-outputs/architecture/ADD-005-api-layer-routers.md` | approved, links to SOUP-001 (in_review) |
| W5 | ADD-005 | `docs/design-outputs/architecture/ADD-005-api-layer-routers.md` | approved, links to SOUP-002 (in_review) |
| W5 | ADD-005 | `docs/design-outputs/architecture/ADD-005-api-layer-routers.md` | approved, links to SOUP-003 (in_review) |
| W5 | ADD-005 | `docs/design-outputs/architecture/ADD-005-api-layer-routers.md` | approved, links to SOUP-004 (in_review) |
| W5 | ADD-005 | `docs/design-outputs/architecture/ADD-005-api-layer-routers.md` | approved, links to SOUP-005 (in_review) |
| W5 | ADD-005 | `docs/design-outputs/architecture/ADD-005-api-layer-routers.md` | approved, links to SOUP-006 (in_review) |
| W5 | ADD-005 | `docs/design-outputs/architecture/ADD-005-api-layer-routers.md` | approved, links to SOUP-007 (in_review) |
| W5 | ADD-005 | `docs/design-outputs/architecture/ADD-005-api-layer-routers.md` | approved, links to SOUP-017 (in_review) |
| W5 | ADD-005 | `docs/design-outputs/architecture/ADD-005-api-layer-routers.md` | approved, links to SOUP-024 (in_review) |
| W5 | ADD-006 | `docs/design-outputs/architecture/ADD-006-authentication-and-session.md` | approved, links to SOUP-011 (in_review) |
| W5 | ADD-006 | `docs/design-outputs/architecture/ADD-006-authentication-and-session.md` | approved, links to SOUP-012 (in_review) |
| W5 | ADD-006 | `docs/design-outputs/architecture/ADD-006-authentication-and-session.md` | approved, links to SOUP-013 (in_review) |
| W5 | ADD-006 | `docs/design-outputs/architecture/ADD-006-authentication-and-session.md` | approved, links to SOUP-021 (in_review) |
| W5 | ADD-008 | `docs/design-outputs/architecture/ADD-008-identity-and-account-lifecycle.md` | approved, links to SOUP-014 (in_review) |
| W5 | ADD-010 | `docs/design-outputs/architecture/ADD-010-appointments-and-notifications.md` | approved, links to SOUP-014 (in_review) |
| W5 | ADD-011 | `docs/design-outputs/architecture/ADD-011-clinical-records.md` | approved, links to SOUP-016 (in_review) |
| W5 | ADD-012 | `docs/design-outputs/architecture/ADD-012-attachment-service.md` | approved, links to SOUP-015 (in_review) |
| W5 | ADD-012 | `docs/design-outputs/architecture/ADD-012-attachment-service.md` | approved, links to SOUP-017 (in_review) |
| W5 | ADD-012 | `docs/design-outputs/architecture/ADD-012-attachment-service.md` | approved, links to SOUP-019 (in_review) |
| W5 | ADD-012 | `docs/design-outputs/architecture/ADD-012-attachment-service.md` | approved, links to SOUP-022 (in_review) |
| W5 | ADD-012 | `docs/design-outputs/architecture/ADD-012-attachment-service.md` | approved, links to SOUP-023 (in_review) |
| W5 | ADD-013 | `docs/design-outputs/architecture/ADD-013-audit-service.md` | approved, links to SOUP-008 (in_review) |
| W5 | ADD-014 | `docs/design-outputs/architecture/ADD-014-module-host-plugin-registry.md` | approved, links to SOUP-002 (in_review) |
| W5 | ADD-015 | `docs/design-outputs/architecture/ADD-015-dicom-module-backend.md` | approved, links to SOUP-015 (in_review) |
| W5 | ADD-016 | `docs/design-outputs/architecture/ADD-016-persistence.md` | approved, links to SOUP-006 (in_review) |
| W5 | ADD-016 | `docs/design-outputs/architecture/ADD-016-persistence.md` | approved, links to SOUP-008 (in_review) |
| W5 | ADD-016 | `docs/design-outputs/architecture/ADD-016-persistence.md` | approved, links to SOUP-009 (in_review) |
| W5 | ADD-016 | `docs/design-outputs/architecture/ADD-016-persistence.md` | approved, links to SOUP-010 (in_review) |
| W5 | ADD-016 | `docs/design-outputs/architecture/ADD-016-persistence.md` | approved, links to SOUP-011 (in_review) |
| W5 | ADD-016 | `docs/design-outputs/architecture/ADD-016-persistence.md` | approved, links to SOUP-020 (in_review) |
| W5 | ADD-017 | `docs/design-outputs/architecture/ADD-017-async-worker.md` | approved, links to SOUP-013 (in_review) |
| W5 | ADD-017 | `docs/design-outputs/architecture/ADD-017-async-worker.md` | approved, links to SOUP-014 (in_review) |
| W5 | ADD-017 | `docs/design-outputs/architecture/ADD-017-async-worker.md` | approved, links to SOUP-021 (in_review) |
| W5 | ADD-018 | `docs/design-outputs/architecture/ADD-018-frontend-app-shell.md` | approved, links to SOUP-024 (in_review) |
| W5 | ADD-018 | `docs/design-outputs/architecture/ADD-018-frontend-app-shell.md` | approved, links to SOUP-025 (in_review) |
| W5 | ADD-018 | `docs/design-outputs/architecture/ADD-018-frontend-app-shell.md` | approved, links to SOUP-026 (in_review) |
| W5 | ADD-018 | `docs/design-outputs/architecture/ADD-018-frontend-app-shell.md` | approved, links to SOUP-027 (in_review) |
| W5 | ADD-018 | `docs/design-outputs/architecture/ADD-018-frontend-app-shell.md` | approved, links to SOUP-029 (in_review) |
| W5 | ADD-018 | `docs/design-outputs/architecture/ADD-018-frontend-app-shell.md` | approved, links to SOUP-030 (in_review) |
| W5 | ADD-018 | `docs/design-outputs/architecture/ADD-018-frontend-app-shell.md` | approved, links to SOUP-031 (in_review) |
| W5 | ADD-018 | `docs/design-outputs/architecture/ADD-018-frontend-app-shell.md` | approved, links to SOUP-032 (in_review) |
| W5 | ADD-018 | `docs/design-outputs/architecture/ADD-018-frontend-app-shell.md` | approved, links to SOUP-034 (in_review) |
| W5 | ADD-018 | `docs/design-outputs/architecture/ADD-018-frontend-app-shell.md` | approved, links to SOUP-035 (in_review) |
| W5 | ADD-019 | `docs/design-outputs/architecture/ADD-019-frontend-auth-session-ui.md` | approved, links to SOUP-025 (in_review) |
| W5 | ADD-019 | `docs/design-outputs/architecture/ADD-019-frontend-auth-session-ui.md` | approved, links to SOUP-027 (in_review) |
| W5 | ADD-019 | `docs/design-outputs/architecture/ADD-019-frontend-auth-session-ui.md` | approved, links to SOUP-028 (in_review) |
| W5 | ADD-020 | `docs/design-outputs/architecture/ADD-020-frontend-core-views.md` | approved, links to SOUP-025 (in_review) |
| W5 | ADD-020 | `docs/design-outputs/architecture/ADD-020-frontend-core-views.md` | approved, links to SOUP-028 (in_review) |
| W5 | ADD-020 | `docs/design-outputs/architecture/ADD-020-frontend-core-views.md` | approved, links to SOUP-029 (in_review) |
| W5 | ADD-021 | `docs/design-outputs/architecture/ADD-021-frontend-module-registry.md` | approved, links to SOUP-025 (in_review) |
| W5 | ADD-021 | `docs/design-outputs/architecture/ADD-021-frontend-module-registry.md` | approved, links to SOUP-027 (in_review) |
| W5 | ADD-023 | `docs/design-outputs/architecture/ADD-023-frontend-api-client.md` | approved, links to SOUP-028 (in_review) |
| W5 | ADD-023 | `docs/design-outputs/architecture/ADD-023-frontend-api-client.md` | approved, links to SOUP-033 (in_review) |
| W5 | RISK-001 | `docs/risks/RISK-001-unauthorized-clinical-data-disclosure.md` | approved, links to SOUP-002 (in_review) |
| W5 | RISK-001 | `docs/risks/RISK-001-unauthorized-clinical-data-disclosure.md` | approved, links to SOUP-003 (in_review) |
| W5 | RISK-002 | `docs/risks/RISK-002-clinical-data-misattribution.md` | approved, links to SOUP-008 (in_review) |
| W5 | RISK-002 | `docs/risks/RISK-002-clinical-data-misattribution.md` | approved, links to SOUP-016 (in_review) |
| W5 | RISK-002 | `docs/risks/RISK-002-clinical-data-misattribution.md` | approved, links to SOUP-020 (in_review) |
| W5 | RISK-003 | `docs/risks/RISK-003-incorrect-dicom-rendering.md` | approved, links to SOUP-015 (in_review) |
| W5 | RISK-005 | `docs/risks/RISK-005-account-takeover.md` | approved, links to SOUP-003 (in_review) |
| W5 | RISK-005 | `docs/risks/RISK-005-account-takeover.md` | approved, links to SOUP-012 (in_review) |
| W5 | RISK-005 | `docs/risks/RISK-005-account-takeover.md` | approved, links to SOUP-013 (in_review) |
| W5 | RISK-005 | `docs/risks/RISK-005-account-takeover.md` | approved, links to SOUP-021 (in_review) |
| W5 | RISK-005 | `docs/risks/RISK-005-account-takeover.md` | approved, links to SOUP-024 (in_review) |
| W5 | RISK-006 | `docs/risks/RISK-006-incomplete-audit-trail.md` | approved, links to SOUP-008 (in_review) |
| W5 | RISK-006 | `docs/risks/RISK-006-incomplete-audit-trail.md` | approved, links to SOUP-020 (in_review) |
| W5 | RISK-007 | `docs/risks/RISK-007-clinical-information-unavailable.md` | approved, links to SOUP-014 (in_review) |
| W5 | RISK-007 | `docs/risks/RISK-007-clinical-information-unavailable.md` | approved, links to SOUP-019 (in_review) |
| W5 | RISK-007 | `docs/risks/RISK-007-clinical-information-unavailable.md` | approved, links to SOUP-020 (in_review) |
| W5 | RISK-007 | `docs/risks/RISK-007-clinical-information-unavailable.md` | approved, links to SOUP-021 (in_review) |
| W5 | RISK-007 | `docs/risks/RISK-007-clinical-information-unavailable.md` | approved, links to SOUP-022 (in_review) |
| W5 | RISK-008 | `docs/risks/RISK-008-personal-data-lifecycle-failure.md` | approved, links to SOUP-014 (in_review) |
| W5 | RISK-009 | `docs/risks/RISK-009-notification-not-delivered.md` | approved, links to SOUP-014 (in_review) |
| W5 | RISK-009 | `docs/risks/RISK-009-notification-not-delivered.md` | approved, links to SOUP-021 (in_review) |
| W5 | RISK-011 | `docs/risks/RISK-011-encryption-key-management-failure.md` | approved, links to SOUP-011 (in_review) |
| W5 | RISK-011 | `docs/risks/RISK-011-encryption-key-management-failure.md` | approved, links to SOUP-019 (in_review) |
| W5 | RISK-011 | `docs/risks/RISK-011-encryption-key-management-failure.md` | approved, links to SOUP-022 (in_review) |
| W5 | SR-001 | `docs/design-inputs/software-requirements/SR-001-browser-accessible-web-application-over-https.md` | approved, links to RISK-010 (in_review) |
| W5 | SR-022 | `docs/design-inputs/software-requirements/SR-022-encryption-in-transit-and-at-rest.md` | approved, links to RISK-010 (in_review) |
| W5 | SR-025 | `docs/design-inputs/software-requirements/SR-025-password-complexity-policy.md` | approved, links to RISK-010 (in_review) |
| W5 | SR-028 | `docs/design-inputs/software-requirements/SR-028-traceable-version-controlled-development-records.md` | approved, links to RISK-010 (in_review) |
| W5 | TASK-132 | `docs/design-outputs/tasks/TASK-132-clinical-entries-view-completeness-remediation.md` | approved, links to TASK-101 (draft) |
| W5 | TASK-154 | `docs/design-outputs/tasks/TASK-154-soup-anomaly-list-review.md` | approved, links to RISK-010 (in_review) |
| W5 | TASK-154 | `docs/design-outputs/tasks/TASK-154-soup-anomaly-list-review.md` | approved, links to RISK-012 (in_review) |
| W5 | TASK-155 | `docs/design-outputs/tasks/TASK-155-pin-container-images-by-tag-and-digest.md` | approved, links to RISK-010 (in_review) |
| W5 | TASK-156 | `docs/design-outputs/tasks/TASK-156-ci-image-pin-check.md` | approved, links to RISK-010 (in_review) |
| W5 | TP-001 | `docs/test-plans-reports/plans/TP-001-verification-plan-migration-baseline.md` | approved, links to TS-013 (in_review) |
| W7 | TASK-073 | `docs/design-outputs/tasks/TASK-073-dicom-module-backend-authorized-bytes.md` | approved TASK; implemented SR-017 has no TS |
