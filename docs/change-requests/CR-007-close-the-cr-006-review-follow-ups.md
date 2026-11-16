---
id: CR-007
type: change-request
title: Close the CR-006 review follow-ups (frontend module design, budget check, upload scratch space)
status: open
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-11-16"
updated: "2026-11-16"
branch: fix/cr-007-review-followups
risk_impact: affects_controls
links:
  - target: PRB-091
    relation: resolves
  - target: PRB-093
    relation: resolves
  - target: PRB-092
    relation: relates_to
  - target: SR-013
    relation: relates_to
  - target: SR-015
    relation: relates_to
  - target: SR-016
    relation: relates_to
  - target: SR-026
    relation: relates_to
  - target: ADD-021
    relation: relates_to
  - target: RISK-004
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: TASK-229
    relation: relates_to
  - target: TASK-230
    relation: relates_to
  - target: TASK-231
    relation: relates_to
  - target: CR-006
    relation: relates_to
tags:
  - review-follow-up
  - stacked-on:CR-006
---

## Reason

The CR-006 reviews (TASK-225 and TASK-226 QA) raised three problem reports outside CR-006's scope.
All three are `minor`; none affects a safety-related function or a clinical decision:

- **PRB-091:** the approved design (ADD-021, arc42 sections 05 and 12) describes two frontend units,
  `U-FEM-Registry` and `U-FEM-NavGate`, and a `ModuleRegistry` interface that were never built. The
  design records and the code disagree (IEC 62304 §5.3, §5.4).
- **PRB-093:** `npm run check:budget` run after `npm run build` crashes with an uncaught ENOENT stack
  trace instead of a verdict, because the build removes the Vite manifest the check reads.
- **PRB-092:** the API container spools an upload above 1 MiB to a temporary file, and nothing limits
  or checks that space. A full directory fails the upload with a 5xx and stores nothing (RISK-007).

