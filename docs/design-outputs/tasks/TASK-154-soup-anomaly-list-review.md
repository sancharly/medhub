---
id: "TASK-154"
type: task
title: "First SOUP anomaly-list review"
status: approved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-22"
links:
  - target: "RISK-010"
    relation: mitigates
  - target: "SR-028"
    relation: implements
  - target: "TASK-155"
    relation: relates_to
  - target: "TASK-157"
    relation: relates_to
  - target: "TASK-158"
    relation: relates_to
  - target: "RISK-012"
    relation: relates_to
tags: ["soup", "regulatory", "phase:9-integration-system-testing-compliance", "control:protective", "cr:CR-001"]
---

# TASK-154 — First SOUP anomaly-list review

- **Software item / unit:** all (SOUP crosses every item)
- **Depends on:** TASK-155 (pinned image versions for SOUP-001, SOUP-020..024), TASK-157 (locked
  `boto3` version for SOUP-019), TASK-158 (SOUP-018 obsolete, so it is not reviewed), as
  `relates_to` links; the `soup` records in [`../../soup/`](../../soup/)
- **Branch:** `bug/soup-pinning` (CR-001)

## Objective

The `soup` records in [`../../soup/`](../../soup/) identify every SOUP item with its exact
version, but no published anomaly list has been reviewed yet (§7.1.2–7.1.3). Until that review
exists and is dated, the SOUP list cannot support a release. This task performs the first round
for SR-028 AC-6 and confirms the cadence in PLAN-002. It implements RISK-010's protective control
"anomaly and advisory review per version".

## Implementation detail

- Scope: every `soup` record whose status is not `obsolete`, which is SOUP-001..035 except SOUP-018.
  Review each one **at the version it records after TASK-155 and TASK-157**, never at a floating
  tag.
- For each record, check the published sources for that exact version and cite each one by name
  and URL:
  - the advisory databases: OSV (`osv.dev`, PyPI and npm ecosystems), GitHub Security Advisories,
    NVD;
  - the vendor's security page or release notes. Examples: nginx security advisories, PostgreSQL
    security information, the Redis and MinIO GitHub advisories, Python security announcements.
    For images, also the base OS of the pinned digest (Debian or Alpine, CR-001 A-5) at the level
    of the image's own advisories.
  Write the section "Anomaly list review": sources, date, every anomaly that applies to that
  version with a hazard-relevance judgement, or "none found". Set `anomaly_review` to the review
  date. Add the same entry to the change log. The record stays at the `1.1` set by
  TASK-155/157 (SOUP-002..017 and SOUP-025..035 were not touched before: bump them to `1.1`,
  remove the approval record). Every reviewed record goes to `in_review`.
- Prioritize the items behind a risk control: `cryptography` (encryption at rest, SR-022),
  `argon2-cffi` (password hashing), nginx (TLS/HSTS, SR-001), MinIO (server-side encryption),
  `pydicom` (image rendering, SR-017), SQLAlchemy (parameterized queries, SR-031), Redis (session
  integrity, SR-030), and `boto3`, which carries the SSE request since PRB-002.
