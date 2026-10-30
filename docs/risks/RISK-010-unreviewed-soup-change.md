---
id: RISK-010
type: risk
title: Unreviewed SOUP change weakens a verified risk control
status: in_review
version: "1.5"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-30"
hazard: A third-party component changing behaviour in a way that disables or weakens a control that a risk record depends on.
cause: A pinned version is changed without review (a lock-file or image-digest update merged without the SOUP record and its anomaly review being updated), or a pinned version keeps an anomaly that no upgrade can fix because its component is no longer maintained (MinIO until CR-002, PRB-042), or a rolling-release component falls behind the release that fixes an advisory (SeaweedFS, SOUP-036) → TLS/HSTS headers, server-side encryption, password hashing or query parameterization behave differently, or a known defect in them stays deployed → a control that a RISK record claims is verified no longer holds, with no test failing.
harm: "Indirect: re-enables the harms of RISK-001, RISK-005, RISK-007, RISK-008 or RISK-011."
severity_initial: 3
probability_initial: 2
severity_residual: 3
probability_residual: 1
acceptability: acceptable
links:
  - target: SOUP-001
    relation: relates_to
  - target: SOUP-002
    relation: relates_to
  - target: SOUP-003
    relation: relates_to
  - target: SOUP-004
    relation: relates_to
  - target: SOUP-005
    relation: relates_to
  - target: SOUP-006
    relation: relates_to
  - target: SOUP-007
    relation: relates_to
  - target: SOUP-008
    relation: relates_to
  - target: SOUP-009
    relation: relates_to
  - target: SOUP-010
    relation: relates_to
  - target: SOUP-011
    relation: relates_to
  - target: SOUP-012
    relation: relates_to
  - target: SOUP-013
    relation: relates_to
  - target: SOUP-014
    relation: relates_to
  - target: SOUP-015
    relation: relates_to
  - target: SOUP-016
    relation: relates_to
  - target: SOUP-017
    relation: relates_to
  - target: SOUP-019
    relation: relates_to
  - target: SOUP-020
    relation: relates_to
  - target: SOUP-021
    relation: relates_to
  - target: SOUP-024
    relation: relates_to
  - target: SOUP-025
    relation: relates_to
  - target: SOUP-026
    relation: relates_to
  - target: SOUP-027
    relation: relates_to
  - target: SOUP-028
    relation: relates_to
  - target: SOUP-029
    relation: relates_to
  - target: SOUP-030
    relation: relates_to
  - target: SOUP-031
    relation: relates_to
  - target: SOUP-032
    relation: relates_to
  - target: SOUP-034
    relation: relates_to
  - target: SOUP-035
    relation: relates_to
  - target: SOUP-036
    relation: relates_to
  - target: RISK-012
    relation: relates_to
tags:
  - hazard:soup
  - class:B
---

# RISK-010 — Unreviewed SOUP change weakens a verified risk control

## Hazard

A third-party component changing behaviour in a way that disables or weakens a control that a risk record depends on.

## Sequence of events

Since CR-001 every shipped component is pinned: packages through `backend/uv.lock` and
`frontend/package-lock.json`, container images by release tag and `@sha256:` digest. A new version
therefore needs a commit. Two paths remain:

1. **Unreviewed change of a pinned version.** A lock-file or image-digest update is merged without
   the SOUP record and its anomaly review being updated → TLS/HSTS headers, server-side encryption,
   password hashing or query parameterization behave differently → a control that a RISK record
   claims is verified no longer holds, with no test failing.
2. **Anomaly with no fix path, or a fix not adopted.** A pinned version keeps a known or future
   anomaly that no upgrade can fix, because the component is no longer maintained, or that a
   rolling-release component fixes only in a release MedHub has not adopted. The anomaly review
   finds the defect, but no deployed version removes it → the control the item bears (for the
   object store: server-side encryption, SR-022, and the integrity of the stored attachments)
   stays weakened.
   - Until CR-002 this was MinIO server and client (SOUP-022, SOUP-023): the community edition is
     unmaintained and archived (PRB-042), and four hazard-relevant CVEs were deployed (PRB-043).
     CR-002 replaced both (TASK-175, TASK-176); the records are `obsolete`.
   - Since CR-002 the object store is SeaweedFS 4.51 (SOUP-036), maintained but with rolling
     releases only: fixes ship in the latest release, so a pinned digest falls behind as soon as a
     newer release fixes an advisory (25 advisories in 2026, 9 critical).

Before CR-001 the first step was "a floating image tag (`nginx:alpine`, `minio/minio:latest`) or an
unreviewed library upgrade pulls a new version". PRB-001 removed the floating tags.

