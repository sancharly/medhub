---
id: SR-028
type: software-requirement
title: Traceable, version-controlled development records
status: approved
version: "1.6"
author: Carlos Santiago Liceras
created: "2026-07-07"
updated: "2026-10-30"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-30"
approved_digest: 48fcf3109fc7b116257f58ca9f2fab0cdfca1ee76fecb7550bc479f157209377
approval_note: self-approved
links:
  - target: RR-006
    relation: satisfies
  - target: RR-007
    relation: satisfies
  - target: RR-008
    relation: satisfies
  - target: RR-010
    relation: satisfies
  - target: RISK-007
    relation: mitigates
  - target: RISK-010
    relation: mitigates
  - target: NFR-005
    relation: derives_from
  - target: NFR-006
    relation: derives_from
tags:
  - control:design
  - control:protective
---

## Summary

The development shall maintain uniquely identified, version-controlled requirements with bidirectional traceability and risk analysis, shall trace each software requirement to at least one test, and shall identify every third-party (SOUP) component of the build by an exact, immutable version with a dated anomaly-list review.

## Description

This requirement implements the process/documentation obligations of the medical-device regulation and IEC 62304. Each requirement (user need, NFR, software requirement) is uniquely identified, kept under version control with status and version history, and carries risk analysis. Software requirements reference their origin user need/NFR, and each is traced to at least one system test, forming an auditable design and verification record.

The same obligation covers the software of unknown provenance the build is assembled from (RR-008, RR-010): every third-party package, language runtime and container image resolves to exactly one version that cannot change without a commit, so the released build is reproducible from version-controlled sources and each SOUP record states what is actually deployed.

## Acceptance Criteria

1. Every requirement has a unique identifier, a status, and a version history, and is stored under version control.
2. Every software requirement records its origin user need or NFR (bidirectional traceability is maintained).
3. Every requirement includes a documented risk analysis (rationale, potential risks, control measures).
4. Each software requirement is traced to at least one system test before release.
5. Every third-party component that the deployed software ships or requires at runtime is declared in a version-controlled manifest and resolves to exactly one version: packages through the committed lock files, container images through a reference that carries both a release tag and an immutable content digest (`@sha256:`). The CI pipeline fails on a change that leaves a container image reference in the deployment or image-build files (Compose files, Dockerfiles) without a digest.
6. Every SOUP component in use has a `soup` record whose `soup_version` equals the version the build resolves, and a dated review of its published anomaly list that cites the source reviewed; at release the review is no older than `soup_anomaly_max_age_days` in `docs/medtrace.yml`.
7. Every container image the deployment references can be obtained, by its pinned tag and digest or by a documented build from version-controlled sources with verified checksums, on a host that holds no cached images: building and starting the stack on such a host succeeds.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-005 "Medical device regulatory compliance (MDR and FDA)" and NFR-006 "IEC 62304 development process compliance".

## Risk Analysis

### Rationale

Traceable, controlled records are mandatory for MDR/FDA technical documentation and IEC 62304 lifecycle conformity.

### Potential Risks

- Compliance risk: missing traceability or records blocks regulatory acceptance.
- Quality risk: untraced requirements may go unverified.
- Safety risk: a floating or undeclared third-party component changes or disappears between builds, silently weakening a verified risk control or disabling a function (RISK-010).

### Control Measures

- Maintain requirements in the repository using the template (IDs, status, version history, origin, risk analysis); establish requirement-to-test traceability during the testing phase per the development plan.
- Pin every package through the lock files and every container image by tag and digest, enforced by a CI check; review each SOUP item's anomaly list per PLAN-002 (AC-5, AC-6; verified through TS-013 once it covers them).

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-007, RISK-010 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.2 (2026-09-17) — Added `satisfies` link to RR-006, RR-007, RR-008, RR-010 (regulatory requirements
  extracted from the NFRs with clause citations). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
- 1.3 (2026-10-21) — Tagged `control:design`, `control:protective` (type of the risk control it implements,
  medical-records 0.3.2). Traceability only: the content is unchanged, so the existing approval stands.
- 1.4 (2026-10-21) — Restored from `obsolete` by the owner's decision: the restatement as RR-011
  was withdrawn because SR-028 is the only SR realizing RR-006/007/008 and is implemented by
  TASK-001/005/111/147/154. Its architecture coverage is now ADD-024. Content unchanged.
- 1.5 (2026-10-22) — Content change, so the approval record is cleared and the record returns to
  review (CR-001). Added AC-5 (every third-party component resolves to one exact version; container
  images pinned by tag and `@sha256:` digest, enforced in CI) and AC-6 (SOUP record version matches
  the build and carries a dated, sourced anomaly-list review), with the matching summary,
  description, risk and control-measure text. Reason: RR-008 and RR-010 ask for exact versions
  matching the build, a dated anomaly review and a reproducible build, and SR-028 is the only SR
  that realizes them, but none of its criteria stated those obligations, so the pinning check and
  the anomaly review of CR-001 (PRB-001, PRB-002, PRB-033, TASK-154) had no testable criterion to
  verify against.
- 1.6 (2026-10-30) — Content change, so the approval record is cleared and the record returns to review (CR-002). Added AC-7 (every pinned component can be obtained on a host with no cached images). Reason: the pinned MinIO images can no longer be pulled from any registry, so the pinned build is not reproducible on a fresh or amd64 host (PRB-042, §5.8.5).