- **MinIO distribution status (CR-001 D-4).** At the Risk stage (2026-10-22) the registry refused
  `minio/minio` and `minio/mc` (Docker Hub "pull access denied, repository does not exist or may
  require authorization"; quay.io 401), so TASK-155 pinned the locally cached releases. Confirm or
  refute from MinIO's own notices whether the community edition still publishes images, binaries
  and security fixes, and whether the pinned releases can still be obtained. If confirmed,
  escalate under AC-12:
  - a PRB for SOUP-022/023, covering obtainability on a fresh host (§5.8.5) and no upstream
    fixes (§6.1 f);
  - the risk input for RISK-007 (object storage cannot be deployed on a new host) and for
    RISK-010 / RISK-001 (SSE server without security fixes), each revised record linking
    `relates_to` → SOUP-022.
  Do not change the component (D-4).
- Any anomaly that could contribute to a hazardous situation goes to `risk-management` as a RISK
  record, new or an existing one revised, linking `relates_to` → the SOUP record. Any defect that
  affects MedHub becomes a PRB (`problem-report-resolution`). An upgrade found necessary is a
  separate CR (CR-001 out of scope).
- List every escalation, or "none", in CR-001 under a new subsection
  `### Anomaly review escalations (AC-12)` of `## Implementation plan`.
- PLAN-002 "SOUP monitoring (§6.1 f)": compare it with the cadence and owner actually applied.
  If it already matches, leave it unchanged and say so in the handoff. If not, revise it
  (`version` bump, approval record removed, `in_review`).
- Review published information only. Do not fetch or execute anything from a dependency's
  repository to test it.

## Acceptance criteria

- [x] CR-001 **AC-11**: every non-obsolete `soup` record has `anomaly_review` and an "Anomaly list
      review" section citing each source checked for its exact `soup_version`, with each applicable
      anomaly judged for hazard relevance or "none found". No section reads "Not yet performed".
      The image items are reviewed at their pinned versions.
- [x] CR-001 **AC-12**: each hazard-relevant anomaly is in a RISK record linking `relates_to` → the
      SOUP record; each MedHub-affecting anomaly has a PRB; CR-001 lists the escalations or "none".
      The MinIO distribution status is confirmed or refuted, with its source.
- [x] CR-001 **AC-13**: PLAN-002's SOUP monitoring section matches the cadence and owner applied.

## Definition of Done

- [x] Every reviewed `soup` record updated and left `in_review` for human approval
- [x] `traceability-check` shows no `soup_anomaly_review_stale` warning and no error for the
      touched records

## Implementation notes and evidence

Performed on 2026-10-22 by the Software Architect role in three parallel slices, then
consolidated. Every record cites its own sources and judgement in its "Anomaly list review"
section. This section summarizes them.

### Method (all slices)

- Published information only. Nothing was fetched from a dependency's repository to be built or
  run, and no package manager audit command was used.
- Each item was reviewed at the exact version it records after TASK-155 and TASK-157 (lock file
  or pinned image digest), never at a floating tag.
- **Classes of source:**
  - advisory databases: OSV (PyPI, npm, Go, Debian:13, Alpine), the GitHub Advisory Database and
    repository advisories, NVD CVE API 2.0;
  - vendor security pages and release notes: nginx.org, postgresql.org, python.org, Redis
    releases, the MinIO README, releases and dl.min.io, changelogs of the libraries;
  - registry metadata: npm registry, Docker Hub and quay.io APIs.
- **Base OS of images (A-5):** each image's package database was copied out of the pinned digest
  without running it (`docker create` + `docker cp`). Each source package was then queried in OSV
  at its installed version, and the Debian entries were triaged for an available fix.
- Each advisory was judged against its affected range and against how MedHub uses the item,
  cited by file.

### Results per record

| Slice | Record (version) | Result |
|---|---|---|
| Container/runtime | SOUP-001 Python 3.12.15 | Applicable, not affecting MedHub: CVE-2026-12345 (`tempfile`, no 3.12 fix; MedHub doesn't use `tempfile`); bundled pip 25.0.1 advisories (build time only, PRB-034). Debian base: no entry with a fix available |
| Container/runtime | SOUP-020 PostgreSQL 16.15 | None found. Debian base: no entry with a fix available |
| Container/runtime | SOUP-021 Redis 7.4.11 | Applicable, not affecting MedHub: CVE-2026-92925 (cluster bus, not enabled), GHSA-2r7g-8hpc-rpq9 (authenticated DoS, internal network). Alpine 3.21 base ends support 2026-11-01 → PRB-045 |
| Container/runtime | SOUP-022 MinIO RELEASE.2025-09-07T16-13-09Z | **Hazard-relevant**: CVE-2026-41145, CVE-2026-40344, CVE-2026-113466, CVE-2026-34204 (no community fix) → RISK-012, PRB-043. Other advisories and Go 1.24.6 stdlib entries not affecting or availability only. D-4 confirmed → PRB-042 |
| Container/runtime | SOUP-023 mc RELEASE.2025-08-13T08-35-41Z | No vendor advisory. Go 1.24.6 stdlib entries not hazard-relevant. Item unmaintained, image unobtainable → PRB-042 |
| Container/runtime | SOUP-024 nginx 1.31.8 | None found (all 2026 advisories fixed ≤ 1.31.7). Alpine 3.24 base: no entry |
| Backend | SOUP-002 FastAPI, SOUP-004 Uvicorn, SOUP-006 Pydantic, SOUP-007 pydantic-settings, SOUP-012 argon2-cffi, SOUP-013 redis-py, SOUP-014 Celery, SOUP-017 python-multipart | None found |
| Backend | SOUP-003 Starlette 1.3.1 | Starlette none found. Transitive anyio 4.14.0: three advisories, not affecting → PRB-047 |
| Backend | SOUP-005 gunicorn 26.0.0 | No advisory. Published bugs apply in principle but have no trigger in MedHub. The control-socket failure is the existing PRB-041 |
| Backend | SOUP-008 SQLAlchemy 2.0.51 | No advisory. Later bug fixes do not touch MedHub's parameterized-query paths |
| Backend | SOUP-009 Alembic 1.18.4 | Alembic none found. Transitive Mako 1.3.12: CVE-2026-102991 (Windows only), not affecting |
| Backend | SOUP-010 psycopg2-binary 2.9.12 | No advisory. Bundled libpq predates CVE-2026-6477, but MedHub uses no large objects: not affecting |
| Backend | SOUP-011 cryptography 49.0.0 | Applicable, not affecting: CVE-2026-69247 (PKCS#7 only) → PRB-047 |
| Backend | SOUP-015 pydicom 3.0.2 | No upstream anomaly applies (CVE-2026-32711 fixed in 3.0.2). Environment findings: NumPy not declared, so `?frame=` would fail loudly once reachable → PRB-046. The `dicom_viewer` module is installed in no environment, so the path returns 404 today (found by QA) → PRB-048 |
| Backend | SOUP-016 fhir-resources 8.2.0 | No advisory. Later validation fixes not hazard-relevant (RISK-002 unaffected) |
| Backend | SOUP-019 boto3 1.43.117 | boto3, botocore, s3transfer, jmespath none found. Transitive urllib3 2.7.0: three advisories, not affecting → PRB-047 |
| Frontend | SOUP-025 React, SOUP-026 react-dom, SOUP-028 TanStack Query, SOUP-029 MUI Material, SOUP-030 MUI Icons, SOUP-031/032 Emotion, SOUP-034/035 fonts | None found that applies to MedHub's use |
| Frontend | SOUP-027 react-router 7.18.0 | Applicable, not affecting: GHSA-qwww-vcr4-c8h2 (RSC CSRF; MedHub uses declarative client routing) |
| Frontend | SOUP-033 openapi-fetch 0.17.0 | None found. Not used by MedHub → PRB-044 |

SOUP-018 is `obsolete` (TASK-158) and was not reviewed. Every reviewed record has
`anomaly_review: "2026-10-22"`, a dated review section with no "Not yet performed", and a
change-log entry, and is `in_review`.

### Escalations (AC-12)

Listed in CR-001, "Escalations from TASK-154 (AC-12)":

- **RISK-012** (new, `in_review`; 4 × 2 → alarp; residual = initial until CR-002): object store
  compromised from the internal network or left unpatchable. It links `relates_to` → SOUP-022,
  SOUP-023, PRB-042 and PRB-043. It states the input for RISK-010, which TASK-159 applies: the
  MinIO path's residual probability goes from 1 to 2 (3 × 2 → alarp) until PRB-042 is resolved.
- **PRB-042** (major): MinIO community edition unmaintained, images unobtainable.
- **PRB-043** (critical): unfixed MinIO CVEs exposed by MedHub's configuration. It blocks any
  release until CR-002.
- **PRB-044** (minor): `openapi-fetch` declared but unused; ADD-004 misdescribes the client.
- **PRB-045** (minor): Redis image base OS Alpine 3.21 ends support on 2026-11-01.
- **PRB-046** (minor): NumPy not declared, so DICOM frame extraction fails loudly.
- **PRB-047** (minor): anyio, urllib3 and cryptography advisories that don't affect MedHub; upgrade
  at the next dependency change.
- **PRB-048** (major, found by the QA review of this task): the DICOM viewer module is installed in
  no environment. SR-017's viewer endpoint is never mounted and the "view" link never shows;
  download still works. It masks PRB-046. The human may change the criticality at approval.
- No other hazard-relevant anomaly was found.
- Human decisions of 2026-10-22: the MinIO mitigation goes to a separate CR-002, with no release
  before it; the MinIO hazard is a new RISK-012; PRB-043 is critical.

### MinIO distribution status (D-4): confirmed

From MinIO's own notices (evidence in SOUP-022 and PRB-042):

- **2025-10-15**, README commit `9e49d5e7a6`: source-only distribution, no more community
  binaries.
- **2025-10-16**: `RELEASE.2025-10-15T17-29-55Z` is published without assets. The pinned server
  release is the last one with binaries and images, and the pinned `mc` release is `mc`'s last.
- **2025-12-03**, commit `27742d4694`: maintenance mode.
- **2026-02-12**, commit `7aac2a2c5b`: no longer maintained.
- **April 2026**: both repositories archived.
- **2026-10-22**:
  - `dl.min.io` returns HTTP 410 for community downloads, with a no-security-updates notice.
  - Docker Hub returns 404 for `minio/minio` and `minio/mc`, and quay.io returns 401.
  - Every 2026 advisory is fixed only in AIStor.
  - The archived GitHub release binaries still answer (HEAD 200).

The component is not changed by CR-001.

### PLAN-002 "SOUP monitoring" (AC-13)

All three slices applied the section as written: a review at this dependency change (CR-001),
owned by the Software Architect role with the human accountable, with the review date in
`anomaly_review` and a maximum interval of 365 days. **PLAN-002 is unchanged.**

Two observations were considered for the plan and kept out of it, because they are item-specific
and already recorded where they act:

- nginx 1.31 is a mainline branch with frequent security releases, so 365 days is only the upper
  bound. This is recorded in SOUP-024. The plan already says "at most 365 days apart", plus every
  dependency change and every release.
- For MinIO, monitoring cannot lead to a fix. This is recorded in SOUP-022, PRB-042 and RISK-012.

### Cross-references and CR-001 change analysis

- Each affected SOUP record names its escalation records in its review section and change log:
  - SOUP-022: RISK-012, PRB-042, PRB-043;
  - SOUP-023: RISK-012, PRB-042;
  - SOUP-021: PRB-045;
  - SOUP-015: PRB-046, PRB-048;
  - SOUP-033: PRB-044;
  - SOUP-003, SOUP-011, SOUP-019: PRB-047.
- CR-001's change analysis has a dated update (2026-10-22). RISK-012 predates the change, so
  `risk_impact` stays `affects_controls`. The class stays B, because severity 4 is the harm class
  of RISK-002/003. **The class confirmation is pending the human.**

### Known gaps

- The RHEL 9.6 UBI micro packages (22 RPMs) in the MinIO and `mc` images were not checked one by
  one against Red Hat errata: no RPM tool or working scanner was available. SOUP-022 and SOUP-023
  state this explicitly. Those images will never be rebuilt, which PRB-042 covers.
- `docker scout cves` (CLI 0.20.0) crashed on the first image, so no image scanner was used for
  any image. The base-OS review was done through the package databases and OSV, as described above.

## QA review (2026-10-22)

**Verdict: CHANGES REQUESTED** (`in_review → draft`). The review itself is thorough and, where QA
checked it against live sources, accurate. There are 0 traceability errors. One HIGH finding
blocks approval: the reviewed SOUP records contradict or leave out the escalation records created
from them. Checkboxes stay unticked until re-review.

### Findings

- **[HIGH] SOUP review sections contradict or omit the escalation records.**
  - **Cause:** the slices wrote their records before the consolidation created RISK-012 and
    PRB-042..047, and nobody updated the records afterwards. No SOUP record names any of them
    (grep: 0 hits each).
  - **Records affected:**
    - `docs/soup/SOUP-022-minio.md:152-153` says "escalated … as candidate RISK and PRB inputs" and
      "No RISK or PRB record is created in this review". `:170` (change log) says "escalated as
      candidates". The actual records are RISK-012, PRB-042 (major) and PRB-043 (critical,
      release-blocking).
    - `SOUP-023-minio-client.md:80-81` and `:98-99` say "candidate … No RISK or PRB record is
      created". The actual records are RISK-012 and PRB-042.
    - `SOUP-021-redis-server.md:87` and `:105` say "candidate problem report". The actual record is
      PRB-045.
    - `SOUP-015-pydicom.md:79-80` says "Escalation proposed: a PRB … proposed `minor`". The actual
      record is PRB-046.
    - `SOUP-033-openapi-fetch.md:50` says "raised for a separate PRB". The actual record is PRB-044.
    - `SOUP-003-starlette.md:73`, `SOUP-011-cryptography.md:74` and `SOUP-019-boto3.md:82` say
      "no RISK or PRB". PRB-047 was raised for exactly these advisories.
  - **Why HIGH:** these sections are the §7.1.3 evidence, and the human approves each record on
    its own (CR-001 Risks table). PRB links stay `[]` by convention and the SOUP records have
    `links: []`. The only path from the SOUP list to an escalation is therefore RISK-012's
    `relates_to`, and SOUP-022 currently says the opposite of the outcome for a critical finding.
  - **Fix:** in each record, replace the candidate wording with the record IDs and the decision.
    Example for SOUP-022: "Escalated under CR-001 AC-12 (2026-10-22): RISK-012 (new, 4 × 2 alarp),
    PRB-042 (major), PRB-043 (critical; no release before CR-002)." Do the same in the change-log
    entries. For SOUP-003, 011 and 019, change "no RISK or PRB" to "no RISK; recorded for upgrade in
    PRB-047 (minor)".
- **[MEDIUM] PRB-046 and SOUP-015 misstate the mechanism. The DICOM viewer module is not
  installed anywhere, which is a new, separate defect.**
  - **Evidence (QA):**
    - In the production image `medhub-backend:ci`, `importlib.metadata.entry_points(group="medhub.modules")`
      returns `[]` and `find_spec("dicom_viewer")` is `False`. The dev venv (`uv run`) also returns
      `[]`.
    - `backend/pyproject.toml` neither lists nor sources `modules/dicom_viewer`, and
      `backend/Dockerfile` only copies the folder.
    - So `discover_modules()` (`backend/app/modules/discovery.py:46`) finds nothing, and the
      `/studies/{attachment_id}` router (`dicom_viewer/router.py:22`) is never mounted.
  - **Consequences:**
    - A `?frame=` request gets a 404, not the server error that PRB-046 and SOUP-015:79 describe.
      The NumPy gap becomes reachable only once the module is installed.
    - SR-017's module path is absent in every environment built from the manifests. ADR-0005
      requires a module to be "build/deploy-time installed (package present in the image)".
    - The module is never in the registry, so `dicomModuleEnabled`
      (`frontend/src/core/clinical/AttachmentItem.tsx:24`) is never true and the DICOM "view" link
      never appears. The core download link still works.
    - The unit tests put the module on `sys.path` themselves (`modules/dicom_viewer/tests/conftest.py`),
      so the suite does not show this.
  - **Fix:**
    - Raise a new PRB (next free ID, PRB-048) for "DICOM viewer module not installed in any
      environment". Its criticality is for the human; by the PRB-002 precedent, a core SR function
      unavailable is `major`.
    - Correct PRB-046 "Observed" and "Impact" and SOUP-015:76-82: the frame path is unreachable
      today (PRB-048), and once the module is installed it fails without NumPy.
    - Add PRB-048 to CR-001's escalation table, noting that QA found it during the TASK-154 review.
- **[MEDIUM] CR-001's change-analysis conclusion is now wrong and must change.**
  `CR-001…md:148-151` says "the worst harm reachable … severity 3 at most … No new RISK record is
  needed". The review created RISK-012 at severity 4.
  → Keep the dated Risk-stage text and add a dated update. For example: "Update 2026-10-22
  (TASK-154): the anomaly review surfaced RISK-012 (4 × 2, alarp), a hazard that predates this
  change (the MinIO release and its configuration were in use before CR-001; pinning only recorded
  them). `risk_impact` stays `affects_controls`. The software safety class stays B: severity 4 is
  the harm class of RISK-002 and RISK-003, already assessed under class B. Confirmed by the human
  on <date>." The class confirmation is required by the `risk-management` class-change rule, and
  only the human can give it. Also add RISK-012 to the TASK-154 row of the table (`:162`).
- **[LOW] RISK-012 uses a new tag spelling.** `hazard:integrity` (RISK-012 frontmatter) does not
  match the register's `hazard:data-integrity` (RISK-002). The category itself is the right choice:
  severity 4 is driven by substitution, which is an integrity harm, and `hazard:security` correctly
  names the mechanism. → Rename the tag to `hazard:data-integrity`. Optionally add `hazard:soup`,
  as RISK-010 does. RISK-012's "Software items involved" also lists "the DICOM viewer item", which
  is not deployed (see the MEDIUM finding above); add a reference to PRB-048 there.

### Judgements asked for

- **AC-11:** met apart from the HIGH finding.
  - Script over all 34 non-obsolete records:
    - frontmatter order puts `anomaly_review: "2026-10-22"` (quoted) after `soup_version`, followed
      by `links` and `tags`;
    - no approval fields remain;
    - status is `in_review`;
    - version is bumped from the approved one: 1.0 → 1.1, and 1.1 → 1.2 for the seven records the
      human approved in `e836c58`, which is correct after approval;
    - no `soup_version` changed, and every one equals `uv.lock` / `package-lock.json`;
    - each review section has 4 to 15 URLs and the date, with no "Not yet performed";
    - each change log has an entry.
  - The images were reviewed at their pinned digests.
  - The RHEL UBI RPM gap in SOUP-022/023 is stated explicitly. It is acceptable because those images
    are never rebuilt (PRB-042).
- **AC-12:** every hazard-relevant anomaly is in RISK-012, which links `relates_to` → SOUP-022 and
  SOUP-023. Every MedHub-affecting anomaly has a PRB (PRB-042..047). CR-001 lists them all. Still
  missing: PRB-048 (MEDIUM above) and the record cross-references (HIGH above).
- **RISK-012 against `risk-management`:**
  - The hazard chain is complete in frontmatter and body.
  - Scores are within 1..5. `acceptability: alarp` is derived from `risk_matrix[4][2]`, and the
    projected 4 × 1 = `acceptable` is labelled as an estimate.
  - Controls name an implementer (CR-002) and "none yet" for verification.
  - The residual is "Decided by: pending".
  - The "ALARP justification" heading formally satisfies `risk_not_acceptable`, but its text says
    "Not yet justified". That is honest, and it is acceptable only because PRB-043 is critical
    (release gate) and the human ruled out a release before CR-002. The human should see it as
    such. It has no inbound `mitigates` link (W3) until CR-002.
  - Choosing RISK-012 over revising RISK-007 for obtainability is defensible. PRB-042's safety
    evaluation explains that a fresh host fails at deployment, before any clinical use.
- **PRB-042..047:** all are `open`, with Observed, Impact, Safety evaluation (which states no
  release and no notification), Proposed resolution and Source. Leaving `## Investigation` until
  resolution is the project convention for open PRBs (PRB-034..040). The criticalities are
  justified: PRB-043 critical (a human decision, consistent with the integrity harm) and PRB-042
  major.
- **AC-13 — "PLAN-002 unchanged" is defensible.** `PLAN-002 … "SOUP monitoring (§6.1 f)"` says:
  every dependency change, before every release, at most 365 days, date in `anomaly_review`, owner
  the Software Architect role with the human accountable. That is exactly what was applied. The
  MinIO and nginx observations belong in the item records, where they already are.

### Spot-checks against live sources (QA, 2026-10-22; read-only HTTP; nothing from a dependency executed)

| Record | Claim | Source queried | Result |
|---|---|---|---|
| SOUP-027 | GHSA-qwww-vcr4-c8h2 applies to 7.18.0; MedHub uses declarative routing only | OSV `vulns/GHSA-qwww-vcr4-c8h2` and `query` for `react-router` / `react-router-dom` 7.18.0; grep of `frontend/src` | Range `introduced 7.12.0, fixed 7.18.2` (and 8.0.0–8.3.0). OSV returns only this ID for 7.18.0 and none for `react-router-dom`. No `createBrowserRouter`, `RouterProvider`, `unstable_` or `@react-router` in the code. **Confirmed** |
| SOUP-022 | CVE-2026-41145, -40344, -113466, -34204 | NVD CVE API 2.0 | All exist, with matching descriptions and ranges (≥ RELEASE.2023-05-18 to before RELEASE.2026-04-11; up to RELEASE.2025-10-15; before RELEASE.2026-03-26). **Confirmed** |
| SOUP-022 | D-4 distribution status | GitHub API (`repos/minio/minio`, `minio/mc`, releases, commits `9e49d5e7a6`, `27742d4694`, `7aac2a2c5b`), `dl.min.io`, Docker Hub, quay.io | Both repositories archived (minio pushed 2026-04-24). `RELEASE.2025-10-15T17-29-55Z` has 0 assets; pinned `RELEASE.2025-09-07T16-13-09Z` has 48 and is the newest release with assets (`mc` `RELEASE.2025-08-13T08-35-41Z` likewise). Commits dated 2025-10-15, 2025-12-03 and 2026-02-12 with the stated messages. `dl.min.io` 410; Hub 404 (minio, mc); quay 401; archived binary HEAD 200. **Confirmed** |
| SOUP-011 | One advisory, CVE-2026-69247 (PKCS#7), not reaching MedHub | OSV `query` cryptography 49.0.0; grep of `backend/app` | GHSA-g6cj-pr64-35w5 / PYSEC-2026-3552, range 44.0.0 to 50.0.0, only. The only import is `AESGCM` (`app/db/crypto.py:20`). **Confirmed** |
| SOUP-015 | CVE-2026-32711 fixed in 3.0.2; NumPy not declared | OSV `query` pydicom 3.0.2 and 3.0.1; `uv.lock`; image | 3.0.2: no entry. 3.0.1: GHSA-v856-2rf8-9f28 (fixed 3.0.2). No `numpy` in the lock or the image. **Confirmed**, but the mechanism differs: see MEDIUM (module not installed) |
| SOUP-024 | nginx 1.31.8 "none found" | nginx.org security advisories page (68 entries) | The newest advisories (CVE-2026-15176, -93479, -95101, -97629, -97205) are "Not vulnerable: 1.31.7+". None covers 1.31.8. **Confirmed** |
| SOUP-021 / PRB-045 | Alpine 3.21 end of support on 2026-11-01 | endoflife.date API; `/etc/alpine-release` of the pinned image | 3.21 EOL 2026-11-01; image base 3.21.9. **Confirmed** |
| SOUP-033 / PRB-044 | `openapi-fetch` not imported | grep of `frontend/src`, `tests`, Vite config | Only `package.json:23`. **Confirmed** |

### Verification run

| Command | Result |
|---|---|
| Structural script over `docs/soup/SOUP-*.md` against `git show HEAD:` | 34 records OK (see AC-11); SOUP-018 `obsolete`, skipped |
| `soup_version` against `backend/uv.lock` and `frontend/package-lock.json` (28 package records) | all match |
| `trace.py` scoped on SOUP-001..035 except 018, RISK-012, PRB-042..047, CR-001, TASK-154 (43 records, 338 indexed) | **0 errors.** One warning: `risk_control_unverified`, TASK-154 → RISK-010 (no TR until the release) |
| `trace.py` on SOUP-001..035 | `soup_anomaly_review_stale` only for the obsolete SOUP-018 (a parser artefact). Gone for all 34 others |
| `trace.py` on every record (336 in scope) | 0 errors |
| Production image `medhub-backend:ci`: `find_spec` and `entry_points("medhub.modules")` | `numpy` absent; `dicom_viewer` absent; entry points `[]` |

### For re-review

Fix the HIGH and both MEDIUMs, then hand back to `in_review`. The human should give the class-B
confirmation in CR-001, and decide on PRB-048 and its criticality. The LOW can ride along.

### Changes after QA round 1 (2026-10-22)

- **[HIGH]** Replaced the candidate and "no RISK or PRB" wording with the actual record IDs and
  decisions, in the review sections and change-log entries of SOUP-022 (RISK-012, PRB-042,
  PRB-043 critical, CR-002), SOUP-023 (RISK-012, PRB-042), SOUP-021 (PRB-045), SOUP-015 (PRB-046,
  PRB-048), SOUP-033 (PRB-044), and SOUP-003, SOUP-011 and SOUP-019 ("no RISK; recorded for upgrade
  in PRB-047"). A grep of all 34 records for "candidate", "proposed", "separate PRB", "for a PRB"
  and "no RISK or PRB" leaves only records with no escalation, where that wording is correct.
- **[MEDIUM]** Verified QA's DICOM-module finding statically:
  - `backend/pyproject.toml` and `backend/uv.lock` have no `dicom-viewer` entry and no `[tool.uv]`
    sources or workspace;
  - `backend/Dockerfile:6,13` only copy the folder;
  - the entry point is declared at `modules/dicom_viewer/pyproject.toml:7-8`;
  - the other cited lines also check out: `discovery.py:46`, `main.py:42`, `router.py:22`,
    `AttachmentItem.tsx:24,32`, `tests/conftest.py`, ADR-0005:41.

  Created PRB-048 (major). Corrected PRB-046 (Observed, Impact, Safety evaluation, Proposed
  resolution) and SOUP-015: the path returns 404 today, and fails without NumPy once the module
  is installed. Added PRB-048 to CR-001's escalation table.
- **[MEDIUM]** CR-001: added the dated update to the change analysis (see above) and RISK-012 to
  the TASK-154 row of the §7.4 table.
- **[LOW]** RISK-012 tags: `hazard:integrity` → `hazard:data-integrity`, plus `hazard:soup`.
  PRB-043's tag was aligned the same way. RISK-012's "Software items involved" now says the DICOM
  viewer is not deployed and points to PRB-048.
- Back to `in_review`. No version bump: these records are not yet committed, so the existing 1.4
  (TASK-154, CR-001) and 1.0 (RISK-012, PRBs) entries were extended in place.

### QA re-review, round 2 (2026-10-22)

**Verdict: APPROVED** (`in_review → approved`). All four round-1 findings are resolved, and every
check is clean. The 34 SOUP records, RISK-012, PRB-042..048 and CR-001 stay `in_review` or `open`
for the human.

**Round-1 findings:**
- **[HIGH] resolved.** Every SOUP record that produced an escalation now names it:
  - SOUP-022: RISK-012, PRB-042, PRB-043 (`:153-160`, change log `:178-179`);
  - SOUP-023: RISK-012, PRB-042 (`:82-83`, `:101`);
  - SOUP-021: PRB-045 (`:87`, `:106`);
  - SOUP-015: PRB-046 and PRB-048;
  - SOUP-033: PRB-044;
  - SOUP-003, SOUP-011, SOUP-019: PRB-047;
  - SOUP-005: PRB-041.

  A grep of all 34 records for "candidate", "proposed", "separate PRB", "for a PRB", "No RISK or PRB
  record" and "handoff" finds only "no RISK or PRB", and only in the ten records with no escalation
  (SOUP-002, 004, 007, 008, 009, 010, 012, 014, 016, 017), where it is correct.
- **[MEDIUM] PRB-046 / SOUP-015 / PRB-048 resolved.**
  - PRB-048 (major, `open`) has Observed, Impact, Safety evaluation, Proposed resolution and Source.
    The Safety evaluation states no release and no notification and justifies the criticality by
    the PRB-002 precedent.
  - Every `file:line` reference checks out against the tree: `modules/dicom_viewer/pyproject.toml:7-8`
    (entry point), no `[tool.uv]` in `backend/pyproject.toml`, no `dicom` entry in `uv.lock`,
    `Dockerfile:6,13` (COPY only), `discovery.py:40,46`, `main.py:42`, `router.py:22`,
    `AttachmentItem.tsx:24,32`, `tests/conftest.py:1-16` (`sys.path.insert`) and ADR-0005:41.
  - PRB-046 and SOUP-015 now describe the 404 today and the failure without NumPy once the module
    is installed.
- **[MEDIUM] CR-001 resolved.** The dated "Update 2026-10-22 (TASK-154)" (`CR-001…md:179-196`)
  states that RISK-012 predates the change, that `risk_impact` stays `affects_controls`, and that
  class B stays, with the **human's class confirmation still pending**. Recording that confirmation
  is the human's step at approval. The TASK-154 row (`:162`) names RISK-012, and PRB-048 is in the
  escalation table (`:442`).
- **[LOW] resolved.** RISK-012 is tagged `hazard:security`, `hazard:data-integrity`, `hazard:soup`.
  PRB-043 is aligned. RISK-012 `:83-86` notes that the viewer is not deployed (PRB-048).

**New finding (non-blocking):**
- **[LOW] The frontend's "Open in viewer" link does not use the module.**
  `frontend/src/core/clinical/AttachmentItem.tsx:32-34` builds it from the same
  `apiClient.getAttachmentUrl(...)` as "Download" (`frontend/src/api/client.ts:166-167`, the core
  `/attachments/{id}`). No frontend code calls the module's `/studies/` endpoint.
  - PRB-046 "Impact" ("That is the path the frontend's 'view' link uses") is therefore wrong.
  - PRB-048's Impact ("the in-app viewer cannot be reached") and its Proposed resolution are
    incomplete: installing the module would only reveal a second link to the raw download.
  - → In PRB-046, replace the sentence with: "the frontend's 'Open in viewer' link uses the core
    attachment URL, not this endpoint". In PRB-048, add one Observed bullet and one resolution
    bullet: wire the link to the module endpoint, or record that the viewer has no frontend.
  - Both are open PRBs, so this can be applied before the commit or by the CR that resolves PRB-048.

**Verification (round 2):**

| Command | Result |
|---|---|
| Structural script over `docs/soup/SOUP-*.md` | 34 OK; SOUP-018 obsolete |
| Escalation-wording grep and ID grep over all 34 SOUP records | see the HIGH above |
| PRB-048 references (`sed -n` on each cited line) | all accurate |
| `trace.py` scoped: SOUP-001..035 except 018, RISK-012, PRB-042..048, CR-001, TASK-154 (44 records, 339 indexed) | **0 errors.** One warning: `risk_control_unverified`, TASK-154 → RISK-010 (no TR until the release) |
| `trace.py` project-wide (337 records) | **0 errors**, 198 warnings. `soup_anomaly_review_stale` only for the obsolete SOUP-018, a parser artefact |
| `trace.py` on TASK-154 after this approval | 0 errors. W5: TASK-154 `approved` → RISK-012 `in_review` (clears when the human approves RISK-012), plus the `risk_control_unverified` warning above |

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-010 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.2 (2026-10-21) — Tagged `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.3 (2026-10-22) — Planned under CR-001 (issue sancharly/medhub#26). Branch changed to
  `bug/soup-pinning` (D-5). Now depends on TASK-155, TASK-157 and TASK-158 (`relates_to` links),
  replacing the PRB-001 caveat. SOUP-018 is excluded as obsolete. Added the MinIO
  distribution-status check (D-4) with the Risk-stage observation, the CR-001 AC-11..13 mapping
  and the escalation list in CR-001. Content change.
- 1.4 (2026-10-22) — Performed (three slices, consolidated): "Implementation notes and evidence"
  added (results per record, escalations RISK-012 and PRB-042..047, D-4 confirmed, AC-13: PLAN-002
  unchanged, known gaps). `relates_to` link to RISK-012. Handed to QA (`in_review`); the
  checkboxes are left for QA.
  After QA round 1 (same version): SOUP cross-references fixed, PRB-048 added, PRB-046/SOUP-015
  corrected, CR-001 change-analysis update, RISK-012 tags; back to `in_review`.
