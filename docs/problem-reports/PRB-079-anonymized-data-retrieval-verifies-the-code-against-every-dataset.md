---
id: "PRB-079"
type: problem-report
title: "Anonymized-data retrieval verifies the code with Argon2 against every dataset"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
criticality: minor
links: []
tags: ["performance", "erasure", "hazard:availability", "found-in:cr-006-plan"]
---

# PRB-079 — Anonymized-data retrieval verifies the code with Argon2 against every dataset

## Observed

Found at the CR-006 Plan stage (2026-11-13) while reading the erasure path for TASK-141.
`ErasureService.retrieve_anonymized` (`backend/app/identity/erasure.py:146`) loads every anonymized
dataset (`all_datasets = self._dataset_repo.list()`, `:156`) and runs `self._password_svc.verify(dataset.code_hash, code)`
on each in turn (`:157-158`) until one matches. The code comment says the scan is needed because
Argon2id hashes are salted. Called from `POST` retrieval in `backend/app/api/routers/anonymized_data.py:76`.

## Impact

Each Argon2id verification uses the `PasswordHasher()` defaults (`backend/app/auth/password.py:37`,
about 64 MiB and tens of milliseconds per call). The cost of one retrieval therefore grows linearly
with the number of retained datasets (5-year retention, ADR-0013): a wrong code, or the code of the
last dataset, always runs the full scan. With hundreds of datasets one request holds a worker thread
and a memory peak for seconds; the retrieval rate limit (5 per hour per client, SR-042 AC 4) bounds
repetition per client but not the cost of each request. The same pattern was a defect for activation
tokens (PRB-022, fixed). Not in SR-026 AC 6, which covers authorization and module-gating paths only.

## Investigation

- Lookup design: the dataset has no non-secret lookup key, so the code alone cannot select a row.
  A remedy needs a design decision (for example a code that embeds a random dataset identifier plus the
  secret part, with only the secret part hashed), which changes the retrieval-code format of SR-024 and
  ADR-0013, and how existing codes keep working.
- To confirm: time one retrieval with 1, 100 and 1 000 seeded datasets.

## Safety evaluation

No wrong data is returned: the match is exact and the deadline check is unchanged. The effect is slow
or timed-out retrieval and, under load, delay to other requests on the same worker (RISK-007,
information unavailable; RISK-008 only in that a retrieval may fail and be retried). No new hazard.
Criticality **minor** today: the dataset count is small in the MVP and the rate limit bounds abuse; it
grows with operation time. No release exists, so no notification is needed. The human sets the final
criticality.

## Disposition

Out of CR-006 scope (Plan-gate decision D-23). Needs its own CR with a requirement decision on the
retrieval-code format.

## Version history

- 1.0 (2026-11-13) — Created from CR-006 Plan-stage finding P-9, at the human's Plan-gate decision. Not in CR-006
  scope.
