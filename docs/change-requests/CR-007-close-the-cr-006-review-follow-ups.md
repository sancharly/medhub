---
id: CR-007
type: change-request
title: Close the CR-006 review follow-ups (frontend module design, budget check, upload scratch space)
status: open
version: "1.3"
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
    relation: resolves
  - target: SR-013
    relation: relates_to
  - target: SR-027
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
  - target: TASK-232
    relation: relates_to
  - target: SOUP-002
    relation: relates_to
  - target: SOUP-003
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
  or checks that space. A full directory fails the upload and stores nothing (RISK-007). Today the failure
  is a plain HTTP 400 "There was an error parsing the body" (`application/json`, not a problem) that the API
  does not log: FastAPI 0.138.0 wraps the spool `OSError` raised inside `await request.form()` into that 400
  (`fastapi/routing.py:420-465`), so the 500 handler (`backend/app/api/errors.py:206-221`) never runs
  (TASK-231 QA R1-1, 2026-11-16; versions 1.0 and 1.1 of this CR wrongly said "a 5xx").

One CR bundles them because they come from the same review, are small, and share one verification run
(frontend suite and build, `traceability-check`). The branch `fix/cr-007-review-followups` stacks on
the CR-006 branch head `f47d617` (PR #40, not merged); CR-007 is merged after CR-006.

## Scope

### In scope

| PRB | Crit. | State on this branch (evidence) | Change | TASK |
|---|---|---|---|---|
| PRB-091 Approved design names frontend module units that were never built | minor | Open: no `ModuleRegistry`, `register(` or module navigation item in `frontend/src`; the only reader of `GET /me/modules` is `useMyModules` (`frontend/src/modules/useMyModules.ts:12`), whose one consumer is `AttachmentItem` (`frontend/src/core/clinical/AttachmentItem.tsx:18-30`, the "Open in viewer" link of a DICOM attachment) | Documentation correction (D-1): ADD-021, arc42 05 and 12 describe what exists; the registry and the navigation gate are recorded as deferred to the frontend DICOM viewer module (PRB-048; planned in TASK-100, TASK-101). No code change | TASK-230 |
| PRB-093 Standalone `check:budget` fails with a stack trace after a build | minor | Open: `frontend/scripts/check-bundle-budget.mjs:36` `measureInitial` reads `dist/.vite/manifest.json` (and `:48` `chunk-modules.json`) without checking that they exist; `package.json` `build` ends with `--clean`, which removes `dist/.vite` | Fix option (a) (D-1): a missing manifest prints a clear message telling the user to run `npm run build` (or `npx vite build`) and exits 1; never a pass | TASK-229 |
| PRB-092 Upload scratch space in the API container is neither limited nor checked | minor | Open: no limit or free-space check in `backend/app` or `infra/docker-compose.yml`; `infra/DEPLOY.md:234-235` says only that concurrent large uploads need free disk space. A full directory answers a plain 400 with no API log (TASK-231 QA R1-1); nginx also buffers the body to its own temporary directory (`infra/reverse-proxy/nginx.conf:75-89`, R1-2) | (1) Code fix (D-7): a spool `OSError` on the upload route is logged at ERROR and answered 503 `application/problem+json` `upload-storage-unavailable` with `Retry-After: 30`; nothing is stored; a malformed body stays 400. (2) Information for safety (D-1, D-5 as amended by D-7): the DEPLOY.md note names both temporary directories, about 300 MiB free per concurrent maximum-size upload where they share a disk, and the fixed failure behaviour. Capacity itself stays uncontrolled: residual in RISK-007. CR-007 `resolves` PRB-092 (D-7; D-4 superseded) | TASK-232, then TASK-231 (round 2) |

### Requirements decision

No SR, UN, NFR or RR changes in this CR. PRB-093 restores the intended behaviour of the SR-026 AC 7
check (a verdict, fail closed). PRB-091 changes design records only. Whether SR-016 AC 2 needs a
wording change is open (P-1); no SR is edited here. TASK-232 (PRB-092) implements existing criteria and
needs no SR change: SR-013 AC 1 (an upload either succeeds or fails with nothing stored) and SR-027 AC 3 (a
failed operation shows a clear, actionable message); the API contract gains one documented response.

### Out of scope

- Building `ModuleRegistry`, `FrontendModule` or the module navigation gate. They stay planned in
  TASK-100 and TASK-101 (`draft`) and are built with their first consumer, the frontend DICOM viewer
  module (PRB-048, TASK-102).
- ADR-0005 (plugin module mechanism) and `docs/specifications/api-design.md` (the `FrontendModule`
  shape): they record the decision and the target interface, which still hold; only the "built"
  claims in ADD-021 and sections 05 and 12 are corrected.
- A capacity control for the upload scratch space (a sized scratch volume, an upload concurrency limit
  or a start-up free-space check). Declined by the human (D-1); revisit if a deployment reports it. D-7
  adds failure handling (TASK-232), not a capacity control: the space can still run out.
- The reverse proxy's own client-body buffer (R1-2): nginx answers its own 500 and logs at `crit` when its
  temporary directory is full, so that failure is already logged; it is covered by the DEPLOY.md sizing
  (TASK-231), with no nginx change.
- Other multipart routes: there are none (`POST /api/v1/clinical-entries/{entry_id}/attachments` is the
  only route that takes a form body); TASK-232 scopes the mapping to the attachments router.
- RISK acceptance and record approval: only the human approves, in MedTrace.

### Boundaries

- **Ask first:** any change to `package.json` scripts (option (b) of PRB-093 was not chosen); any
  change to `backend/app` or `infra/docker-compose.yml` beyond TASK-232's two files
  (`backend/app/api/errors.py`, `backend/app/api/routers/attachments.py`; D-7); any change to
  `infra/reverse-proxy/nginx.conf`.
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
- **PRB-092, code fix (TASK-232, SR-013 AC 1, SR-027 AC 3):** backend tests through `create_app()` with
  `tempfile.SpooledTemporaryFile.rollover` raising `OSError(ENOSPC)` on a 2 MiB part: 503
  `application/problem+json` `upload-storage-unavailable`, `Retry-After: 30`, `store` never called, one
  ERROR record with the route template and `ENOSPC` and without the entry id or file name; written first
  and failing on `4eeef74` (400, no log). Regression: an 8 KB part header and a missing boundary still
  answer 400 as before; an `OSError` from `store` still answers the 500 problem. Frontend: the client and
  the upload form surface the 503 detail. Mutation checks: no cause check, no route class, wrong
  `HTTPException` class. Recorded in TS-007 TC-007.17 and TS-011 TC-011.7.
- **PRB-092, information (TASK-231 round 2):** review that RISK-007 lists the scratch-space cause, the
  TASK-232 control, the residual and the DEPLOY.md measure, and that the DEPLOY.md note states both
  directories, the sizing rule and the fixed failure behaviour, matching the TASK-232 tests.
- **Whole change:** `npm run test -- --run`, `npm run lint`, `npm run typecheck`, `npm run build`
  (frontend, Node 20 or later); backend suite, Ruff and Black; OpenAPI regenerated with one additive
  change (the upload's 503) and `frontend/src/api/generated/openapi.ts` regenerated from it (drift test and
  CI `openapi-lint` green); `traceability-check` with no errors for the records of this CR.

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
  *Superseded in 1.2 by D-7:* a fix now exists (TASK-232), so `resolved` no longer claims a fix that
  does not exist; see D-7.
- **P-4. DEPLOY.md wording (TASK-231).** The current note does not say how much space or what happens
  when it runs out, which an information-for-safety measure needs. *Recommendation:* extend the note
  to: the directory (the container's temporary directory, `/tmp` unless `TMPDIR` is set), the sizing
  rule (about 150 MiB free per concurrent maximum-size upload the site expects), the failure behaviour
  (the upload answers a 5xx, nothing is stored, the user retries) and that other requests needing the
  directory may fail while it is full. *Corrected in 1.2:* the "5xx" was wrong for the code at the time
  (a plain 400, R1-1) and becomes true only with TASK-232 (503 problem, logged); the sizing is about
  300 MiB where the API and proxy temporary directories share a disk (R1-2). See D-7 and P-5.
- **P-5. Confirmation of the D-7 consequences (new in 1.2).** D-7 changes two earlier answers:
  (a) PRB-092 moves from `relates_to` to `resolves` and becomes `resolved` once TASK-232 and TASK-231
  round 2 pass QA, superseding D-4 (it leaves the "Known residual anomalies" list of the release records;
  the capacity residual stays in RISK-007); (b) the D-5 sizing of about 150 MiB becomes about 300 MiB per
  concurrent maximum-size upload where both temporary directories share a disk (QA R1-2, a fact about
  the deployment, not a new choice). *Recommendation:* confirm both with the approval of CR-007 1.2.
  Alternative to (a): keep D-4 (`open`, `relates_to`) because the title's "neither limited" stays true;
  then the release records list PRB-092 with the RISK-007 evaluation.

## Decisions

- **D-1 (2026-11-16):** the human (Carlos Santiago Liceras) answered "Sí, CR-007" in chat, accepting
  the recommendations for the three PRBs: (1) PRB-091: correct the design records to describe what
  exists; build the registry when the frontend DICOM viewer module is built (PRB-048), its first
  consumer; resolve PRB-091 in CR-007 by the documentation correction. (2) PRB-093: fix option (a),
  a clear message and exit 1 on a missing manifest; resolved by CR-007. (3) PRB-092: no code control;
  accept the residual and record it in RISK-007 with the DEPLOY.md note as the information-for-safety
  measure (a loud 5xx, no partial record); RISK acceptance stays with the human in MedTrace. The
  decision was relayed by the coordinating agent; the human's MedTrace approval of CR-007 confirms it.
  *Correction (1.2):* "a loud 5xx" described the code wrongly; it was a plain, unlogged 400 (TASK-231
  QA R1-1). Part (3) is replaced by D-7.

- **D-2 (P-1, human decision 2026-11-16, "Defer to PRB-048"):** SR-016 AC 2 keeps its wording and stays
  unverified until the frontend DICOM viewer module is built (PRB-048), as D-35 of CR-006 did for SR-026 AC 3.
- **D-3 (P-2, human decision 2026-11-16, plan approved with "no change"):** SR-015 AC 3 and SR-026 AC 7 are
  not changed; TASK-100 adds the module chunk to `LAZY_GROUPS` when it builds the registry.
- **D-4 (P-3, human decision 2026-11-16, "Keep open"):** PRB-092 stays `open` as a known residual anomaly;
  CR-007 links it `relates_to`. *Superseded by D-7 (1.2), subject to P-5 (a).*
- **D-5 (P-4, human decision 2026-11-16, plan approved):** the DEPLOY.md note names the directory, about
  150 MiB free per concurrent maximum-size upload, and the failure behaviour (5xx, nothing stored, retry).
  *Amended by D-7 (1.2), subject to P-5 (b):* both directories, about 300 MiB where they share a disk,
  and the failure behaviour as built by TASK-232.
- **D-6 (2026-11-16):** the human approved the plan (TASK-229, TASK-230, TASK-231) with "Approve and build".
- **D-7 (2026-11-16, human decision):** asked "How should CR-007 handle PRB-092 now?" after TASK-231 QA
  round 1 (R1-1: a full scratch directory answers a plain, unlogged 400), the human answered "Add a code
  fix in CR-007": a new task that logs the disk error and answers a 5xx problem+json on the upload route.
  Consequences in 1.2: TASK-232 (logged 503 `upload-storage-unavailable`, attachments router only, design
  in the TASK); TASK-231 round 2 runs after it; CR-007 `resolves` PRB-092 because the defect — a scratch
  failure that neither the operator nor the user can act on — is fixed by the logged, retryable 503 plus
  the sizing note, and what remains (the space can still run out) is the capacity residual accepted in
  RISK-007, not a defect; this supersedes D-4. The D-1 "no code control" for capacity still holds. Relayed
  by the coordinating agent; the human's approval of CR-007 1.2 (with P-5) confirms it.

- **D-8 (P-5 and the TASK-232 plan gate, human decisions 2026-11-16):** TASK-232 approved ("Approve and
  build"); (a) PRB-092 is resolved by CR-007, superseding D-4 ("Resolve it"); (b) the DEPLOY.md sizing is
  about 300 MiB per concurrent maximum-size upload where the API and reverse-proxy directories share a disk
  ("Yes, ~300 MiB").

## Change analysis (§7.4, 2026-11-16)

Software Architect role. Scales and matrix: `docs/medtrace.yml` (5 × 5 `risk_matrix`) and PLAN-005.

- **Records consulted:** PRB-048, PRB-091, PRB-092, PRB-093; SR-013, SR-015, SR-016, SR-026; ADD-021;
  TS-005, TS-010, TS-018; RISK-004, RISK-007; ADR-0005, ADR-0021; TASK-100, TASK-101; arc42 05, 11, 12;
  `infra/DEPLOY.md`.
- **Code read:** `frontend/scripts/check-bundle-budget.mjs`, `frontend/package.json`,
  `frontend/src/modules/useMyModules.ts`, `frontend/src/core/clinical/AttachmentItem.tsx`; for 1.2
  also `fastapi/routing.py:367-465, 1183-1240` (0.138.0), `backend/app/api/errors.py`,
  `backend/app/api/routers/attachments.py`, `backend/app/core/body_limit.py`, `backend/app/main.py`,
  `frontend/src/api/client.ts`, `frontend/src/core/clinical/AttachmentUpload.tsx`,
  `infra/reverse-proxy/nginx.conf`; records SR-027, SR-043, TS-007, TS-011, SOUP-002, SOUP-003, ADD-005,
  arc42 08 and 12.

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
- **TASK-231 and TASK-232 (PRB-092): affect the RISK-007 controls.** *Redone in 1.2 (D-7); the 1.0
  text said the failure "is loud (5xx)", which was wrong for the code (TASK-231 QA R1-1).*
  - *Behaviour today (`4eeef74`):* a full scratch directory makes the upload answer a plain 400 "There
    was an error parsing the body"; the API logs nothing; nothing is stored. The user reads it as a bad
    file and may not retry; the operator sees only a 400 in the proxy access log. The hazard (clinical
    information unavailable) is already in RISK-007; no stored data changes (no RISK-002 or RISK-012
    path).
  - *Controls after this CR:* a cause is added to RISK-007 (scratch space full under concurrent large
    uploads, in the API container and in the reverse proxy's body buffer) with two measures:
    (1) **protective, code (TASK-232):** the spool failure is detected, logged at ERROR (operator alarm in
    the application log) and answered 503 problem+json with a retry instruction shown to the user;
    nothing stored; implemented by SR-013 AC 1 and SR-027 AC 3, verified by TC-007.17 and TC-011.7;
    (2) **information (TASK-231):** the DEPLOY.md note (both directories, about 300 MiB per concurrent
    maximum-size upload where they share a disk, the fixed failure behaviour, monitor the free space).
    RISK-007's control types now include a code measure (`control:protective`) beside the information
    measure.
  - *New hazards from the controls:* none found. The mapping is limited to a 400 whose cause is an
    `OSError` on the attachments router, so a malformed body is still refused as a client error and no
    error is hidden (an `OSError` after the parse still gives the logged 500); the log record carries the
    route template and errno only (no path, file name or form data; SR-043); the 503 detail discloses no
    internals; the client does not retry automatically, so `Retry-After` cannot cause a retry storm.
    Reliance on a FastAPI internal (the 400 raised `from` the cause) is recorded in SOUP-002 and pinned
    by TC-007.17 against the locked version.
  - *Residual:* severity 3 × probability 2 → `alarp`, unchanged. The protective measure does not lower
    the probability that the space runs out; it makes the failure visible and recoverable (retry), which
    supports the ALARP argument but is not scored as a reduction. The cause needs several concurrent
    maximum-size uploads on a host with little temporary space; ADR-0010 and PRB-057 still set the
    residual. The SR-026 AC 5 load test (TC-018.3) uploads 1 MiB files, at the spool threshold, so it
    does not exercise this cause. Acceptance is the human's, in MedTrace.
  - RISK-007 is `in_review` 1.20 in the working tree (TASK-231 round 1, not committed); TASK-231 round 2
    carries all RISK-007 edits, including the TASK-232 control row, so one task edits it.
- **Class:** no change reaches a harm above severity 3; the code change adds no function whose failure
  could cause more than a delayed upload; the class B rationale in `docs/medtrace.yml` holds.

## Plan

Plan stage, 2026-11-16, Software Architect role. The plan is the TASK records below (overlay: no
`docs/plans/<feature>.md`). Nothing is built until the human approves CR-007 and the answers to P-1 to
P-4. All tasks on `fix/cr-007-review-followups`, one commit per QA-approved task with its records.

### Tasks

| Order | Task | PRB | SR (AC) | RISK (`mitigates`) | Size | Depends on | Status |
|---|---|---|---|---|---|---|---|
| 1 | [TASK-229](../design-outputs/tasks/TASK-229-clear-message-when-the-budget-check-has-no-manifest.md) Clear message and exit 1 when the budget check has no manifest | 093 | SR-026 AC 7 | — | XS | — | approved (`92f1b05`) |
| 2 | [TASK-230](../design-outputs/tasks/TASK-230-correct-the-frontend-module-design-to-what-exists.md) Correct ADD-021, arc42 05 and 12 to the built frontend module units | 091 | SR-015, SR-016 (design records) | — | S | — (parallel with 1) | approved (`4eeef74`) |
| 3 | [TASK-232](../design-outputs/tasks/TASK-232-answer-a-logged-503-when-the-upload-cannot-be-spooled.md) Answer a logged 503 problem when the upload body cannot be spooled to disk | 092 | SR-013 AC 1, SR-027 AC 3 | 007 | M | — | new (1.2) |
| 4 | [TASK-231](../design-outputs/tasks/TASK-231-record-the-upload-scratch-space-residual.md) Record the upload scratch-space residual in RISK-007 and DEPLOY.md — round 2 | 092 | SR-013 AC 1 | 007 | S | 3 (states what TASK-232 built) | approved (QA round 2) |
| — | **Checkpoint** | | | | | 1–4 | backend suite, Ruff, Black; frontend suite, lint, typecheck and `npm run build` green; OpenAPI and generated types without drift; `traceability-check` 0 errors |

TASK-232 commits only its own files (`git add` by path): the working tree holds TASK-231's round 1 edits
(RISK-007, PRB-092, DEPLOY.md, section 11), which stay uncommitted until TASK-231 round 2 passes QA.

**What TASK-231 round 2 must state** (its own Objective and Steps are updated by the round 2 author to
match; RISK-007, PRB-092, DEPLOY.md and section 11 are edited only by TASK-231):

- **Fixed behaviour after TASK-232 (R1-1):** a full scratch directory in the API container makes the
  upload answer 503 `application/problem+json` `upload-storage-unavailable` with `Retry-After: 30`; the
  form shows "The server could not receive the file …"; nothing is stored in the object store or the
  database; the API writes an ERROR record (route template and errno, `ENOSPC`); the user can retry.
  Replace the round 1 wording ("a 5xx", "fails loudly") with this exact behaviour; mention the plain 400
  only as the behaviour before TASK-232 (PRB-092 Investigation). Where it applies (DEPLOY.md, RISK-007 Sequence of events and residual paragraph,
  section 11 row, PRB-092 Impact, Safety evaluation and Resolution), say what the operator sees: the API
  ERROR log line and the 503 in the proxy access log; tell the operator to monitor the free space.
- **Both directories (R1-2):** the API container's temporary directory (`/tmp` unless `TMPDIR` is set) and
  the reverse-proxy container's nginx client-body temporary directory; a full proxy directory makes
  nginx answer its own 500 and log at `crit`, before the API sees the request.
- **Sizing (R1-2):** about 300 MiB free per concurrent maximum-size upload where both directories share
  a disk (the usual Docker data root on one host), about 150 MiB in each otherwise.
- **RISK-007:** a Risk control measures row for TASK-232 — "Spool failure on upload detected, logged at
  ERROR and answered 503 problem+json with a retry instruction; nothing stored", type Protective,
  implemented by SR-013 AC 1, SR-027 AC 3 and TASK-232, verified by TS-007 TC-007.17 and TS-011
  TC-011.7 — beside the information row; scores 3 × 2 `alarp` unchanged with the reasoning of the
  §7.4 analysis above; version line.
- **PRB-092 (R1-3):** replace "Open decision for a human" with a pointer to CR-007 D-1, D-7 (and P-5);
  Resolution names TASK-232 and TASK-231; status `resolved` once both pass QA (D-7, unless the human keeps
  D-4 at P-5).
- **Implementation record (R1-4):** "a DB failure attempts to delete the object" (best effort,
  `backend/app/attachments/service.py:126-132`), not "deletes".

### Plan risks

| Risk | Impact | Mitigation |
|---|---|---|
| CR-006 changes RISK-007, ADD-021 or TS-018 before it merges | Record edits conflict | Rebase onto the CR-006 head before each task; bump from the version found |
| The missing-manifest branch is written as a pass | A budget breach hidden | Test asserts exit 1 and no "within the budget"; QA mutant |
| ADD-021 loses the deferred design | The registry is forgotten | ADD-021 names TASK-100, TASK-101 and PRB-048 as the deferred build |
| A FastAPI upgrade stops raising the parse 400 `from` its cause | The 503 mapping stops silently; back to an unlogged 400 | TC-007.17 runs against the locked FastAPI and fails (400 instead of 503); relied-on behaviour recorded in SOUP-002, reviewed at every dependency change (PLAN-002) |
| The mapping is too broad | A client error becomes a 503 | Only a 400 whose cause is an `OSError`, only on the attachments router; malformed-body regression cases and a mutation check without the cause check |
| TASK-232's commit picks up TASK-231's uncommitted record edits | Records committed before QA approved them | `git add` by path; QA checks the commit's file list |

## Version history

- 1.0 (2026-11-16) — Created with the Plan (Software Architect role) from the human decision D-1 ("Sí, CR-007"). `resolves` PRB-091 and PRB-093; `relates_to` PRB-092 (P-3). Change analysis: `affects_controls` (RISK-007 gains a cause and an information measure), no new hazard, class B unchanged. TASK-229 to TASK-231 new. Open questions P-1 to P-4 for the human. `open`.
- 1.1 (2026-11-16) — Plan gate: the human answered P-1 to P-4 (D-2 to D-5) and approved the plan (D-6). No scope change. `open`.
- 1.2 (2026-11-16) — After TASK-231 QA round 1 (R1-1: a full scratch directory answers a plain, unlogged 400, not a 5xx; R1-2: nginx buffers a second copy), the human decided D-7 ("Add a code fix in CR-007"). Software Architect role: TASK-232 added (logged 503 `upload-storage-unavailable` on the attachments router; additive OpenAPI response); PRB-092 `relates_to` → `resolves`, superseding D-4; D-5 sizing amended to about 300 MiB where the directories share a disk; P-5 asks the human to confirm both. Every "5xx"/"loud" statement about the behaviour before TASK-232 corrected (Reason, Scope, D-1, P-3, P-4, change analysis). §7.4 analysis redone: RISK-007 gains a protective code measure beside the information measure; no new hazard; residual 3 × 2 `alarp` unchanged; class B unchanged. Plan: TASK-232 before TASK-231 round 2, with what round 2 must state. `open`; the plan gate for TASK-232 is the human's approval of 1.2.
- 1.3 (2026-11-16) — D-8: the human approved TASK-232 and answered P-5 (PRB-092 resolved by CR-007; about 300 MiB sizing). No scope change. `open`.
- 1.3 (2026-11-16, QA) — TASK-231 round 2 approved: its plan row status updated; PRB-092 `resolved` (D-8). No scope change. `open`.
