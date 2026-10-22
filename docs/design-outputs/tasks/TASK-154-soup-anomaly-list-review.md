---
id: "TASK-154"
type: task
title: "First SOUP anomaly-list review"
status: draft
version: "1.3"
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

- [ ] CR-001 **AC-11**: every non-obsolete `soup` record has `anomaly_review` and an "Anomaly list
      review" section citing each source checked for its exact `soup_version`, with each applicable
      anomaly judged for hazard relevance or "none found". No section reads "Not yet performed".
      The image items are reviewed at their pinned versions.
- [ ] CR-001 **AC-12**: each hazard-relevant anomaly is in a RISK record linking `relates_to` → the
      SOUP record; each MedHub-affecting anomaly has a PRB; CR-001 lists the escalations or "none".
      The MinIO distribution status is confirmed or refuted, with its source.
- [ ] CR-001 **AC-13**: PLAN-002's SOUP monitoring section matches the cadence and owner applied.

## Definition of Done

- [ ] Every reviewed `soup` record updated and left `in_review` for human approval
- [ ] `traceability-check` shows no `soup_anomaly_review_stale` warning and no error for the
      touched records

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
