---
id: RISK-010
type: risk
title: Unreviewed SOUP change weakens a verified risk control
status: approved
version: "1.4"
author: Carlos Santiago Liceras
created: "2026-09-17"
updated: "2026-10-29"
hazard: A third-party component changing behaviour in a way that disables or weakens a control that a risk record depends on.
cause: A pinned version is changed without review (a lock-file or image-digest update merged without the SOUP record and its anomaly review being updated), or a pinned version keeps an anomaly that no upgrade can fix (MinIO, SOUP-022/023, PRB-042) → TLS/HSTS headers, server-side encryption, password hashing or query parameterization behave differently, or a known defect in them stays deployed → a control that a RISK record claims is verified no longer holds, with no test failing.
harm: "Indirect: re-enables the harms of RISK-001, RISK-005, RISK-007, RISK-008 or RISK-011."
severity_initial: 3
probability_initial: 2
severity_residual: 3
probability_residual: 2
acceptability: alarp
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-29"
approved_digest: cedf412b415b8c3864bb814469c38fd8ffb30355b28da33046a564e34bb3022d
approval_note: self-approved
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
  - target: SOUP-022
    relation: relates_to
  - target: SOUP-023
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
2. **Anomaly with no fix path.** A pinned version keeps a known or future anomaly that no upgrade
   can fix, because the component is no longer maintained. Today this is MinIO server and client
   (SOUP-022, SOUP-023): the community edition is unmaintained and archived (PRB-042), and four
   hazard-relevant CVEs stay deployed (PRB-043). The anomaly review finds the defect, but no
   version exists that removes it → the server-side encryption control (SR-022) and the integrity
   of the stored attachments stay weakened.

Before CR-001 the first step was "a floating image tag (`nginx:alpine`, `minio/minio:latest`) or an
unreviewed library upgrade pulls a new version". PRB-001 removed the floating tags.

## Hazardous situation

A risk control believed to be in place is not, and nobody knows.

## Harm

Indirect: re-enables the harms of RISK-001, RISK-005, RISK-007, RISK-008 or RISK-011.

## Software items involved

All items; specifically nginx, MinIO, cryptography, argon2-cffi, SQLAlchemy, Redis, pydicom
(SOUP-001..035). SOUP-018 is obsolete since CR-001 (TASK-158). SOUP-033 (openapi-fetch, never
imported) leaves the list with CR-003 (TASK-165, PRB-044), so this record no longer links it. The pin check is part of SI-DEVINFRA
`U-INF-CIPipeline` (ADD-024). The MinIO path is analyzed in full, at its own severity, in
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
| SOUP list with exact versions, required functions and required HW/SW | Design | SR-028, SOUP-001..035 (SOUP-018 obsolete; SOUP-033 obsolete with CR-003 TASK-165) | TR-001, TS-013 |
| Every image and dependency pinned to an immutable version | Design | SR-028 AC-5; CR-001: TASK-155 (every image by release tag and digest, PRB-001), the committed lock files `backend/uv.lock` and `frontend/package-lock.json`, TASK-157 / TASK-158 (manifest corrections, PRB-002 / PRB-033). CR-003 re-pins at the upgraded versions: TASK-161 (Redis), TASK-162 (Node build image), TASK-163 / TASK-164 (lock) | The CR-001 AC-3 pin check (TASK-156, CI job `image-pins`); TS-013 TC-013.5, TC-013.6, TC-013.7, TC-013.8 |
| CI rejects any image reference without a digest | Protective | SR-028 AC-5; TASK-156 (`infra/check_image_pins.py`, CI job `image-pins`, ADD-024) | TS-013 TC-013.5, TC-013.6 |
| Anomaly and advisory review per version, at least yearly and before release | Protective | SR-028 AC-6; TASK-154 (first review), PLAN-002 "SOUP monitoring" (cadence and owner). CR-003 re-reviews SOUP-003, 011, 019 and 021 at their new versions (TASK-161, TASK-163, TASK-164) | The dated, sourced reviews (`anomaly_review`; 2026-10-22 from TASK-154, re-dated by CR-003 for SOUP-003, 011, 019, 021) in SOUP-001..017, SOUP-019..032, SOUP-034 and SOUP-035; TS-013 TC-013.9. For SOUP-022/023 the review detects but cannot lead to a fix (path 2) |
| Tests asserting the security headers, encryption and hashing behaviour | Protective | SR-001, SR-022, SR-025 | TR-001, TS-001, TS-008, TS-011 |

