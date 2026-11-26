---
id: CR-008
type: change-request
title: Install the DICOM viewer module in every environment and make its frame path work
status: in_progress
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-11-25"
updated: "2026-11-26"
branch: bug/dicom-module-install
risk_impact: affects_controls
links:
  - target: PRB-048
    relation: resolves
  - target: PRB-046
    relation: resolves
  - target: PRB-094
    relation: resolves
  - target: PRB-095
    relation: resolves
  - target: SR-017
    relation: relates_to
  - target: SR-015
    relation: relates_to
  - target: SR-016
    relation: relates_to
  - target: SR-026
    relation: relates_to
  - target: SR-028
    relation: relates_to
  - target: SR-013
    relation: relates_to
  - target: RISK-003
    relation: relates_to
  - target: RISK-007
    relation: relates_to
  - target: SOUP-015
    relation: relates_to
  - target: ADD-004
    relation: relates_to
  - target: ADD-015
    relation: relates_to
  - target: ADD-022
    relation: relates_to
  - target: TASK-073
    relation: relates_to
  - target: TASK-101
    relation: relates_to
  - target: TASK-102
    relation: relates_to
  - target: TS-005
    relation: relates_to
  - target: TS-010
    relation: relates_to
  - target: TS-013
    relation: relates_to
  - target: TS-019
    relation: relates_to
  - target: PRB-006
    relation: relates_to
  - target: PRB-075
    relation: relates_to
  - target: CR-006
    relation: relates_to
  - target: SOUP-037
    relation: relates_to
  - target: ADD-021
    relation: relates_to
  - target: TASK-233
    relation: relates_to
  - target: TASK-234
    relation: relates_to
  - target: TASK-235
    relation: relates_to
  - target: TASK-236
    relation: relates_to
  - target: TASK-237
    relation: relates_to
  - target: TASK-238
    relation: relates_to
  - target: TASK-239
    relation: relates_to
  - target: TASK-240
    relation: relates_to
  - target: ADD-012
    relation: relates_to
  - target: ADD-014
    relation: relates_to
tags:
  - configuration-management
  - dicom
  - github:sancharly/medhub#35
---

## Reason

The CR-001 anomaly review (TASK-154) and its QA found that SR-017 (DICOM image opening and rendering)
has no working backend in any environment:

- **PRB-048 (major):** the `medhub-dicom-viewer` package (`backend/modules/dicom_viewer/pyproject.toml`,
  entry point `dicom-viewer` in group `medhub.modules`) is installed nowhere. `backend/pyproject.toml`
  neither depends on it nor declares a uv source or workspace, `backend/uv.lock` has no entry for it, and
  the Dockerfile only copies the `modules/` folder. `discover_modules()` (`backend/app/modules/discovery.py`)
  therefore finds nothing and `GET /api/v1/modules/dicom-viewer/studies/{attachment_id}` is never mounted
  (404). ADR-0005 requires a plugin to be "build/deploy-time installed (package present in the image)".
  The module tests pass only because `backend/modules/dicom_viewer/tests/conftest.py` puts the module on
  `sys.path` itself. The frontend "Open in viewer" link (`frontend/src/core/clinical/AttachmentItem.tsx`)
  never renders, and if it did it would point at the core `/attachments/{id}` download URL, not at a viewer.
- **PRB-046 (minor):** once installed, `GET /studies/{id}?frame=N` cannot succeed: `stream_dicom`
  (`backend/modules/dicom_viewer/dicom_viewer/dicom.py`) reads `ds.pixel_array`, which needs NumPy, and
  compressed transfer syntaxes also need a decoder plugin. Neither is declared, and the production image
  is built with `uv sync --frozen --no-dev`.

One CR bundles both: PRB-046 is masked by PRB-048 and becomes reachable the moment PRB-048 is fixed, they
touch the same module, and they share one verification run.

