---
id: "PRB-095"
type: problem-report
title: "TC-019.4 reference-study test fails about one run in 45 (random UID length)"
status: open
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-25"
updated: "2026-11-25"
criticality: minor
links: []
tags: ["test", "backend", "found-in:TASK-235", "outside:CR-008"]
---

# PRB-095 — TC-019.4 reference-study test fails about one run in 45 (random UID length)

## Observed

`backend/modules/dicom_viewer/tests/test_size_bounds.py::test_reference_study_at_bounds_not_refused` (TC-019.4, TASK-218) sometimes fails with `assert len(data) == MAX_STORED` (for example 157286398 against 157286400). Found by the Software Developer in TASK-235 (2026-11-25): one failure in the first full module run; six isolated runs passed. (A second failure seen later in that task was caused by the task's own change to the `_Frame` stub, not by this defect.) Rate measured by QA in TASK-235 round 1: 68 mismatches in 3000 builds of `_padded_to` (2.3 %, about one run in 45).

## Impact

A green/red verdict on the module suite that depends on chance; a real regression is harder to tell from the flake. The product code is not involved.

## Investigation

`_padded_to` builds a base object, measures it, then builds the final one with the pad length; `_dicom` gives each dataset a `generate_uid()` Media Storage SOP Instance UID. pydicom's UIDs are 64 characters in about 90 % of cases and 61 to 63 in the rest (measured over 20000 UIDs: 64: 17982, 63: 1810, 62: 189, 61: 19), but a UI value is padded to even length when written, so 63 and 64 characters encode alike; the encoded object is 412 bytes in 99 % of builds and 410 in 1 %. The base and the final object differ in length only when their UIDs fall on different sides of that, and the final size then misses `MAX_STORED` (2.3 % of builds). Not fixed in TASK-235 (outside CR-008). Candidate fix: a fixed UID in `_dicom` (as `fixtures.SOP_INSTANCE_UID` does).

## Safety evaluation

No safety impact and no contribution to a RISK: test-only, and a false red, never a false green (the assertion is an exact-size precondition).

## Resolution

Not yet resolved.

## Source

TASK-235 development (2026-11-25).

## Version history

- 1.0 (2026-11-25) — Created from TASK-235. `open`, `minor`, outside CR-008.
- 1.1 (2026-11-25) — TASK-235 QA round 1 (R1-5): title and figures corrected (about one run in 45, not one in ten). Still `open`; the human decides whether it is resolved in CR-008.