## Hazardous situation

A risk control believed to be in place is not, and nobody knows.

## Harm

Indirect: re-enables the harms of RISK-001, RISK-005, RISK-007, RISK-008 or RISK-011.

## Software items involved

All items; specifically nginx, the SeaweedFS object store, cryptography, argon2-cffi, SQLAlchemy,
Redis, pydicom (SOUP-001..036). SOUP-022 and SOUP-023 (MinIO) are obsolete since CR-002 (TASK-176,
TASK-175), so this record no longer links them. SOUP-018 is obsolete since CR-001 (TASK-158). SOUP-033 (openapi-fetch, never
imported) leaves the list with CR-003 (TASK-165, PRB-044), so this record no longer links it. The pin check is part of SI-DEVINFRA
`U-INF-CIPipeline` (ADD-024). The object-store path is analyzed in full, at its own severity, in
[RISK-012](RISK-012-object-store-compromised-or-unpatchable.md).

## Initial risk

Severity 3 — Moderate (a control silently stops working) — × probability 2 (Remote) → **alarp** per `risk_matrix` in
`docs/medtrace.yml` ([PLAN-005](../plans/PLAN-005-risk-management-plan.md)). Following the plan's software
convention, P1 — the probability of the software fault itself — is taken as 1 (the fault is assumed to
occur); the score is severity × P2, the probability that the hazardous situation leads to the harm.
Scored before CR-001 (floating tags, no anomaly review); unchanged.

## Risk control measures

| Measure | Type | Implemented by | Verified by |
|---|---|---|---|
| SOUP list with exact versions, required functions and required HW/SW | Design | SR-028, SOUP-001..036 (SOUP-018 obsolete; SOUP-033 obsolete with CR-003 TASK-165; SOUP-022 and SOUP-023 obsolete with CR-002 TASK-176 and TASK-175; SOUP-036 new with CR-002 TASK-172) | TR-001, TS-013 |
| Every image and dependency pinned to an immutable version | Design | SR-028 AC-5; CR-001: TASK-155 (every image by release tag and digest, PRB-001), the committed lock files `backend/uv.lock` and `frontend/package-lock.json`, TASK-157 / TASK-158 (manifest corrections, PRB-002 / PRB-033). CR-003 re-pins at the upgraded versions: TASK-161 (Redis), TASK-162 (Node build image), TASK-163 / TASK-164 (lock). CR-002 pins the object store `chrislusf/seaweedfs:4.51` by index digest (TASK-176) | The CR-001 AC-3 pin check (TASK-156, CI job `image-pins`); TS-013 TC-013.5, TC-013.6, TC-013.7, TC-013.8; for SOUP-036, TS-014 TC-014.1 (image by digest) and `infra/check_image_pins.py` exit 0 (TASK-176 QA) |
| CI rejects any image reference without a digest | Protective | SR-028 AC-5; TASK-156 (`infra/check_image_pins.py`, CI job `image-pins`, ADD-024) | TS-013 TC-013.5, TC-013.6 |
| Anomaly and advisory review per version, at least yearly and before release | Protective | SR-028 AC-6; TASK-154 (first review), PLAN-002 "SOUP monitoring" (cadence and owner). CR-003 re-reviews SOUP-003, 011, 019 and 021 at their new versions (TASK-161, TASK-163, TASK-164). CR-002 reviews SOUP-036 (TASK-172) | The dated, sourced reviews (`anomaly_review`; 2026-10-22 from TASK-154, re-dated by CR-003 for SOUP-003, 011, 019, 021; 2026-10-30 for SOUP-036 from TASK-172, spot-checked by QA) in SOUP-001..017, SOUP-019..021, SOUP-024..032, SOUP-034..036; TS-013 TC-013.9 |
| Monthly advisory check for items with rolling releases; a fix for a hazard-relevant advisory adopted by a reviewed digest change no later than the next check | Protective | SR-028 AC-6; TASK-172 (PLAN-002 1.2 "Items with rolling releases", SOUP-036 "Monitoring"; first check due 2026-11-30) | SOUP-036 review of 2026-10-30 as the baseline; TS-013 TC-013.9. PLAN-002 1.2 is `in_review`: the rule binds once the human approves it |
| Tests asserting the security headers, encryption and hashing behaviour | Protective | SR-001, SR-022, SR-025 | TR-001, TS-001, TS-008, TS-011 |

## Residual risk

