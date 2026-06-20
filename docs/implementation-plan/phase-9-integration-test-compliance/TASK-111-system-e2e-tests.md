# TASK-111 — System / end-to-end tests (Playwright) + cross-browser pass

- **Phase:** 9 — Integration, system testing, compliance hardening
- **Software item / unit:** (system-level) — full stack via the SPA against the running backend
- **Implements:** SR-028 (AC-4 every SR traced to at least one system test), SR-019 (AC-1/2/3 cross-browser, layout intact, documented pass per release); exercises the acceptance criteria of every functional SR; ADR-0003 (browser matrix), ADR-0008 (WebGL DICOM)
- **Depends on:** TASK-102 (DICOM viewport), TASK-103 (viewer controls), TASK-090–096 (all frontend core views) must be merged first; runs against the full deployed stack (TASK-004)
- **Branch:** `enabler-story/system-e2e-tests`
- **Status:** Not started

## Objective

Author the **system-level end-to-end test suite** with Playwright that drives the running application through the browser for every user type and maps **each SR acceptance criterion to at least one system test** (SR-028.4 / NFR-006.4 — the requirement→test obligation). The same suite runs **cross-browser** on the four supported targets (Safari/WebKit, Firefox, Chromium for Chrome, and Edge) including **WebGL DICOM rendering** (SR-019, ADR-0008). This is the executable evidence that the product satisfies its requirements and works on all target browsers; the reference-image DICOM correctness check (deferred from TASK-102, SR-017 risk control) lands here.

## Interfaces to honor

- Drives the **public external interface only**: the SPA UI and, through it, `/api/v1/*`. Tests assert observable user-visible behavior and HTTP outcomes, never internal services.
- Authentication is the opaque session **cookie** + CSRF flow (ADR-0012, SR-031.3) exactly as a real browser performs it; tests log in via the UI, not by injecting sessions.
- Access control is verified to be **server-side**: a test that manipulates client state (e.g., reveals a hidden nav item) must still receive **403** from the API (SR-031.5, ADR-0003) — UI hiding is never the sole control.
- DICOM bytes are fetched only from `GET /api/v1/modules/dicom-viewer/studies/{attachmentId}` (ADR-0008); rendering uses real WebGL in each browser.

Tests must **not**: seed data by writing directly to the DB in a way that bypasses authorization (set up via the API as the appropriate actor); rely on a single browser; assert pixel-exact rendering except in the dedicated reference-image check.

## Implementation detail

- Files to create under `frontend/tests/e2e/` (Playwright project, `playwright.config.ts` with `projects` for `webkit`, `firefox`, `chromium`, and an Edge channel; CI from TASK-005):
  - `auth.spec.ts` — login success/failure (generic error), lockout after 5 failures, inactivity warning at 2 min before timeout and session expiry, logout (SR-002, SR-029, SR-030).
  - `activation-password.spec.ts` — activation link → set password (policy + mismatch errors), change password (SR-033, SR-025).
  - `profile.spec.ts` — each user type sees own profile only (SR-003, SR-007).
  - `patients-clinical.spec.ts` — doctor patient list scoped to accessible patients; view/create clinical entry; attachment (DICOM/report) upload (SR-006, SR-012, SR-013).
  - `appointments.spec.ts` — doctor creates appointment; patient confirms/declines; visibility scoping; confirm grants access, decline scopes correctly (SR-010, SR-011, SR-035, SR-036).
  - `consent.spec.ts` — patient grants/revokes; unified manual + appointment view; revoke is immediate (SR-008, SR-036.7).
  - `admin-accounts.spec.ts` — admin sees non-clinical projection; create/deactivate/reactivate/delete with confirmation (SR-009, SR-032, SR-034).
  - `admin-groups-modules.spec.ts` — sysadmin manages groups, membership, per-group module enablement (SR-014, SR-015).
  - `module-nav-gating.spec.ts` — DICOM viewer nav item appears only when the module is enabled for the user's group; deep-link still gated server-side (SR-015, SR-016.2).
  - `dicom-viewer.spec.ts` — open a study, initial image renders, controls operate: window/level, zoom, pan, slice navigation (SR-017, SR-018); access-denied surface on 403 (SR-017 AC-5).
  - `dicom-reference-render.spec.ts` — **reference-image correctness** (SR-017 risk control, deferred from TASK-102): open known CT, MRI, and X-ray studies and assert correct pixel scaling, default window/level, and slice order against committed reference snapshots, on each browser (ADR-0008, safety/NFR-005).
  - `responsive.spec.ts` — core workflows on phone/tablet/desktop viewports, no horizontal scroll of primary content (SR-020).
  - `usability.spec.ts` — each user type completes its core task using on-screen guidance only (SR-027.4).
  - `_fixtures/` — API-driven seed helpers (create accounts/groups/appointments/consents via `/api/v1` as the correct actor); DICOM sample fixtures (CT/MRI/X-ray) and their reference snapshots.
  - `traceability.md` (or a tagged-test report) — the SR-AC → spec → test-name map, the input TASK-114 consumes.
- Each test is **tagged** with the SR/AC id(s) it covers (Playwright annotations) so the suite emits an SR→test report (SR-028.4).
- Cross-browser: the suite runs unchanged on all four projects; WebGL rendering (DICOM) is exercised per browser, with the documented Safari/WebKit caveats from ADR-0008 explicitly tested (SR-019 AC-1).
- The documented cross-browser test pass (SR-019 AC-3) is produced as the CI matrix report per release.
- Performance assertions (3 s / 10 s budgets) are **not** made here — that is TASK-112; this suite asserts functional correctness and layout integrity.

## Tests (write first — TDD, CLAUDE.md §4)

This task is the system-test suite itself. Each spec is written to the SR acceptance criteria before the suite is considered complete and is tagged with the verified SR/AC id. Coverage cases: every functional SR has at least one passing tagged test (SR-028.4); each browser project runs the full suite (SR-019); the reference-image specs cover CT, MRI, and X-ray (SR-017 AC-2). The suite must demonstrate that bypassing client-side UI hiding still yields server-side 403 (SR-031.5).

## Acceptance criteria

- [ ] Every functional SR maps to at least one tagged, passing Playwright system test (SR-028.4, NFR-006.4).
- [ ] The full suite passes on current stable Safari/WebKit, Firefox, Chrome/Chromium, and Edge with no functional errors and layout intact (SR-019 AC-1/2).
- [ ] WebGL DICOM rendering operates on all four browsers; reference CT/MRI/X-ray images render with correct scaling, default window/level, and slice order (SR-017, ADR-0008).
- [ ] Responsive core workflows show no horizontal scroll of primary content across phone/tablet/desktop (SR-020).
- [ ] Client-side UI hiding is shown to be non-authoritative — server returns 403 when client gates are bypassed (SR-031.5).
- [ ] A documented cross-browser test pass is produced for the release (SR-019 AC-3).
- [ ] The SR-AC → test map is emitted for TASK-114 consumption.

## Definition of Done

- [ ] Lint + type-check pass (`eslint`/`tsc` on the Playwright project)
- [ ] System E2E suite passes on all four browser projects; SR→test report generated
- [ ] OpenAPI regenerated and re-linted (N/A)
- [ ] Audit events: N/A at the UI layer (asserted at integration level in TASK-110)
- [ ] Traceability matrix rows updated (functional SRs + SR-019/028 → TASK-111 → tagged tests) — consumed by TASK-114
- [ ] Security review N/A (no auth/session implementation; this suite verifies it)
