---
id: "TASK-200"
type: task
title: "Anchor the module version expression fully"
status: approved
version: "1.3"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-11-02"
links:
  - target: "SR-016"
    relation: implements
  - target: "PRB-028"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-014"
    relation: relates_to
tags: ["security", "modules", "cr:CR-004"]
---

# TASK-200 — Anchor the module version expression fully

- **Software item / unit:** SI-MODHOST discovery (ADD-014).
- **PRB:** PRB-028. **CR:** CR-004.
- **Depends on:** none. Independent; can run in parallel.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** XS (`backend/app/modules/discovery.py`; 1 test file; TS-010)
- **Risk:** no hazard (PRB-028 Safety evaluation; ADR-0005 trusted modules), so no `mitigates`
  link; recorded as "no impact" in CR-004's §7.4 analysis.

## Objective

SR-016 AC 1 (module contract): a manifest version must be a semantic version, nothing after it.
PRB-028 Investigation: `discovery.py:13,29` uses `^\d+\.\d+\.\d+` with `.match`.

## Implementation detail

`_SEMVER_RE = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?")`
used with `fullmatch` (the module contract's version rule, SR-016 AC 1: the semver.org expression, ASCII only). Rejection keeps the
current warning and skip.

## Tests (write first)

`backend/tests/modules/test_discovery.py` (extend): accepted `1.2.3`, `0.1.0-rc.1`, `1.0.0+build.5`;
rejected `1.2.3-evil!`, `1.2.3.4`, `1.2.3 `, `01.2.3`, `1.2`, `v1.2.3`.

## Acceptance criteria

- [x] SR-016 AC 1: a version with trailing characters is rejected at discovery
      (`backend/tests/modules/test_discovery.py`).

## Verification

```sh
cd backend && uv run pytest tests/modules -v && uv run ruff check . && uv run mypy app
cd backend && uv run pytest modules/dicom_viewer/tests -v     # the bundled module's version still passes
```

## Records

- **TS-010** → 1.2 (`in_review`): TC-010.5 (version fully anchored), `verifies` SR-016.
- **PRB-028**: `## Resolution`, `resolved`.

## Definition of Done

- [x] Tests pass; TS-010 `in_review`; PRB-028 `resolved`.
- [x] `traceability-check` shows no error for TASK-200, TS-010, SR-016, PRB-028.

## Implementation and verification (2026-11-02)

- `backend/app/modules/discovery.py`: `_SEMVER_RE` is now the module contract's version rule (SR-016 AC 1; no leading
  zeros, optional pre-release and build) and `_is_valid_manifest` uses `fullmatch`. The warning
  text is "version not a semantic version".
- `backend/tests/modules/test_discovery.py`, class `TestModuleVersionShape`: 7 accepted versions
  and 14 rejected (superseded in round 2: 9 accepted, 23 rejected) (`1.2.3x`, `1.2.3 `, ` 1.2.3`, `1.2.3\n`, `1.2.3-evil!`, `1.2.3.4`, `01.2.3`,
  `1.2`, `v1.2.3`, `1.2.3-`, `1.2.3+`, empty, two 100 000-character inputs). Written first: 8
  cases failed against the old expression.
- The bundled module's version (`0.1.0`) is covered by the existing
  `modules/dicom_viewer/tests/test_audit_module_key.py::test_real_manifest_passes_discovery`.
- Negative control: `fullmatch` put back to `match` -> 8 failed, 36 passed in `test_discovery.py`;
  restored -> all pass.
- Commands: `pytest tests/modules` 55 passed; `pytest modules/dicom_viewer/tests` 25 passed;
  `pytest --cov=app --cov-fail-under=85` 1271 passed, 93.29 % (21 failures in
  `tests/api/test_csrf_enforcement.py` and `tests/auth/test_session_cap_concurrency.py`, files of
  TASK-139 and TASK-199 under way in the same tree; re-run, 63 passed); ruff, black, mypy clean.

## QA review — round 1 (2026-11-02): CHANGES REQUESTED

The anchoring with `fullmatch` works, and the developer's figures reproduce: 55 passed in `tests/modules`, 25 in
`modules/dicom_viewer/tests`, and 8 failed with `fullmatch` changed back to `match`. QA also ran its own mutations:
the old expression fails 9 cases, dropping the no-leading-zero rule fails 1, and dropping pre-release/build fails 4.
There is no ReDoS: adversarial 100 000-character inputs take 0-8 ms and 1 000 000 characters take 49 ms, which is
linear. The verdict is CHANGES REQUESTED because the expression still accepts trailing characters (finding 1). That
is the task's only acceptance criterion. The records also call the expression "SemVer 2.0", and it is looser than
that (finding 2).