Severity 3 (unchanged — controls reduce probability, not severity) × probability 1 (Improbable) →
**acceptable**, derived from `risk_matrix` (row 3, column 1). The record carries one residual, and
the worst path governs. Re-evaluated on 2026-10-30 by CR-002 TASK-181 (AC-14) from the CR-002
evidence; version 1.4 was 3 × 2 → `alarp`, set by the MinIO path.

- **Path 1, every SOUP item (SOUP-001..017, 019..021, 024..032, 034..036): probability 1
  (Improbable).**
  - Every shipped component is fixed by a committed lock file or an image digest. A new version
    needs a commit that changes the lock or the digest. That commit passes PR review, the CI pin
    check and the PLAN-002 rule "review at every dependency change".
  - The anomaly review gives each pinned version a dated, sourced baseline, and its findings for
    these items have a fix path (PRB-044..047 are upgrades or declarations). CR-003 applied that
    fix path to PRB-044, PRB-045 and PRB-047, and CR-002 applied it to the object store (below).
  - What stays unenforced is process: no automated gate ties a lock or digest change to a SOUP
    record update. Review checks it, and so do TS-013 TC-013.9 and `traceability-check` at release.
  - PRB-035 (end-of-life Node 20 build stage) is resolved by CR-003 TASK-162. PRB-034 (unpinned CI
    tooling and `uv`) is still open and does not reopen the path: `uv sync --frozen` and `npm ci`
    install only locked versions, and no build tool ships.
  - On this path alone: 3 × 1 → acceptable.
- **Path 2, anomaly with no fix path, or a fix not adopted: probability 1 (Improbable), lowered
  from 2.** AC-14 allows 3 × 1 only if a maintained, patchable object store is deployed. Each
  condition, with its evidence:
  - *The unmaintained item is gone.* No `minio` service or `minio/*` image remains in
    `infra/docker-compose.yml` (TS-014 TC-014.1, TASK-176 QA); SOUP-022 and SOUP-023 are
    `obsolete`. No other deployed item is known to be without a fix path.
  - *The replacement is deployed at a pinned digest.* `chrislusf/seaweedfs:4.51@sha256:f7a49e3f…134b8`
    (SOUP-036; TC-014.1; `infra/check_image_pins.py` exit 0; built and started on an empty
    `docker:dind` daemon, TS-013 TC-013.10).
  - *Its review found a fix path.* TASK-172's review (2026-10-30, QA spot-checked): no advisory
    affects 4.51, the repository is active and not archived, fixes ship in the latest release, and
    4.51 is the newest. A found anomaly can therefore be followed by a reviewed digest change.
  - *The monitoring is in place for rolling releases.* PLAN-002 1.2 "Items with rolling releases"
    and SOUP-036 "Monitoring": checked monthly, a fix for a hazard-relevant advisory adopted by a
    reviewed digest change no later than the next check; first check due 2026-11-30.
    **PLAN-002 1.2 is `in_review`.** Probability 1 on this path holds only with that rule
    approved; without it, the yearly cadence is too slow for 25 advisories a year and path 2
    returns to 2 (3 × 2 → `alarp`).
  - Base-OS package `fuse` from Alpine v3.24 `community` (support ends 2026-11-01, PRB-051, minor,
    not exercised) has the same fix path: an upstream rebuild adopted by a reviewed digest change.
  - Severity stays 3 for this record's harm (a control silently weakened). The severity-4 harm on
    the object-store path is analyzed in RISK-012 (re-scored to 4 × 1 by the same task) and not
    counted twice here. RISK-002 and RISK-003 are not re-scored (human decision, 2026-10-22).

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

Not needed: the residual 3 × 1 is `acceptable` under `risk_matrix`. The ALARP state of 1.3 and 1.4
(path 2, MinIO, accepted for development only) ends when the human approves this version together
with PLAN-002 1.2.

## Risks introduced by controls

- Pinning delays security patches; the monitoring cadence in PLAN-002 is the counterweight.
- **The object-store replacement ships on a rolling release line (CR-002).** SeaweedFS publishes no
  maintained release line and no end-of-life date; fixes ship only in the latest release
  (4.47..4.51 between 2026-09-14 and 2026-10-25), and the 2026 advisory rate is high (25, 9
  critical). A pinned digest therefore falls behind at the next fixing release. The counterweight
  is the monthly check of PLAN-002 1.2 and a digest change by the next check; each such change is
  an upgrade with its own change analysis (soup-management step 5), because existing controls
  (SSE, the loopback binding of internal ports, SOUP-036 F-1/F-2) depend on the server's
  behaviour, and TS-008 TC-008.8 and TS-014 re-verify them on every pull request and started stack.