**Dependency PRB-006 (satisfied).** Installing the module makes the frame path reachable, so its size and
decompression bound must already be in place. It is: PRB-006 is `resolved` and its CR-006 is `closed`
(2026-11-16). At `396e9de` the router opens the attachment with `max_bytes=dicom_max_stored_bytes()`
(rule `dicom_stored_size_exceeded`), and `stream_dicom` runs `_check_declared_decoded_size` on a
`stop_before_pixels=True` header read before any decode, with any decode exception mapped to
`dicom_decode_failed` and no partial bytes (SR-017 AC 6, TS-019 TC-019.1 to TC-019.4). CR-008 must not
weaken these checks; it makes them verifiable with a real decode for the first time.

**Coordination with #29 (phase 8, TASK-100 to TASK-103).** The in-app viewer is built there: TASK-102
renders client-side with Cornerstone3D from bytes fetched "only" from the module endpoint (ADR-0008).
CR-008 delivers the backend that #29 needs and decides what the attachment list shows until #29 lands
(D-5). It does not build any frontend module, registry or viewport.

## Scope

### In scope

| PRB | Crit. | State at `396e9de` (evidence) | Change |
|---|---|---|---|
| PRB-048 | major | Module package not installed in dev, CI or the production image; router not mounted; tests rely on a `sys.path` insertion; "Open in viewer" link targets the core download URL | Install the module from the lock in every environment (D-1, D-2); fail CI when the production image does not discover it (D-6); run the module tests against the installed package (D-7); resolve the link (D-5) |
| PRB-046 | minor | NumPy and decoder plugins undeclared; `pixel_array` cannot decode in any environment | Declare NumPy (D-2); support an explicit allow-list of transfer syntaxes and refuse the rest before decoding (D-3); correct the frame response media type (D-4); real-decode tests on fixtures (D-7) |
| PRB-094 | major | Upload validation (`backend/app/attachments/dicom_validation.py:19`) inflates a Deflated upload without a bound (pydicom 3.0.2); added at the Plan gate (D-B) | Inflate a Deflated upload with the shared bounded helper under the 1 GiB `dicom_max_decoded_bytes` setting before validation, refuse above it, store nothing (TASK-240) |

### Decisions to take (D-1 to D-7)

Items marked **for approval** are the human's choice; the others are proposals that the approval of this
CR confirms. Each states the options and the recommendation; nothing is chosen silently.

- **D-1. How the module is installed — for approval.**
  - (a) **uv workspace member:** `backend/pyproject.toml` gains `[tool.uv.workspace] members =
    ["modules/*"]`, `[tool.uv.sources] medhub-dicom-viewer = { workspace = true }` and
    `medhub-dicom-viewer` in `[project] dependencies`. One lock for host and modules; a future module is a
    new folder plus one dependency line; uv installs workspace members editable unless `--no-editable`.
  - (b) **path dependency:** `[tool.uv.sources] medhub-dicom-viewer = { path = "modules/dicom_viewer" }`
    plus the dependency line. Equivalent result for one module; each future module repeats the source
    entry; no shared workspace constraints.
  - *Recommendation:* (a). It matches ADR-0005 (a module is its own package, the image installs every
    module it ships), keeps one lock (SR-028), and scales to the next module with no new mechanism. The
    production image installs it non-editable (`uv sync --frozen --no-dev --no-editable`) so the image
    does not depend on the `modules/` source tree at run time; the architect confirms the flags. Either
    option needs `backend/uv.lock` refreshed.
- **D-2. Where the module's runtime dependencies are declared — proposal.** The module declares what it
  imports in its own `pyproject.toml` (`numpy`, `pydicom`, and any decoder chosen in D-3), resolved to the
  single lock; the host keeps `pydicom` for upload validation (`backend/app/attachments/dicom_validation.py`).
  *Recommendation:* module-owned dependencies, so installing or removing a module carries its
  dependencies with it (ADR-0005). Alternative: declare NumPy in `backend/pyproject.toml`; simpler today,
  but the host then carries a dependency only a module uses.
