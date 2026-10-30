---
id: "PRB-053"
type: problem-report
title: "The raw-SQL guard test flags harmless f-strings and misses some raw SQL"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
criticality: minor
links: []
tags: ["verification", "backend"]
---

# PRB-053 — The raw-SQL guard test flags harmless f-strings and misses some raw SQL

## Observed

While implementing CR-002 TASK-175, `backend/tests/db/test_no_raw_sql.py` failed three times on
lines with no SQL, such as `raise X(f"...") from exc` and `", ".join(...)`. The developer worked
around it with a helper function. QA confirmed the defect on 2026-10-30 with a probe script (not
kept in the repository).

## Impact

The test gives false failures on ordinary code and misses some raw SQL, so it is weak evidence for
SR-031 (no raw SQL built from strings).

## Investigation

`backend/tests/db/test_no_raw_sql.py:16-34` greps only the first source line of each f-string for
SQL keywords, case-insensitively. Lines `:50-56` look for string SQL only inside `text()`. QA's probe
showed three failures:

- `f"failed to update {name}"` is flagged (false positive).
- A multi-line f-string whose SQL starts on a later line is not flagged (false negative).
- `"SELECT ...".format(x)` used outside `text()` is not flagged (false negative).

## Safety evaluation

No product code is affected and no raw SQL was found in the product. SR-031 is also verified by
real-database tests (TS-008 TC-008.3), so the weakness does not leave an unverified safety
function. It does not affect data integrity, a safety-related function or a clinical decision.
No released version exists, so no notification is needed. Hence `minor`.

## Proposed resolution

Check the arguments actually passed to `text()`, `execute()` and `exec_driver_sql()` (an AST walk)
instead of grepping for keywords, and add cases for the three probe results. Needs a task and a CR;
outside CR-002's scope.

## Source

Software developer and QA, CR-002 TASK-175 (2026-10-30).