- For MinIO, pinning recorded the last community release, and that counterweight did not work: no
  patched release would be published (D-4, PRB-042). CR-002 removed it; kept here as history.
- Pinning by digest also holds back upstream rebuilds that keep the same tag. On 2026-10-26
  upstream rebuilt `redis:7.4.11-alpine` under the same tag (new index digest
  `sha256:d9436322…3193`). MedHub kept the pinned `sha256:892022f9…eab1` until CR-003 changed the
  digest (CR-003, observation of 2026-10-29). This is the intended behaviour: the tag alone does
  not identify the image. Base-OS fixes made by such rebuilds reach MedHub only through a reviewed
  digest change, and the same PLAN-002 counterweight applies. No hazard beyond the first bullet.
- The CI pin check can reject a correct change (false positive). That only blocks a merge, and its
  false-negative modes are covered by the TC-013.6 fixtures. No hazard.

## Version history

- 1.2 (2026-10-21) — Approved (self-approved, 2026-10-21).
- 1.3 (2026-10-22) — CR-001 (TASK-159), §7.4.3 re-assessment after TASK-154..158 and TASK-160.
  Content change, so the approval record is cleared and the record returns to review.
  - Control table: implementer and verification evidence filled for "every image and dependency
    pinned" (TASK-155, the lock files, TASK-157/158; the AC-3 pin check; TS-013 TC-013.5..8) and
    for the anomaly review (TASK-154, the dated SOUP reviews, TS-013 TC-013.9). New row for the
    CI pin check (TASK-156, protective).
  - `cause` and Sequence of events: the floating tags are gone (PRB-001). They now name the two
    remaining paths: an unreviewed change of a pinned version, and an anomaly with no fix path
    (MinIO).
  - Residual re-scored from 3 × 1 (acceptable, conditional on preconditions that were unmet) to
    3 × 2. `acceptability` is `alarp`, derived from `risk_matrix`. Path 1 holds at probability 1;
    path 2 (MinIO, SOUP-022/023) stays at 2 because the review cannot lead to a fix (D-4, input
    from RISK-012). ALARP justification added.
  - `relates_to` SOUP-018 removed (obsolete since TASK-158), and `relates_to` RISK-012 added,
    which shares the MinIO path.
- 1.4 (2026-10-29) — CR-003 Risk stage (§7.4, CR-003 AC-15), by the Software Architect role.
  Content change, so the approval record is cleared and the record returns to review.
  - `relates_to` SOUP-033 removed (openapi-fetch, never imported; obsolete with CR-003 TASK-165,
    PRB-044).
  - The path-1 rationale no longer cites PRB-035 as open. It names its resolution (TASK-162,
    Node 24 LTS) and records that CR-003 applies the fix path to PRB-044, PRB-045 and PRB-047.
  - Control table: CR-003's re-pins (TASK-161..164) and re-reviews (SOUP-003, 011, 019, 021) are
    named.
  - Risks introduced by controls: a new bullet on upstream rebuilds under a pinned tag
    (`redis:7.4.11-alpine`, 2026-10-26).
  - Residual confirmed at 3 × 2 → `alarp`, derived from `risk_matrix`, not re-scored. Path 2
    (MinIO) still governs and is CR-002's. Path 1 stays at probability 1. Acceptance is the
    human's, through approval of this version. TASK-168 confirms the PRB-035 statement once
    TASK-162 has landed.
- 1.5 (2026-10-30) — CR-002 TASK-181, §7.4.3 re-evaluation of path 2 (CR-002 AC-14), by the
  Software Architect role. Content change, so the approval record is cleared and the record
  returns to review.
  - `cause`, Sequence of events path 2 and Software items: MinIO is history (obsolete since
    TASK-175 and TASK-176); path 2 now also covers a rolling-release item that falls behind its
    fixing release (SeaweedFS, SOUP-036).
  - Links: `relates_to` SOUP-022 and SOUP-023 (obsolete) replaced by SOUP-036 (CR-002 AC-12).
  - Control table: SOUP-036 named in the list, pin and review rows; new row for the monthly
    advisory check of PLAN-002 1.2 (TASK-172).
  - Residual re-scored from 3 × 2 to 3 × 1 → `acceptable`, derived from `risk_matrix`: path 2 has
    a maintained, patchable store at a pinned digest, a review that found a fix path, and the
    monthly check. Conditional on the human's approval of PLAN-002 1.2; otherwise path 2 stays 2.
  - ALARP justification replaced by a statement that none is needed. Risks introduced by
    controls: the rolling release line of the replacement added; the MinIO bullet kept as history.
  - Acceptance is the human's, through approval of this version.
