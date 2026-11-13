---
id: "PRB-022"
type: problem-report
title: "Activation token validation scans the whole account table"
status: rejected
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-13"
criticality: major
links: []
tags: ["performance"]
---

# PRB-022 — Activation token validation scans the whole account table

## Observed

`app/identity/activation.py` validates and activates by calling `repo.list()` and scanning in Python, an O(n) operation per attempt.

## Impact

Activation latency grows with the user base and the endpoint becomes an easy amplification target (SR-033, SR-026).

## Safety evaluation

Contributes to RISK-007 and, indirectly, RISK-009 (a patient cannot activate their account).

## Resolution

Rejected: already fixed before CR-006, working tree verified 2026-11-13 (CR-006 D-1). Evidence: `backend/app/identity/activation.py:67` loads one account with `self._repo.get_by_id(account_id)` and `_validate_token` (`:162-168`) checks only that row. No `list()` scan remains in `app/identity/` for activation (the only `list()` there is the anonymized dataset repository at `erasure.py:156`). The change came with the account-id activation route (commit 03c879e, 2026-10-31, TASK-188 and PRB-070). The regression guard is SR-026 AC 6 (validating an activation token reads at most one account row), tested under CR-006.

## Source

`docs/implementation-plan/AUDIT-FINDINGS.md` — Performance.

## Version history

- 1.0 (2026-09-17) — Created from the audit. `open`.
- 1.1 (2026-11-13) — CR-006 D-1: `rejected`, already fixed.