- **D-3. Which transfer syntaxes the frame path supports — for approval.** The whole-object path (no
  `frame`) returns the stored bytes unchanged for every transfer syntax and is not affected; the
  Cornerstone3D viewer (#29) decodes compressed syntaxes in the browser.
  - (a) **Native only, NumPy and no plugin:** Implicit VR Little Endian (`1.2.840.10008.1.2`), Explicit VR
    Little Endian (`1.2.840.10008.1.2.1`), Deflated Explicit VR Little Endian (`1.2.840.10008.1.2.1.99`),
    Explicit VR Big Endian (`1.2.840.10008.1.2.2`, retired) and RLE Lossless (`1.2.840.10008.1.2.5`,
    pydicom's own decoder). Every other syntax — JPEG Baseline/Extended/Lossless, JPEG-LS, JPEG 2000,
    HTJ2K, MPEG/HEVC video, and a missing or unknown UID — is refused before decoding with a 400 problem,
    rule `dicom_transfer_syntax_unsupported`, naming the UID.
  - (b) (a) **plus the JPEG family** through decoder plugins (pylibjpeg with `pylibjpeg-libjpeg` and
    `pylibjpeg-openjpeg`, or Pillow, or `python-gdcm`). Each plugin is a new SOUP item with an anomaly
    review, a new RISK-003 cause (decoder defect producing wrong pixels) and a licence review
    (`pylibjpeg-libjpeg` is reported as GPL-3.0; to be confirmed).
  - (c) Uncompressed only, without RLE Lossless.
  - *Recommendation:* (a). It needs no SOUP beyond NumPy, every supported syntax is lossless so the frame
    equals the acquired data, and the refusal is an explicit allow-list checked from the header, so an
    unsupported object can never be partly decoded. Compressed studies stay viewable through the
    whole-object path. Revisit (b) if a server-side consumer of compressed frames appears.
- **D-4. What a frame response is — for approval.** Today a successful `?frame=N` returns
  `pixel_array[N].tobytes()` (raw decoded samples, no rows, columns or data type) labelled
  `application/dicom`, which is wrong: it is not a DICOM object.
  - (a) Keep the raw samples and label them `application/octet-stream`; document the layout (native
    little-endian samples of the decoded array, rows x columns x samples per pixel, in the object's
    declared order) in the route's `responses=` and in ADD-015.
  - (b) Return a single-frame DICOM Part-10 object (`application/dicom`) built from the source header and
    frame N. Self-describing, consumable by Cornerstone3D, but needs an encoding path and more tests.
  - (c) Leave as is (rejected: a mislabelled payload is the kind of silent misinterpretation RISK-003 names).
  - *Recommendation:* (a), confirmed with #29 before approval. TASK-102 mentions "optional `?frame=`", but
    Cornerstone3D's DICOM image loader consumes Part-10 objects, so the planned viewer would use the
    whole-object path; with no consumer, the smallest honest fix is the correct media type. If #29 needs
    per-frame fetches, choose (b) instead.
- **D-5. What happens to the frontend "Open in viewer" link — for approval.**
  - (a) **Remove the link now;** every attachment keeps its Download link. #29 (TASK-101, TASK-102)
    introduces the entry point to the in-app viewer route, gated by `GET /me/modules`. TS-005 TC-005.6
    (client-side evidence for SR-015 AC 3 and AC 4) is retired or reworded in the Plan stage; SR-015 keeps
    its server-side verification (TC-005.2).
  - (b) Point the link at `GET /api/v1/modules/dicom-viewer/studies/{id}`. It would download the same
    object a second way under a "viewer" label, which is still not a viewer.
  - (c) Leave it: once the module is installed and enabled, the link would render and open the core
    download under a "viewer" label (the PRB-048 defect itself).
  - *Recommendation:* (a). No control should claim to open a viewer that does not exist (SR-017 AC 11),
    the gated entry point is rebuilt by #29 against the real route, and this CR then changes no frontend
    behaviour beyond the removal. #29's TASK-101 and TASK-102 must be told the link is gone.
- **D-6. CI check that the production image discovers the module — proposal.** A step in the Docker Build
  job (`.github/workflows/ci.yml`), next to "Check production dependency set" (TS-013 TC-013.8), runs
  Python in `medhub-backend:ci` and fails unless `importlib.metadata.entry_points(group="medhub.modules")`
  contains `dicom-viewer`, `dicom_viewer.manifest` imports, and `numpy` imports. *Recommendation:* that
  step, plus an assertion in the started-stack smoke test that an unauthenticated
  `GET /api/v1/modules/dicom-viewer/studies/<random uuid>` answers 401, not 404 (the router is mounted).
- **D-7. Module tests against the installed package — proposal.** Remove the `sys.path` insertion from
  `backend/modules/dicom_viewer/tests/conftest.py`; the existing CI step (`uv run pytest
  modules/dicom_viewer/tests`) then imports the installed package, and a guard test fails when the entry
  point is not discoverable in the test environment. Replace the stubbed decode with real decodes on
  fixtures generated in the tests (pydicom and NumPy: one single-frame and one multi-frame object per
  supported syntax; a compressed-syntax object for the refusal, whose pixel data need not be valid
  because it is refused from the header). The size-bound tests (TC-019.1 to TC-019.4) keep their stubs
  where a real 1 GiB decode would be impractical, and gain one real decode at a small size.

### Requirements decision

SR-017 is updated to 1.7 (`in_review`) with AC 7 to AC 11: installation in every environment, the
whole-object path, the supported-syntax decode, the loud refusal of the rest, and the frontend entry point
(see SR-017). No new SR: the change restores the intended behaviour of SR-017 and adds its missing
acceptance criteria; installation in the image is part of making SR-017 available, not a separate need.
No RR: no regulation drives a new need (the configuration-management obligations are already in SR-028
and the lifecycle plans). No UN or NFR change.

IEC 62304 §5.2.2 walk for this change: (a) functional — AC 9, AC 10; (b) inputs/outputs — supported UIDs,
frame range, media type (D-3, D-4); (c) interfaces — module endpoint, AC 7; (d) operator messages —
problem responses with rule and UID, AC 10; (e) security — unchanged, SR-005/SR-015 guards and audit stay
as built (TASK-073); (f) usability — AC 11; (g) data — not applicable, no schema change; (h) installation
— AC 7; (i) operation/maintenance — not applicable beyond AC 7; (j) IT-network — not applicable;
(k) user documentation — the supported transfer syntaxes go in `infra/DEPLOY.md` or the module notes
(Plan stage decides); (l) regulatory — not applicable, no new RR.

### Records the later stages must touch (not written in Specify)

- **Risk stage (§7.4):** RISK-003 revisit — new cause "unsupported or mis-identified transfer syntax
  decoded" and its control (header allow-list before decode, SR-017 AC 10); the "render only from the
  authoritative object" and size-bound rows become verifiable with a real decode; re-score from evidence;
  add `relates_to` the NumPy SOUP (and any D-3 (b) decoder). RISK-007 — the module becomes available, and
  PRB-075 (start-up fails when an enabled module disappears) becomes reachable once the module is
  installed and enabled; assess, not fix, here.
- **SOUP:** a new `soup` record for NumPy (exact locked version, anomaly review dated), and one per
  decoder plugin if D-3 (b) is chosen; SOUP-015 updated (relied-on requirement: pixel decode for the
  D-3 syntaxes; note that NumPy is now present).
- **Plan stage:** ADD-015 (installation mechanism, module dependencies, transfer-syntax allow-list,
  frame media type; `relates_to` the new SOUP), ADD-004 (SOUP list), ADD-022 (entry point removed until
  TASK-102, if D-5 (a)); arc42 sections 05 and 07 (module present in the image); an ADR only if the
  architect judges D-1 an architectural decision beyond ADR-0005. TASK records for each change. Test
  records: TS-019 (real-decode, refusal and media-type cases; TC-019.5 becomes executable for the backend
  frame), TS-010 (discovery in the installed environment), TS-013 (the D-6 CI check), TS-005 (TC-005.6, if
  D-5 (a)).

### Out of scope

- The frontend module system and viewer (TASK-100 to TASK-103, #29), including SR-016 AC 2 and SR-026 AC 3
  ("first rendered image within 10 s"), which stay deferred to #29 as CR-006 D-35 and CR-007 D-2 recorded.
- PRB-075 (start-up with an enabled-but-missing module): related, not fixed here.
- Changing the PRB-006 bounds or the SR-005/SR-015 guards on the module route.
- DICOMweb or any new endpoint.
- The core OpenAPI export: the module router is not part of it (PRB-006 resolution), so no
  `openapi.json` or generated-types change is expected; if the architect finds otherwise, the CLAUDE.md
  contract workflow applies.

### Boundaries

- **Ask first:** any new runtime dependency beyond NumPy (D-3 (b)); any change to `backend/app` beyond what
  installation needs, the shared DICOM helper `app.modules.dicom_support` with its module allow-list entry
  (TASK-234) and the bounded inflation in upload validation (TASK-240, D-B); any change to the size bounds or the module access guard; any frontend change beyond
  D-5.
- **Never:** return partial or unlabelled pixel data; decode before the transfer-syntax and size checks;
  let a production image that does not discover the module pass CI; edit an `approved` record without
  bumping its version, setting `in_review`, removing its approval record and adding a version-history line.

## Risk and Plan stages (2026-11-25, Software Architect role)

**Risk (§7.4).** No new hazard and no class change. RISK-003 1.6: two causes added (unsupported or
mis-identified transfer syntax decoded; decoded frame mislabelled as DICOM), four control rows; scores
unchanged, 4 × 3 → 4 × 2, alarp. RISK-007 1.21: two causes added (module absent from an environment;
pydicom's unbounded inflation of Deflated objects, on the frame path and in the host's upload validation),
two control rows; PRB-075 assessed as still unreachable with one module; scores unchanged, 3 × 2, alarp.
Both `in_review` for the human's acceptance. No SR-017 AC added: the Deflated inflation bound is covered by
AC 6 ("before decoding any pixel data") and AC 10.

**SOUP.** SOUP-037 NumPy 2.5.5 (new, anomaly review 2026-11-25); SOUP-015 pydicom 3.0.2 1.3 (pixel decoding
relied on; re-reviewed 2026-11-25; unbounded Deflated inflation recorded). No decoder plugin (D-3 (a)).
ADD-004 is obsolete (the SOUP list is the `soup` records) and is not changed.

**Architecture.** ADR-0024 (proposed): modules are uv workspace members with their own dependencies, a
pinned build backend, installed non-editable in the image (refines ADR-0005). ADD-015 1.3 (allow-list,
check order, bounded inflation, frame layout, installation; `implements` SR-028; SOUP-037), ADD-022 1.1
(no viewer entry point until #29). No core OpenAPI change expected (the module router is not in the core
export); TASK-234 and TASK-235 verify it.

**Tasks, in order.**

| Task | Title | Implements | Mitigates | Depends on |
|---|---|---|---|---|
| TASK-233 | Install the module as a uv workspace member (lock, Dockerfile, module pyproject, D-7 guard test) | SR-017 AC 7, SR-016, SR-028 | RISK-007 | — |
| TASK-234 | Refuse unsupported transfer syntaxes and bound Deflated inflation before any decode | SR-017 AC 6, AC 10 | RISK-003, RISK-007 | TASK-233 |
| TASK-235 | Return decoded frames as `application/octet-stream`, real-decode tests | SR-017 AC 6, AC 8, AC 9 | RISK-003 | TASK-234 |
| TASK-236 | CI image discovery check and smoke-test 401 (D-6) | SR-017 AC 7, SR-028 | RISK-007 | TASK-233 (parallel with 234, 235) |
| TASK-237 | Remove the "Open in viewer" link, keep Download (D-5) | SR-017 AC 11 | RISK-003 | — (parallel) |
| TASK-240 | Bound the inflation of Deflated DICOM uploads before validation (PRB-094, D-B) | SR-013 AC 6 | RISK-007 | TASK-234 (parallel with 235, 236) |
| TASK-238 | Documentation: arc42 05, 07, 12, ADD-012, ADD-014, ADD-015, ADD-021, DEPLOY.md (P-2) | SR-017, SR-028 | RISK-003 | TASK-233 to TASK-237, TASK-240 |
| TASK-239 | Verification, risk re-score, PRB-048, PRB-046 and PRB-094 resolutions | SR-017 AC 6 to AC 11, SR-013 AC 6 | RISK-003, RISK-007 | all |

Build order: TASK-233, TASK-234, then TASK-235, TASK-236 and TASK-240 (parallel), TASK-237 (any time),
TASK-238, TASK-239. TASK-234 1.1 puts the transfer-syntax read and the bounded inflation in the host
helper `app.modules.dicom_support` so that TASK-240 reuses it.

Checkpoints: after TASK-233 (module installed, whole backend suite green, image runs the wheel); after
TASK-235 and TASK-236 (backend complete: module suite with real decodes, Docker Build job with the new
step) and TASK-240 (upload bound); after TASK-237 and TASK-238 (frontend on Node 20+, documentation reviewed), then TASK-239.

**Open questions for the human (Plan gate)** — all answered on 2026-11-25, see D-B.

- Q-1. Upload validation inflates Deflated uploads without a bound (`app/attachments/dicom_validation.py`,
  pydicom 3.0.2): reachable today by any user who may upload. Recommendation: raise a separate PRB (major,
  availability) and keep it out of CR-008, whose boundary excludes `backend/app` changes beyond
  installation; or bring it into CR-008 as an eighth task. **Answered (D-B): into CR-008** — PRB-094,
  TASK-240.
- Q-2. The Deflated inflation bound on the frame path is `dicom_max_decoded_bytes` (1 GiB), the existing
  AC 6 setting; no new setting. Confirm. **Answered (D-B): confirmed**, for the frame path and the upload path.
- Q-3. TASK-234 reads the transfer syntax with pydicom's private `_read_file_meta_info` (public
  `read_file_meta_info` takes a path only), pinned by a test and recorded in SOUP-015. Alternative: a
  hand-written group 0002 reader. Recommendation: the pinned private call. **Answered (D-B): the pinned
  private call.**
- Q-4. Accept ADR-0024. **Answered (D-B): accepted.**

## Verification approach

IEC 62304 §8.2.1 (change approval), §8.2.3 (verification of changes), §5.5 (unit verification, class B),
§5.6 (integration) and §9.7 (verification of the problem resolution).

- **PRB-048, installation (SR-017 AC 7):** `uv sync` from a clean checkout, then
  `uv run python -c "from importlib.metadata import entry_points; print([e.name for e in
  entry_points(group='medhub.modules')])"` prints `['dicom-viewer']`; the same in the CI test environment
  (D-7 guard test) and in `medhub-backend:ci` (D-6 step), which fails on `396e9de` and passes after the
  change. Started stack: the unauthenticated module request answers 401, not 404; an authenticated user
  without the module enabled gets 403 (existing guard, TASK-073).
- **PRB-048, tests against the installed package (D-7):** with the `sys.path` insertion removed, the
  module suite passes; uninstalling the package (or reverting the `pyproject.toml` change) makes the guard
  test and the import fail, shown once as a negative control.
- **PRB-046, decode (SR-017 AC 9):** for each D-3 supported syntax, single- and multi-frame fixtures:
  `?frame=N` returns 200, the D-4 media type, and bytes equal to the fixture's known pixel values for
  frame N; frame N = number of frames answers the existing 400 problem. Run in the module suite and once on
  the started stack (TS-019 TC-019.5, backend frame part).
- **PRB-046, loud refusal (SR-017 AC 10):** a JPEG Baseline, a JPEG 2000 and a missing-UID fixture each
  answer 400 `application/problem+json` with rule `dicom_transfer_syntax_unsupported` naming the UID, no
  pixel bytes, and `pixel_array` never called; negative control: drop the allow-list and the tests fail.
  The PRB-006 tests (TC-019.1 to TC-019.4) stay green, and their order (stored size, then transfer syntax
  or declared size, then decode) is asserted.
- **Whole-object path (SR-017 AC 8):** without `frame`, the response body is byte-identical to the stored
  object for a compressed and an uncompressed fixture, media type `application/dicom`.
- **Frontend (SR-017 AC 11, D-5):** `AttachmentItem` tests: no control labelled or linking as a viewer for
  any attachment, Download kept; `npm run test -- --run`, lint, typecheck and build on Node 20 or later.
- **Whole change:** backend suite with coverage, module suite, Ruff, Black and mypy; Docker Build job
  including the D-6 step; `traceability-check` with no errors for this CR's records.

## Verification summary

Executed by TASK-239 on 2026-11-26 on branch `bug/dicom-module-install`, head 5bd10e7 plus the task's working-tree changes (details and numbers in the TASK-239 Implementation record).

- Suites: module suite 84 passed; `tests/modules` 119; backend 1775 passed and 10 skipped, coverage 95.24 %; Ruff, Black, `mypy app` and `mypy` of the module clean; OpenAPI export identical to the committed file; frontend (Node 20.19.0) 412 passed, lint, typecheck and build clean; infra tests 178.
- Clean checkout: `uv sync --frozen --python 3.12`, entry points `['dicom-viewer']` (PRB-048).
- Negative controls, each failing as expected and passing restored: pre-TASK-233 image (image check exit 1), package uninstalled (TC-010.8), allow-list removed (TC-019.6), upload inflation check removed (TC-007.18), entry-point target `:nope` (the new `discover_modules()` assertion).
- Started stack (a scratch Compose project): module route 401 unauthenticated and 403 without the module; frame bytes equal to the known values, `?frame=<frames>` 400, JPEG Baseline 400 `dicom_transfer_syntax_unsupported`, whole object byte-identical; a deflate bomb under 1 MiB stored refused 400 in 1.8 s with the backend at 152 to 153 MiB and no restart (PRB-094). Smoke test: 75 passed, 1 failed (PRB-096, an older defect of the smoke test, outside this CR).
- PRB-048, PRB-046, PRB-094 and PRB-095 are `resolved` (PRB-095 by D-D: a fixed UID in the stored-bound test). RISK-003 (4 × 2) and RISK-007 (3 × 2) re-scored from the evidence, both alarp, unchanged; both stay `in_review` for the human's acceptance.
- Not verified: the Docker Build job and the full workflow on hosted CI (verified on hosted CI after push); the first rendered image within 10 s (SR-026 AC 3, #29); smoke test "0 failed" (PRB-096).

## Assumptions

- A-1. Class B is unchanged (`docs/medtrace.yml` `safety_class: B` and `CLAUDE.md` agree).
- A-2. PRB-006 is a satisfied dependency (resolved; CR-006 closed 2026-11-16; bounds present at
  `396e9de`), so CR-008 does not move it into scope.
- A-3. Installing the module makes it available, not enabled: a system administrator still enables it per
  group (SR-015); discovery registers it in the module registry at start-up as today.
- A-4. `medhub-backend` stays an unpackaged (virtual) uv project that imports `app` from the working
  directory; the architect confirms that a workspace or path source works with it and that the module's
  `app.*` imports resolve in the image.
- A-5. The planned viewer (ADR-0008, TASK-102) renders from the whole Part-10 object; the frame path has no
  planned consumer (to be confirmed with #29 under D-4).
- A-6. No `release` record exists, so no released version in use is affected and no notification is needed
  (PRB-048, PRB-046 safety evaluations).

## Open questions

- **P-1. Criticality.** PRB-048 `major` and PRB-046 `minor` are kept as recorded. *Recommendation:* no
  change; neither shows a wrong image.
- **P-2. Supported-syntax list in user documentation.** Whether the D-3 list belongs in `infra/DEPLOY.md`
  (operator) or only in ADD-015. *Recommendation:* ADD-015 plus one line in DEPLOY.md, since operators
  import studies and should know which ones the frame path refuses.

## Decisions

- **D-A (2026-11-25):** the human (Carlos Santiago Liceras) answered in chat at the Specify gate,
  approving CR-008 and SR-017 1.7 (AC 7 to AC 11) and taking every recommendation:
  D-1 uv workspace member, image built with `uv sync --frozen --no-dev --no-editable`;
  D-3 option (a), the transfer syntaxes NumPy decodes without a plugin (Implicit and Explicit VR
  Little Endian, Deflated Explicit VR Little Endian, Explicit VR Big Endian, RLE Lossless), all others
  refused with `dicom_transfer_syntax_unsupported`; D-4 the frame response is relabelled
  `application/octet-stream` with a documented layout; D-5 the "Open in viewer" link is removed now
  and Download stays, #29 adds the gated entry point; D-2, D-6, D-7, P-1 and P-2 as proposed. The
  decision was relayed by the coordinating agent; the human's MedTrace approval of this CR and of
  SR-017 1.7 confirms it.
- **D-B (2026-11-25):** the human (Carlos Santiago Liceras) answered in chat at the Plan gate:
  Q-1 the unbounded inflation of Deflated uploads in upload validation is taken into CR-008, not a
  separate change (PRB-094, major, resolved by this CR; TASK-240); Q-2 the 1 GiB
  `dicom_max_decoded_bytes` setting bounds the inflation on both paths, no new setting; Q-3 the transfer
  syntax is read with pydicom's private `_read_file_meta_info`, pinned by a test and recorded in SOUP-015;
  Q-4 ADR-0024 accepted. The human approved the plan, TASK-233 to TASK-239, and accepted the residual risks
  of RISK-003 (4 × 2, alarp) and RISK-007 (3 × 2, alarp) with their ALARP arguments; TASK-240 and the
  TASK-234 1.1, TASK-238 1.1 and TASK-239 1.1 revisions follow from Q-1 and were written after that
  answer. The decision was relayed by the coordinating agent; the human's MedTrace approval of the tasks
  and of RISK-003 1.6 and RISK-007 1.21 confirms it. Tasks stay `draft` until built and are approved by QA;
  the RISK records stay `in_review` until that MedTrace approval.
- **D-C (2026-11-25):** the human answered in chat, approving the TASK-234 1.1 revision: the shared host
  helper `backend/app/modules/dicom_support.py` (transfer-syntax read, bounded inflation), used by the
  module and by TASK-240, and its entry in the module-boundary allow-list; and TASK-240, TASK-238 1.1 and
  TASK-239 1.1 with it. Relayed by the coordinating agent; the human's MedTrace approval confirms it.
- **D-D (2026-11-26):** the human answered in chat: PRB-095 (TC-019.4 stored-bound test fails about one
  run in 45 because its `_dicom` helper uses a random-length UID) is taken into CR-008 and resolved by
  TASK-239 with a fixed UID in `test_size_bounds.py`. Relayed by the coordinating agent; the human's
  MedTrace approval confirms it.

## Version history

- 1.0 (2026-11-25) — Specify stage of /ship-feature for GitHub sancharly/medhub#35 (Product Owner role).
  Created with Reason, Scope (D-1 to D-7), Verification approach; SR-017 1.7 drafted with AC 7 to AC 11.
  Specify-gate decisions recorded as D-A.
- 1.1 (2026-11-25) — Risk and Plan stages (Software Architect role): RISK-003 1.6, RISK-007 1.21, SOUP-037
  (new), SOUP-015 1.3, ADR-0024 (proposed), ADD-015 1.3, ADD-022 1.1; TASK-233 to TASK-239 created (`draft`);
  links `relates_to` SOUP-037, ADD-021 and the tasks added; open questions Q-1 to Q-4 for the Plan gate.
- 1.2 (2026-11-25) — Plan-gate answers recorded as D-B (Software Architect role); Q-1 to Q-4 marked
  answered. PRB-094 (upload validation inflates Deflated uploads without a bound) taken into scope with
  `resolves`; TASK-240 added; TASK-234, TASK-238, TASK-239 revised to 1.1; scope table and "Ask first"
  boundary updated for the `backend/app` upload validation and the shared helper; links `relates_to`
  SR-013, ADD-012, ADD-014 and TASK-240 added; ADR-0024 accepted.
- 1.3 (2026-11-26) — D-D recorded: PRB-095 taken into scope with `resolves`, fixed in TASK-239
  (orchestrator).
- 1.4 (2026-11-26) — TASK-239: Verification summary added (Software Developer role). Status stays `in_progress`.
