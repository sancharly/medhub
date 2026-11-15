---
id: "PRB-021"
type: problem-report
title: "Authorization lookups have no supporting indexes"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-15"
criticality: major
links: []
tags: ["performance", "hazard:availability"]
---

# PRB-021 — Authorization lookups have no supporting indexes

## Observed

`app/db/alembic/versions/0001_initial.py` creates no index on `appointment.scheduled_at`, `consent_grant.appointment_id`, `clinical_entry.patient_id` or `attachment.patient_id`.

**Corrected 2026-11-13 (CR-006 D-29, TASK-219 QA finding 1).** The original text said all four columns are read on every authorization decision. That is wrong. The consent decision (`ConsentRepository.list_active_for_patient_doctor`) filters on `consent_grant(patient_id, doctor_id, active)` and is served by the existing `ix_consent_grant_patient_doctor_active`. Of the four columns, only `clinical_entry.patient_id` is read by a current query: `ClinicalRepository.list_for_patient(_ordered)`, the listing of a patient's entries after the consent check. No current query filters on `appointment.scheduled_at`, `consent_grant.appointment_id` or `attachment.patient_id` (the revoke-by-source path compares `appointment_id` in Python over grants already loaded by the composite index).

Two lookups the code does issue had no supporting index and still scan after migration 0011: `AttachmentRepository.list_for_clinical_entry` (`attachment.clinical_entry_id`, called from `app/attachments/service.py:332`) and `ConsentRepository.list_patients_for_doctor` (`consent_grant.doctor_id` and `active`, called from `app/clinical/service.py:106`; the composite index leads with `patient_id`).

## Impact

Every clinical request degrades as data grows, against the SR-026 budgets.

## Safety evaluation

Contributes to RISK-007 (clinical information unavailable, through latency).

## Investigation

CR-006 (2026-11-13). The four indexes were added by migration 0011 (TASK-219, QA-approved), which meets SR-026 AC 6 as approved at 1.5; their query-plan check runs the equivalent `select()` on the model, because three of them serve no current query. QA's `EXPLAIN` on a 10 000-row seed showed the two lookups above as `Seq Scan` after 0011. Decision D-29: the two missing indexes are added to TASK-220 as migration 0012 (`attachment.clinical_entry_id`; `consent_grant(doctor_id, active)`), and SR-026 AC 6 names both lookups (1.6, `in_review`). The three 0011 indexes that no current query uses stay, as SR-026 AC 6 requires them.

## Resolution

Resolved by CR-006 through TASK-219 (migration 0011, four indexes, QA-approved) and TASK-220 (migration 0012, the two lookups of D-29, QA-approved). **Verified 2026-11-15 by TASK-226** on the branch head: TS-018 TC-018.5 (`test_migration_0011_indexes.py`) and TC-018.8 (`test_migration_0012_indexes.py`) passed in the backend suite (1743 passed): upgrade and downgrade on an empty and on a populated database (10 000 rows per table), the query plan of each lookup of SR-026 AC 6 uses its index, and the negative control without the indexes scans. On a started stack with an empty database, migrations 0011 and 0012 applied cleanly (1.7 s and 1.6 s wall time including the process start). The status is `resolved`; closing follows the CR.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Performance.

## Version history

- 1.0 (2026-09-17) — Created from the audit findings. `open`.
- 1.1 (2026-11-13) — CR-006 D-29 (TASK-219 QA finding 1): Observed corrected (only `clinical_entry.patient_id` of the four is read by a current query, none by the authorization decision itself); the two unindexed lookups the code issues added; Investigation added; Resolution points at TASK-219 and TASK-220 (migration 0012). Stays `open`.
- 1.2 (2026-11-15) — TASK-226: TASK-220 is QA-approved and the query-plan checks are recorded; `open` → `resolved` (the CR-006 `resolves` link exists).