1. **HIGH — non-ASCII digits are still accepted, including after `1.2.3`.** In `backend/app/modules/discovery.py:15-17`
   the pattern is a `str` pattern without `re.ASCII`, so `\d` matches any Unicode decimal digit. QA probe:
   `_SEMVER_RE.fullmatch` accepts `"1.2.3٣"` (`1.2.3` followed by ARABIC-INDIC DIGIT THREE), `"1٣.2.3"`
   and `"1１.0.0"` (fullwidth 1). These strings have characters after the version, which the TASK's
   SR-016 AC 1 criterion and PRB-028 exclude, and the registry stores them as given.
   → Fix: compile with `re.ASCII`, or write `[0-9]` for `\d`. Add `"1.2.3٣"` and `"1１.0.0"` to the
   rejected cases in `backend/tests/modules/test_discovery.py:260-278`.
2. **MEDIUM — pre-release and build are looser than SemVer 2.0, but the code comment (`discovery.py:14`), this TASK,
   TS-010 TC-010.5 and the PRB-028 Resolution all say "SemVer 2.0".** `-[0-9A-Za-z.-]+` and `\+[0-9A-Za-z.-]+`
   accept empty identifiers and numeric pre-release identifiers with leading zeros. SemVer 2.0 §9-10 forbids both.
   Accepted today: `1.0.0-01`, `1.0.0-a..b`, `1.0.0-.a`, `1.0.0-a.`, `1.0.0-.`, `1.0.0+a..b`, `1.0.0+.`.
   → Fix: use the semver.org expression with ASCII classes and `re.ASCII`:
   `(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-((?:0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9]*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?`
   QA checked this expression. It accepts all 7 current accepted cases and rejects the cases above and in finding 1.
   It is also linear: 1-14 ms on adversarial inputs of 100 000-200 000 characters.
   Add `1.0.0-01`, `1.0.0-a..b`, `1.0.0-a.` and `1.0.0+a..b` as rejected cases, and `1.0.0--` and `1.0.0+001` as
   accepted cases. The other option is to keep the looser grammar and drop "SemVer 2.0" from all four places, but
   the strict form costs nothing.
3. **LOW — the rejection warning logs the full value.** `discovery.py:37` logs `%r` of the version, and a
   100 000-character version produced a 100 061-character log line. The risk is low: `%r` escapes control
   characters, so no log line can be forged; manifests are trusted code (ADR-0005); and discovery runs once at
   startup.
   → Fix: log `%.80r` (truncated repr) and `len(version)`. `discovery.py:28,31,34` use the same pattern
   (pre-existing, optional).
4. **LOW — the 100 000-character parameters become 100 000-character test IDs.** At
   `backend/tests/modules/test_discovery.py:275-276`, a failure, or the `-v` run in this TASK's own Verification
   block, prints them in full.
   → Fix: `pytest.param("1.2.3-" + "a" * 100_000 + "!", id="long-prerelease")` and `id="long-patch"`.
5. **LOW (records) — SR-016 AC 1 says nothing about the version format.** It reads "A new module can be added by
   implementing the defined module contract". The rule "a semantic version, nothing after it" is this TASK's
   interpretation, and `ModuleManifest.version` (`backend/app/modules/contract.py:24`) is a plain `str` with no
   documented format. Nothing approved says whether a pre-release is allowed or whether `0.0.0` is acceptable.
   Both are valid SemVer, and the tests accept both.
   → Fix: document the rule where the contract is defined: a comment or docstring on `ModuleManifest.version`
   ("SemVer 2.0, ASCII, nothing else"). Word the TASK and TC-010.5 as "the module contract's version rule
   (SR-016 AC 1)". If the human wants the rule as a requirement, SR-016 needs a revision, which is a human
   decision and does not block this task.

Records: TASK-200 → `draft` (1.2). TS-010 stays `in_review` 1.2, and its TC-010.5 text must follow findings 1-2
(it currently claims "SemVer 2.0"). PRB-028 stays `open`, and its Resolution must follow findings 1-2 (the case
count and the "SemVer 2.0" claim). `traceability-check` on TASK-200, TS-010, PRB-028, SR-016 and CR-004:
0 errors. W5 TP-001 → TS-010 `in_review` is expected until approval.