One CR bundles them because they come from the same review, are small, and share one verification run
(frontend suite and build, `traceability-check`). The branch `fix/cr-007-review-followups` stacks on
the CR-006 branch head `f47d617` (PR #40, not merged); CR-007 is merged after CR-006.

## Scope

### In scope

| PRB | Crit. | State on this branch (evidence) | Change | TASK |
|---|---|---|---|---|
| PRB-091 Approved design names frontend module units that were never built | minor | Open: no `ModuleRegistry`, `register(` or module navigation item in `frontend/src`; the only reader of `GET /me/modules` is `useMyModules` (`frontend/src/modules/useMyModules.ts:12`), whose one consumer is `AttachmentItem` (`frontend/src/core/clinical/AttachmentItem.tsx:18-30`, the "Open in viewer" link of a DICOM attachment) | Documentation correction (D-1): ADD-021, arc42 05 and 12 describe what exists; the registry and the navigation gate are recorded as deferred to the frontend DICOM viewer module (PRB-048; planned in TASK-100, TASK-101). No code change | TASK-230 |
| PRB-093 Standalone `check:budget` fails with a stack trace after a build | minor | Open: `frontend/scripts/check-bundle-budget.mjs:36` `measureInitial` reads `dist/.vite/manifest.json` (and `:48` `chunk-modules.json`) without checking that they exist; `package.json` `build` ends with `--clean`, which removes `dist/.vite` | Fix option (a) (D-1): a missing manifest prints a clear message telling the user to run `npm run build` (or `npx vite build`) and exits 1; never a pass | TASK-229 |
| PRB-092 Upload scratch space in the API container is neither limited nor checked | minor | Open: no limit or free-space check in `backend/app` or `infra/docker-compose.yml`; `infra/DEPLOY.md:234-235` says only that concurrent large uploads need free disk space | No code control (D-1). The residual is recorded in RISK-007 with the DEPLOY.md note as the information-for-safety measure; the note states the sizing and the failure behaviour. PRB status: see P-3 | TASK-231 |

### Requirements decision

No SR, UN, NFR or RR changes in this CR. PRB-093 restores the intended behaviour of the SR-026 AC 7
check (a verdict, fail closed). PRB-091 changes design records only. Whether SR-016 AC 2 needs a
wording change is open (P-1); no SR is edited here.

### Out of scope

- Building `ModuleRegistry`, `FrontendModule` or the module navigation gate. They stay planned in
  TASK-100 and TASK-101 (`draft`) and are built with their first consumer, the frontend DICOM viewer
  module (PRB-048, TASK-102).
- ADR-0005 (plugin module mechanism) and `docs/specifications/api-design.md` (the `FrontendModule`
  shape): they record the decision and the target interface, which still hold; only the "built"
  claims in ADD-021 and sections 05 and 12 are corrected.
- A code control for the upload scratch space (a sized scratch volume, an upload concurrency limit or
  a start-up free-space check). Declined by the human (D-1); revisit if a deployment reports it.
- RISK acceptance and record approval: only the human approves, in MedTrace.

### Boundaries

- **Ask first:** any change to `package.json` scripts (option (b) of PRB-093 was not chosen); any
  change to `backend/app` or `infra/docker-compose.yml`.
- **Never:** turn a missing manifest into a pass or exit 0; edit an `approved` record without bumping
  its version, setting `in_review`, removing its approval record (`approved_by`, `approved_on`,
  `approved_digest`, `approval_note`) and adding a version-history line; change an SR.

## Verification approach

IEC 62304 §8.2.1 (change approval), §8.2.3 (verification of changes), §5.5 (unit verification, class B)
and §9.7 (verification of the problem resolution).

- **PRB-093 (TASK-229, SR-026 AC 7):** a unit test in `frontend/scripts/check-bundle-budget.test.mjs`
  on an empty temporary `dist` directory: the script exits 1, its output names the missing manifest
  and tells the user to run `npm run build`, and it prints no stack trace; written first and failing
  on `f47d617`. Reproducible command: `npm run build && npm run check:budget; echo $?` prints the
  message and `1`. `npm run build` still ends with "within the budget" and exit 0; the existing
  TC-018.10 tests stay green. Recorded in TS-018 TC-018.10.
- **PRB-091 (TASK-230):** review of ADD-021, `docs/design/05-building-blocks.md` and
  `docs/design/12-interfaces.md` against `frontend/src`: every unit and interface named as built
  exists (`grep -rn "ModuleRegistry\|register(\|FrontendModule" frontend/src` returns nothing, and no
  record claims it does); the existing verification of the built unit is unchanged (TS-005 TC-005.5,
  TC-005.6).
- **PRB-092 (TASK-231):** review that RISK-007 lists the scratch-space cause, the residual and the
  DEPLOY.md measure, and that the DEPLOY.md note states the directory, the sizing rule and the
  failure behaviour. No test: the measure is information for safety.
- **Whole change:** `npm run test -- --run`, `npm run lint`, `npm run build` (frontend); no backend or
  OpenAPI change; `traceability-check` with no errors for the records of this CR.

## Assumptions

- A-1. Class B is unchanged (`docs/medtrace.yml` `safety_class: B` and `CLAUDE.md` agree).
- A-2. CR-006 merges before CR-007. If CR-006 changes RISK-007, ADD-021 or TS-018 again before it
  merges, the CR-007 tasks rebase their record edits onto that version.
- A-3. The DEPLOY.md note is the deployment information shipped to the operator; there is no separate
  instructions-for-use document.

## Open questions

- **P-1. SR-016 AC 2 ("An enabled module is presented in the application's navigation/UI for
  authorized users").** Investigation (2026-11-16): no frontend module exists. The only module entry
  point in the UI is the "Open in viewer" link on a DICOM attachment (`AttachmentItem.tsx:29-33`),
  shown only when `dicom-viewer` is in the user's module list; it links to the attachment download URL,
  not to a viewer. That gating is verified by TS-005 TC-005.6 (which `verifies` SR-015 AC 3 and AC 4,
  not SR-016). TS-010 covers SR-016 AC 1 and AC 3 only (backend discovery, mounting, boundary); no test
  case cites SR-016 AC 2. So the wording claims a module presentation that is not built.
  Options: (a) keep the wording and record that SR-016 AC 2 is deferred to the frontend DICOM viewer
  module (PRB-048, TASK-100, TASK-101), as D-35 of CR-006 did for SR-026 AC 3; (b) reword it to what
  exists, for example "An enabled module's entry points in the user interface are shown only to users
  for whom the module is enabled", and add SR-016 AC 2 to TC-005.6. *Recommendation:* (a). The SR
  states the intended product, the build is already planned, and (b) would weaken a requirement to
  fit the code and need a re-approval of SR-016. Under (a) the release record lists SR-016 AC 2 as not
  verified until PRB-048 is resolved.
- **P-2. SR-015 AC 3 and the lazy loading of modules.** SR-015 AC 3 ("A user can access a module only
  if it is enabled for at least one group they belong to") claims no frontend navigation: it is
  verified on the server (TS-005 TC-005.2) and on the client entry point (TC-005.6). *Recommendation:*
  no change. No SR asks for module lazy loading except SR-026 AC 7 ("routes and modules that the
  landing route does not render"); with no frontend module, its module part is empty today and
  TC-018.10 checks route chunks only. *Recommendation:* no change now; TASK-100 adds the module chunk
  to `LAZY_GROUPS` when it builds the registry (a note in TASK-230's ADD-021 text).
- **P-3. PRB-092 status.** *Recommendation:* keep PRB-092 **`open`** as a known residual anomaly, with
  CR-007 linked by `relates_to`, not `resolves`. Reasons: `rejected` in problem-report-resolution means
  not a real bug (duplicate, working as intended, won't fix); the defect is real and stays in the
  product, and a `rejected` PRB drops out of the "Known residual anomalies" list of every release
  record (§5.8.2, §5.8.3), where the operator-facing evaluation belongs. `resolved` would claim a fix
  that does not exist. Cost: the PRB stays open until a control is built or the product changes; it is
  `minor`, so it never blocks the release gate. Alternative: `rejected` as "won't fix, residual
  accepted in RISK-007"; then the release records must cite RISK-007 for it instead.
- **P-4. DEPLOY.md wording (TASK-231).** The current note does not say how much space or what happens
  when it runs out, which an information-for-safety measure needs. *Recommendation:* extend the note
  to: the directory (the container's temporary directory, `/tmp` unless `TMPDIR` is set), the sizing
  rule (about 150 MiB free per concurrent maximum-size upload the site expects), the failure behaviour
  (the upload answers a 5xx, nothing is stored, the user retries) and that other requests needing the
  directory may fail while it is full.

## Decisions

- **D-1 (2026-11-16):** the human (Carlos Santiago Liceras) answered "Sí, CR-007" in chat, accepting
  the recommendations for the three PRBs: (1) PRB-091: correct the design records to describe what
  exists; build the registry when the frontend DICOM viewer module is built (PRB-048), its first
  consumer; resolve PRB-091 in CR-007 by the documentation correction. (2) PRB-093: fix option (a),
  a clear message and exit 1 on a missing manifest; resolved by CR-007. (3) PRB-092: no code control;
  accept the residual and record it in RISK-007 with the DEPLOY.md note as the information-for-safety
  measure (a loud 5xx, no partial record); RISK acceptance stays with the human in MedTrace. The
  decision was relayed by the coordinating agent; the human's MedTrace approval of CR-007 confirms it.

- **D-2 (P-1, human decision 2026-11-16, "Defer to PRB-048"):** SR-016 AC 2 keeps its wording and stays
  unverified until the frontend DICOM viewer module is built (PRB-048), as D-35 of CR-006 did for SR-026 AC 3.
- **D-3 (P-2, human decision 2026-11-16, plan approved with "no change"):** SR-015 AC 3 and SR-026 AC 7 are
  not changed; TASK-100 adds the module chunk to `LAZY_GROUPS` when it builds the registry.
- **D-4 (P-3, human decision 2026-11-16, "Keep open"):** PRB-092 stays `open` as a known residual anomaly;
  CR-007 links it `relates_to`.
- **D-5 (P-4, human decision 2026-11-16, plan approved):** the DEPLOY.md note names the directory, about
  150 MiB free per concurrent maximum-size upload, and the failure behaviour (5xx, nothing stored, retry).
- **D-6 (2026-11-16):** the human approved the plan (TASK-229, TASK-230, TASK-231) with "Approve and build".

## Change analysis (§7.4, 2026-11-16)

Software Architect role. Scales and matrix: `docs/medtrace.yml` (5 × 5 `risk_matrix`) and PLAN-005.

- **Records consulted:** PRB-048, PRB-091, PRB-092, PRB-093; SR-013, SR-015, SR-016, SR-026; ADD-021;
  TS-005, TS-010, TS-018; RISK-004, RISK-007; ADR-0005, ADR-0021; TASK-100, TASK-101; arc42 05, 11, 12;
  `infra/DEPLOY.md`.
- **Code read:** `frontend/scripts/check-bundle-budget.mjs`, `frontend/package.json`,
  `frontend/src/modules/useMyModules.ts`, `frontend/src/core/clinical/AttachmentItem.tsx`.

**Conclusion: `risk_impact: affects_controls`; no new hazard; class B unchanged.**

- **TASK-229 (PRB-093): no RISK affected.** The script runs at build time and is not deployed. The
  change keeps the check fail closed: a missing manifest still exits 1 and never prints "within the
  budget", so it cannot hide a budget breach (SR-026 AC 7, the RISK-007 route-chunk row). The `build`
  script and `--clean` are unchanged.
- **TASK-230 (PRB-091): no control changed.** Documentation only. The RISK-004 controls for module
  access are unchanged and are what exists: the server guard (`ModuleAccessGuard`, SR-015 AC 3) and
  the client gate on the viewer link through `useMyModules` (SR-015 AC 5, TC-005.5, TC-005.6). The
  correction removes a claim of a client navigation gate that never existed; RISK-004 does not rely on
  it (defence in depth only, PRB-091 safety evaluation).
- **TASK-231 (PRB-092): affects the RISK-007 controls.** A cause is added to RISK-007 (scratch space
  full under concurrent large uploads) with one information-for-safety measure (the DEPLOY.md sizing
  note). The hazard (clinical information unavailable) is already in RISK-007; the failure is loud
  (5xx), stores no partial attachment and changes no stored data (no RISK-002 or RISK-012 path).
  Residual: severity 3 × probability 2 → `alarp`, unchanged. The cause needs several concurrent
  maximum-size uploads on a host with little temporary space, consistent with probability 2; the
  single-host decision (ADR-0010) and PRB-057 still set the residual. Note: the SR-026 AC 5 load test
  (TC-018.3) uploads 1 MiB files, at the spool threshold, so it does not exercise this cause.
  RISK-007 is `approved` 1.19; TASK-231 bumps it to 1.20, sets `in_review` and removes its approval
  record for the human's acceptance.
- **Class:** no change reaches a harm above severity 3; the class B rationale in `docs/medtrace.yml`
  holds.

## Plan

Plan stage, 2026-11-16, Software Architect role. The plan is the TASK records below (overlay: no
`docs/plans/<feature>.md`). Nothing is built until the human approves CR-007 and the answers to P-1 to
P-4. All tasks on `fix/cr-007-review-followups`, one commit per QA-approved task with its records.

### Tasks

| Order | Task | PRB | SR (AC) | RISK (`mitigates`) | Size | Depends on | Status |
|---|---|---|---|---|---|---|---|
| 1 | [TASK-229](../design-outputs/tasks/TASK-229-clear-message-when-the-budget-check-has-no-manifest.md) Clear message and exit 1 when the budget check has no manifest | 093 | SR-026 AC 7 | — | XS | — | new |
| 2 | [TASK-230](../design-outputs/tasks/TASK-230-correct-the-frontend-module-design-to-what-exists.md) Correct ADD-021, arc42 05 and 12 to the built frontend module units | 091 | SR-015, SR-016 (design records) | — | S | — (parallel with 1) | new |
| 3 | [TASK-231](../design-outputs/tasks/TASK-231-record-the-upload-scratch-space-residual.md) Record the upload scratch-space residual in RISK-007 and DEPLOY.md | 092 | SR-013 AC 1 | 007 | XS | — (parallel with 1, 2) | new |
| — | **Checkpoint** | | | | | 1–3 | frontend suite, lint and `npm run build` green; `traceability-check` 0 errors |

### Plan risks

| Risk | Impact | Mitigation |
|---|---|---|
| CR-006 changes RISK-007, ADD-021 or TS-018 before it merges | Record edits conflict | Rebase onto the CR-006 head before each task; bump from the version found |
| The missing-manifest branch is written as a pass | A budget breach hidden | Test asserts exit 1 and no "within the budget"; QA mutant |
| ADD-021 loses the deferred design | The registry is forgotten | ADD-021 names TASK-100, TASK-101 and PRB-048 as the deferred build |

## Version history

- 1.0 (2026-11-16) — Created with the Plan (Software Architect role) from the human decision D-1 ("Sí, CR-007"). `resolves` PRB-091 and PRB-093; `relates_to` PRB-092 (P-3). Change analysis: `affects_controls` (RISK-007 gains a cause and an information measure), no new hazard, class B unchanged. TASK-229 to TASK-231 new. Open questions P-1 to P-4 for the human. `open`.
- 1.1 (2026-11-16) — Plan gate: the human answered P-1 to P-4 (D-2 to D-5) and approved the plan (D-6). No scope change. `open`.
