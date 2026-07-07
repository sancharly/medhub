---
id: "TASK-112"
type: task
title: "Performance validation against the budgets"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-026"
    relation: implements
  - target: "NFR-008"
    relation: implements
  - target: "TASK-111"
    relation: relates_to
  - target: "TASK-004"
    relation: relates_to
tags: ["phase:9-integration-system-testing-compliance"]
---

- **Phase:** 9 — Integration, system testing, compliance hardening
- **Software item / unit:** (system-level) — SI-API, SI-ATTACH, SI-MOD-DICOM-FE under load
- **Implements:** SR-026 (AC-1 routine ops < 3 s; AC-2 save clinical entry < 3 s; AC-3 DICOM initial image < 10 s; AC-4 verified by performance/system tests), NFR-008; under the §10 "normal load" working assumption
- **Depends on:** TASK-111 (the E2E flows and seed fixtures these load tests reuse) must be merged first; runs against the full deployed stack (TASK-004)
- **Branch:** `enabler-story/performance-validation`
- **Status:** Not started

## Objective

Build the **performance/load validation** that asserts MedHub meets its response-time budgets **under the assumed normal load**: routine interactive operations complete in **< 3 s** and the **initial** DICOM image renders in **< 10 s** for a typical study (SR-026, NFR-008). The concrete load figures are the labeled **MVP working assumption** in [10-quality-requirements.md](../../design/10-quality-requirements.md) ("normal load"): **≈50 concurrent active users (peak ~100), ~10 req/s (peak ~25), CT/MRI ~150–300 slices ~50–150 MB, up to ~500 clinical entries per patient, single 4 vCPU / 8–16 GB host**. These are engineering assumptions pending stakeholder confirmation; revising them changes only the thresholds here, not the architecture (§10). The task produces a repeatable load profile and a pass/fail report against the budgets.

## Interfaces to honor

- Measures the **external HTTP/SPA interface** only — page navigation, listings, save-entry, and DICOM first-image — as a user experiences them.
- "Initial rendered image < 10 s" is the **first slice/image**, not the full volume (SR-026.3, ADR-0008): the measurement point is first-image-rendered, consistent with the progressive-load design (TASK-102, §8.9).
- "Save a clinical entry < 3 s" **excludes** large file-upload time (SR-026.2) — the measured operation is the entry-save round-trip, not the attachment byte transfer.
- Load is generated against the same authorized endpoints real clients use; sessions are established via the real login flow (no auth bypass).

Tests must **not**: measure against a stubbed backend or in-memory store (run against the deployed Postgres/Redis/object-store stack); count attachment-upload bytes toward the save-entry budget; assert full-volume DICOM load against the 10 s budget (that budget is first-image only).

## Implementation detail

- Files to create under `backend/tests/performance/` (and/or `infra/perf/`):
  - `load_profile.py` (or `k6`/`locust` script) — models the §10 load: ~50 concurrent virtual users at ~10 req/s sustained with a ~25 req/s peak, mixing the routine operations (login, profile, list appointments, list clinical entries, save clinical entry) across user types.
  - `routine_ops_budget.*` — drives page-nav and data-listing operations (profile, appointments, clinical-entry listing for a patient seeded with ~500 entries) and asserts the **p95** completes < 3 s under the concurrent load (SR-026.1, NFR-008.1).
  - `save_entry_budget.*` — asserts saving a clinical entry (excluding upload) completes < 3 s (SR-026.2, NFR-008.2).
  - `dicom_first_image_budget.*` — measures time-to-first-rendered-image for a typical CT/MRI study (~150–300 slices, ~50–150 MB) and a single X-ray, asserting < 10 s (SR-026.3, NFR-008.3). Front-end timing captured via the TASK-111 Playwright harness (performance marks at first-image-rendered) so the budget reflects real WebGL rendering, not just byte arrival.
  - `thresholds.yaml` — the budget thresholds and the §10 load parameters in one place, labeled as the pending-confirmation assumption so a stakeholder revision is a config edit (§10).
  - `report/` — generated latency-distribution + pass/fail report per run (the SR-026.4 verification artifact).
- Tooling (consistent with the stack and CI from TASK-005): a load generator (`k6` or `locust`) for the API budgets; the TASK-111 Playwright harness with the Performance API for DICOM first-image timing.
- Environment: run against the single-host Docker Compose deployment (ADR-0010) sized per the §10 assumption so results reflect the MVP target host; record the host spec in the report.
- The run is wired into CI (or a scheduled performance job) and fails if any budget's p95 exceeds its threshold (SR-026.4).
- Mitigations the design relies on to meet budgets (asserted indirectly by the budgets holding): object storage off the DB path, client-side DICOM rendering, progressive slice load, lazy module chunks, indexed consent/authorization queries (§8.9).

## Tests (write first — TDD, CLAUDE.md §4)

This task is the performance test suite. The thresholds (3 s routine, 3 s save-entry, 10 s DICOM first-image) and the §10 load profile are encoded first as failing assertions, then verified against the deployed stack. Cases: routine listings under concurrency with the ~500-entry patient (SR-026.1); save-entry excluding upload (SR-026.2); DICOM first-image for CT/MRI and X-ray (SR-026.3). Each assertion names the SR-026 AC it verifies.

## Acceptance criteria

- [ ] Routine page-nav and data-listing operations meet < 3 s (p95) under the §10 concurrent load (SR-026.1, NFR-008.1).
- [ ] Saving a clinical entry (excluding upload) meets < 3 s (SR-026.2, NFR-008.2).
- [ ] DICOM initial rendered image meets < 10 s for a typical study, measured at first-image-rendered (SR-026.3, NFR-008.3).
- [ ] The load profile reflects the §10 assumption (≈50 concurrent users, ~10 req/s sustained, ~25 peak; study sizes as stated) and is parameterized for stakeholder revision.
- [ ] A latency/pass-fail report is produced as the SR-026.4 verification artifact and the run gates CI.

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`eslint` as applicable to the harness)
- [ ] Performance suite runs against the deployed stack and all budgets pass at the §10 load
- [ ] OpenAPI regenerated and re-linted (N/A)
- [ ] Audit events: N/A (read-mostly load; no new security action)
- [ ] Traceability matrix rows updated (SR-026, NFR-008 → TASK-112 → budget tests + report)
- [ ] Security review N/A