## Round 2 (2026-11-02): QA findings 1-5 addressed

- Finding 1: `re.ASCII` and `[0-9]` classes; `1.2.3\u0663`, `1\u0663.2.3` and `1\uff11.0.0` are rejected.
- Finding 2: the semver.org expression (built from `_NUMERIC`, `_PRE_ID`, `_BUILD_ID` in `discovery.py`).
  Added rejected `1.0.0-01`, `1.0.0-a..b`, `1.0.0-a.`, `1.0.0+a..b`, `1.0.0-.a`, `1.0.0+.` and the three
  Unicode strings; added accepted `1.0.0--` and `1.0.0+001`. `TestModuleVersionShape` is now 9 accepted,
  23 rejected and 1 timing test (a 1 000 000-character adversarial version, bound 2 s).
- Finding 3: warnings in `_is_valid_manifest` log `%.80r`; the version one adds the length.
- Finding 4: the two 100 000-character cases have ids `long-prerelease` and `long-patch`.
- Finding 5: the rule is documented on `ModuleManifest.version` (`backend/app/modules/contract.py`); the
  records say "the module contract's version rule (SR-016 AC 1)". SR-016 is not edited.
- Written first: 9 new rejected cases failed against the round-1 expression.
- Negative control: `[0-9]` back to `\d` and `re.ASCII` removed -> the 3 Unicode cases fail (3 failed, 53
  passed in `test_discovery.py`); restored -> pass.
- Timing of `fullmatch` on 1 000 000-character inputs: `1.0.0-` + `a.`x500 000 + `!` 57 ms; `1.` + 10^6 zeros
  0 ms; `1.0.0-` + `-`x10^6 + `!` 64 ms; `1.0.0+` + `a.`x500 000 + `.` 28 ms (linear).
- Commands: `pytest tests/modules` 67 passed; `pytest modules/dicom_viewer/tests` 25 passed; ruff, black
  clean; `mypy app/modules` clean (7 files).
- Second negative control: `fullmatch` back to `match` with the round-2 tests -> 16 failed, 40 passed.

## QA review — round 2 (2026-11-02): APPROVED

Findings 1-5 of round 1 are closed:
1. The pattern uses `[0-9]` and `re.ASCII`. `1.2.3٣`, `1٣.2.3` and `1１.0.0` are rejected (QA probe).
2. The pattern is the semver.org grammar. QA compared it exhaustively with the reference semver.org expression on
   every string of length 5-9 over the alphabet `01a.-+` (12 091 680 strings) and found 0 differences.
   All 7 malformed-identifier cases from round 1 are rejected.
3. Every warning in `_is_valid_manifest` logs `%.80r`. The version warning adds the length. A 100 000-character
   version now gives a 134-character log line.
4. The two long parameters have the short ids `long-prerelease` and `long-patch`.
5. The rule is documented on `ModuleManifest.version` (`contract.py:24-25`), and the records say "the module
   contract's version rule (SR-016 AC 1)".

QA re-ran its mutations on `test_discovery.py`:

| Mutation | Result |
|---|---|
| `fullmatch` changed to `match` | 16 failed |
| `\d` without `re.ASCII` | 3 failed |
| Round-1 loose pre-release/build | 6 failed |
| Leading zeros allowed | 2 failed |
| Original `^\d+\.\d+\.\d+` | 19 failed |

A deliberately catastrophic nested-quantifier mutation hangs the run in the 100 000-character parameter cases. It
never reaches the 2 s timing test, so a ReDoS regression shows up as a CI job timeout, not as a fast failure. This
is accepted and not a finding.

The 2 s wall-clock bound has a low flakiness risk, so it is not a finding. The same input takes 57 ms here, about
35 times below the bound, and the regex is linear (1-2M-character adversarial inputs take 32-116 ms).

Runs:
- `pytest tests/modules`: 67 passed.
- `pytest modules/dicom_viewer/tests`: 25 passed.
- ruff and black: clean.
- `mypy app`: clean (132 files).

`traceability-check` on TASK-200, TS-010, PRB-028, SR-016 and CR-004: 0 errors.

Status: TASK-200 → `approved`. TS-010 → `approved`. PRB-028 → `resolved` (CR-004 D-8).
