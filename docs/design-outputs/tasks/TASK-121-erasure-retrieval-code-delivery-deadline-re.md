---
id: "TASK-121"
type: task
title: "Erasure retrieval-code delivery + deadline + re-keying (remediation)"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-024"
    relation: implements
  - target: "SR-034"
    relation: implements
  - target: "TASK-035"
    relation: relates_to
  - target: "TASK-031"
    relation: relates_to
tags: ["phase:2-auth-identity", "remediation-of:TASK-035", "original-id:TASK-035a"]
---

- **Phase:** 2 — Auth & identity
- **Implements / restores:** SR-024, SR-034.5–7, ADR-0013; remediates TASK-035
- **Depends on:** TASK-035, TASK-031 (email worker)
- **Branch:** `feature/erasure-delivery`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-035 verdict **FAIL**

*Originally filed as TASK-035a.*

## Objective

Account erasure generates and hashes a retrieval code but **never emails it** (the delivery step is a
`pass` no-op in `app/identity/erasure.py`), so the user can never recover their anonymized data — the
DELETE endpoint's "code will be emailed" response is false. Additionally `retrieve_anonymized` ignores
`retention_deadline`, and clinical-data re-keying into the anonymized dataset is unimplemented.

## Implementation detail

- Enqueue a dedicated Celery task to email the ≥128-bit retrieval code to the user during `erase()`
  (the plaintext code must never be persisted/audited — only its hash is stored).
- In `retrieve_anonymized`, reject datasets past `retention_deadline` with **404** (not return them).
- Implement clinical-data re-keying: move the anonymized clinical payload into `AnonymizedDataset`
  (sever back-references / quasi-identifiers) per ADR-0013, so TASK-036's 5-year erase is meaningful.
- Fix the retrieval audit action to the catalog name (`ANONYMIZED_RETRIEVAL`).

## Acceptance criteria

- [x] The retrieval code is emailed exactly once on erasure; only its salted hash is stored; code never logged/audited.
- [x] Anonymized data is retrievable by the code within the window; an expired dataset returns 404.
- [ ] Clinical data is anonymized/re-keyed into the dataset (not silently dropped). — deferred: no ClinicalEntry repo available; payload carries `original_user_type` stub. **Tracked remediation: [TASK-116](../phase-9-integration-test-compliance/TASK-116-clinical-data-rekeying.md)** (phase 9) — the original deferral reason is stale (`ClinicalRepository`/`AttachmentRepository` now exist); once TASK-116's AC/DoD are met, this checkbox is checked and this task's status is re-confirmed as fully Completed.
- [x] Retrieval is audited as `ANONYMIZED_RETRIEVAL`.

## Definition of Done

- [x] Lint + type-check pass
- [x] Tests prove email enqueued (not no-op), deadline→404, no-plaintext-code invariant
- [x] Traceability row updated (SR-024/SR-034 → TASK-035a → tests)
- [x] Security review completed