## Residual risk

Severity 3 (unchanged — controls reduce probability, not severity) × probability 2 (Remote) →
**alarp**, derived from `risk_matrix` (row 3, column 2). The record carries one residual, and the
worst path governs. The PRB-001 and TASK-154 preconditions of version 1.2 now hold: PRB-001 is
resolved (TASK-155, TASK-156) and the first anomaly review was run on 2026-10-22 (TASK-154).

- **Path 1, every SOUP item except MinIO (SOUP-001..017, 019..021, 024..035): probability 1
  (Improbable).**
  - Every shipped component is fixed by a committed lock file or an image digest. A new version
    needs a commit that changes the lock or the digest. That commit passes PR review, the CI pin
    check and the PLAN-002 rule "review at every dependency change".
  - The anomaly review gives each pinned version a dated, sourced baseline, and its findings for
    these items have a fix path (PRB-044..047 are upgrades or declarations). CR-003 applies that
    fix path to PRB-044, PRB-045 and PRB-047. Each upgrade is a reviewed commit that changes a lock
    or a digest, followed by a dated review at the new version. That is the PLAN-002
    counterweight working as this record assumes.
  - What stays unenforced is process: no automated gate ties a lock or digest change to a SOUP
    record update. Review checks it, and so do TS-013 TC-013.9 and `traceability-check` at release.
  - PRB-035 (end-of-life Node 20 build stage) is resolved by CR-003 TASK-162. The build stage
    and CI run on Node 24 LTS (end of life 2028-04-30), pinned by tag and digest.
  - PRB-034 (unpinned CI tooling and `uv`) is still open and does not reopen the path. Neither
    did PRB-035 while it was open. `uv sync --frozen` and `npm ci` install only locked
    versions, and no build tool ships.
  - On this path alone: 3 × 1 → acceptable.
- **Path 2, MinIO server and client (SOUP-022, SOUP-023): probability 2 (Remote), the initial
  value.**
  - Pinning holds (digest), and the review was run. But the review control assumes that a found
    anomaly can be followed by a fixed version, and for MinIO none exists or will exist (PRB-042,
    D-4 confirmed by TASK-154).
  - The control therefore detects but does not correct: it does not lower the probability on this
    path. The item bears a control, server-side encryption of attachments (SR-022, RISK-011's
    at-rest control), and CVE-2026-34204 targets exactly that metadata (PRB-043).
  - This is the input stated in RISK-012 and applied here by the human's decision of 2026-10-22.
  - Severity stays 3 for this record's harm (a control silently weakened). The severity-4 harm on
    this path, a substituted or planted attachment, is analyzed in RISK-012 and not counted twice
    here. RISK-002 and RISK-003 are not re-scored (human decision, 2026-10-22).
  - Its controls are CR-002's: PRB-042 (a maintained object store) and PRB-043 (configuration
    hardening, checksum on download).

**Re-evaluate** when CR-002 resolves PRB-042. With a maintained object store, path 2 has a fix path
again, and the expected residual is 3 × 1 → acceptable. That is an estimate for CR-002 to
confirm, not a score.

**Decided by:** pending — the owner's acceptance is the approval of this record.

## ALARP justification

Not justified for a release. The residual is ALARP only because path 2 has no control that can
correct a found anomaly yet. Further reduction is practicable and planned: replace the
unmaintained object store under CR-002 (PRB-042). The human decided on 2026-10-22 that the MinIO
mitigation goes to CR-002 and that no release is made before it. The current state is accepted for
development only. Path 1 needs no further reduction: it is acceptable on its own. Re-evaluate when
CR-002 lands.

## Risks introduced by controls

- Pinning delays security patches; the monitoring cadence in PLAN-002 is the counterweight.
- For MinIO, pinning recorded the last community release, and that counterweight does not work:
  no patched release will be published (D-4, PRB-042). That is path 2 above, and the input to
  RISK-012.
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
