---
id: "TASK-154"
type: task
title: "First SOUP anomaly-list review"
status: draft
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
links:
  - target: "RISK-010"
    relation: mitigates
  - target: "SR-028"
    relation: implements
tags: ["soup", "regulatory", "phase:9-integration-system-testing-compliance"]
---

# TASK-154 — First SOUP anomaly-list review

- **Software item / unit:** all (SOUP crosses every item)
- **Depends on:** the `soup` records SOUP-001..035 in [`../../soup/`](../../soup/)
- **Branch:** `enabler-story/soup-anomaly-review`

## Objective

The `soup` records in [`../../soup/`](../../soup/) identify every SOUP item with its exact locked
version, but no published anomaly list has been reviewed yet (§7.1.2–7.1.3). Until that review
exists and is dated, the SOUP list cannot support a release. This task performs the first round and
establishes the cadence recorded in the list's Monitoring section.

## Implementation detail

- For each `soup` record, read the manufacturer's release notes, issue tracker and security
  advisories **for the exact locked version**, plus the CVE database, and record the source in the body and the
  review date in the record's `anomaly_review` field.
- Prioritize the items behind a risk control: `cryptography` (encryption at rest, SR-022),
  `argon2-cffi` (password hashing), nginx (TLS/HSTS, SR-001), MinIO (server-side encryption),
  `pydicom` (image rendering, SR-017), SQLAlchemy (parameterized queries, SR-031), Redis (session
  integrity, SR-030).
- Any anomaly that could contribute to a hazardous situation goes to `risk-management` as a RISK
  record; any defect that affects MedHub becomes a PRB.
- Review published information only — do not fetch or execute anything from a dependency's
  repository to test it.
- Note that PRB-001 (floating image tags) limits the review for container images: the exact version
  must be pinned first for the review to mean anything.

## Acceptance criteria

- [ ] Every `soup` record carries an anomaly source in its body and an `anomaly_review` date
- [ ] Hazard-relevant anomalies are listed per item, or the row states "none found" with the date
- [ ] New RISK records and PRBs created where the review found something
- [ ] PLAN-002's SOUP monitoring section reflects the actual cadence and owner

## Definition of Done

- [ ] Every reviewed `soup` record updated and left `in_review` for human approval
- [ ] `traceability-check` shows no error for the touched records

## Version history

- 1.1 (2026-09-17) — Added `mitigates` link to RISK-010 (risk register bootstrap, TASK-147). Traceability only: the requirement content is
  unchanged, so the existing approval stands.
