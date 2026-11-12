---
id: "TASK-213"
type: task
title: "CI check that test container images equal the deployment's"
status: approved
version: "1.6"
author: "Carlos Santiago Liceras"
created: "2026-11-12"
updated: "2026-11-12"
links:
  - target: "SR-028"
    relation: implements
  - target: "RISK-010"
    relation: mitigates
  - target: "CR-005"
    relation: relates_to
  - target: "PRB-040"
    relation: relates_to
  - target: "ADD-024"
    relation: relates_to
  - target: "TS-013"
    relation: relates_to
  - target: "TASK-211"
    relation: relates_to
  - target: "TASK-212"
    relation: relates_to
tags: ["ci", "verification", "soup", "cr:CR-005", "control:protective"]
---

# TASK-213 — CI check that test container images equal the deployment's

- **Software item / unit:** SI-DEVINFRA `U-INF-CIPipeline` (ADD-024), `infra/check_image_pins.py`.
- **PRB:** PRB-040. **CR:** CR-005 (AC-6; negative control). **ADR:** ADR-0020 (Accepted; amended 2026-11-12,
  acknowledged by the human 2026-11-12).
- **Depends on:** TASK-211 (same script, test file and `--root` mechanism), TASK-212 (the
  definition it reads).
- **Branch:** `bug/build-hygiene`.
- **Size:** M (`infra/check_image_pins.py`, `infra/tests/test_check_image_pins.py`, fixture trees,
  TS-013, ADD-024, PRB-040).

## Objective

SR-028 AC-9, enforcement: CI fails, naming file and line, when a test's SOUP image reference
differs from the deployment definition or has no digest, so a later edit cannot bring a floating
tag back (PRB-040 grew from two call sites to eleven without one).

## Implementation detail

Per ADR-0020, three rules over the repository root:

1. `backend/postgres_image.py` (beside the test roots, not in `backend/tests/`: see ADR-0020,
   amended): exactly one assignment to `POSTGRES_IMAGE` at the start of a line, in one of two
   forms, read as text:
   - one line: `POSTGRES_IMAGE = "<ref>"`;
   - parenthesised (as `black` writes it, and as at HEAD, lines 12-14): `POSTGRES_IMAGE = (`, then
     one line holding a single string literal `"<ref>"`, then a line holding `)`.

   The value is one plain string literal, single or double quoted. Implicit or `+` concatenation,
   an f-string or other prefix, a name, a missing `)`, an annotation, or anything else on those
   lines is a finding ("test image definition not in a recognised form"), never passed. `<ref>`
   has a digest and equals the `image:` of the `postgres` service in `infra/docker-compose.yml`. A
   missing file, a missing or second assignment, or a missing Compose service is a finding. A
   finding about the value names the line of the string literal.
2. Every workflow `services.<name>.image` must equal the Compose `image:` of the service with the
   same image repository (`postgres`, `redis` at HEAD; SR-028 AC-9 covers CI service containers,
   which are test containers of SOUP components). A service image with no Compose counterpart is
   a finding.
3. A string literal of the form `"<repo>:<tag…>"` or `'<repo>:<tag…>'`, where `<repo>` is the image
   repository of any Compose service and `<tag>` starts with an alphanumeric (so
   `"redis://localhost:6379/0"` does not match), in `backend/**/*.py` outside
   `backend/postgres_image.py`, is a finding (`.venv/` excluded). Only that one path is exempt: a
   file at the old planned path `backend/tests/postgres_image.py` is checked like any other.

Messages, e.g. `backend/postgres_image.py:13: test image differs from infra/docker-compose.yml:126: <ref>`
(13 is the literal's line in the parenthesised form at HEAD).

## Tests (write first)

New class `TestImagesMatchDeployment` in `infra/tests/test_check_image_pins.py`, on fixture trees
(`--root`), with the definition at `backend/postgres_image.py` in each tree:

- Rule 1, forms: one-line definition equal (pass); parenthesised definition equal (pass, the HEAD
  form); parenthesised with two implicitly concatenated literals (`"postgres:16.15"` /
  `"@sha256:…"` on two lines) (fail); `+` concatenation (fail); f-string (fail); a name instead of
  a literal (fail); `(` with no closing `)` (fail); two assignments (fail); definition file
  missing (fail). Each failing case names the expected line.
- Rule 1, value: tag differs; digest missing; digest differs (each fail, at the literal's line,
  in the parenthesised form).
- Rule 2: workflow service `postgres:16` against a pinned Compose image (fail).
- Rule 3: a `"postgres:16"` literal in `backend/tests/db/x.py` (fail) and in
  `backend/modules/dicom_viewer/tests/x.py` (fail); a definition file at the old path
  `backend/tests/postgres_image.py` (fail, not exempt); `"redis://localhost:6379/0"` (pass).

## Acceptance criteria

- [x] CR-005 AC-6: each failing case is reported with file and line; the passing cases pass; the
      check passes on the repository.
- [x] Negative control: on a scratch copy, setting `POSTGRES_IMAGE` to `postgres:16`, dropping its
      digest, or adding `PostgresContainer("postgres:16")` to one test each make the check exit 1.
- [x] Records: TS-013 1.6 gains TC-013.13 (unit, test-image rules); ADD-024 1.3 describes the
      rules; PRB-040 `## Resolution` written (TASK-212, TASK-213).
- [x] TS-013 TC-013.14 coverage note (TASK-212 QA, LOW 3): the started-container test
      (`tests/db/test_postgres_image.py`) covers the `pg_container` fixture only; the other ten
      call sites are held to the definition by rule 3 (TC-013.13), and the definition to the
      Compose file by rule 1.

## Verification

```sh
python3 -m unittest discover -s infra/tests -v
python3 infra/check_image_pins.py; echo "exit $?"   # 0
```

## Records

TS-013, ADD-024 (version rule in TASK-211). PRB-040 `resolved` only after QA approves (AC-11).

## Carried from TASK-211 QA (round 2, 2026-11-12)

Four LOW findings on the same script, test file and records; fix them here (details and
reproductions in TASK-211, "QA review round 2"):

- [x] Workflows: the `\` join in `logical_lines` must not swallow a YAML key or list item line (or a
      blank line) after a stray trailing `\`; fixture.
- [x] Dockerfiles: skip comment lines inside a `\` continuation, as Docker does; fixture.
- [x] One "not seen" list in the docstring, ADD-024 and TS-013.
- [x] `--root ""` exits 2 (`args.root is not None`); test case.

## Verification results (Software Developer, 2026-11-12)

Files: `infra/check_image_pins.py` (rules 1-3 in `image_findings`, `service_images`,
`python_sources`; `logical_lines(lines, yaml)`; `--root` tested with `is not None`),
`infra/tests/test_check_image_pins.py` (`TestImagesMatchDeployment`, three LOW tests),
fixtures `infra/tests/fixtures/tools/base/infra/docker-compose.yml` and
`base/backend/postgres_image.py` (every `--root` tree now carries a valid pair, because a missing
definition is a finding), `backslash_stray.yml`, `Dockerfile.uv_comment_continuation`. Records:
TS-013 (TC-013.13, TC-013.14 coverage note, one "not seen" list), ADD-024, PRB-040 `## Resolution`.
`backend/` untouched, so `ruff`/`black` were not run.

- `python3 -m unittest discover -s infra/tests -v`: 151 tests OK (48 in `test_check_image_pins`).
- `python3 infra/check_image_pins.py`: exit 0, no output.
- Negative control (scratch copy as a throwaway git repository, `; echo "exit=$?"`): baseline 0;
  `POSTGRES_IMAGE` = `postgres:16` 1 (`backend/postgres_image.py:13`); digest dropped 1 (`:13`);
  CI `postgres` service image `postgres:16` 1 (`ci.yml:51`, also reported by the digest rule);
  `x = "postgres:16"` appended to `backend/tests/db/conftest.py` 1 (`:37`); copy of the definition at
  `backend/tests/postgres_image.py` 1 (`:13`, not exempt); `"a" + "b"` definition 1 (`:1`);
  definition file removed 1; after each restore 0. Carried LOW forms: stray `\` before
  `- uses: actions/checkout@v4` 1 (`ci.yml:16`); comment line in a `RUN pip install \` continuation 1
  (`backend/Dockerfile:25`); `--root ""` 2.
- Assumptions: rule 1 form findings are reported at the assignment line, value findings at the
  literal's line, a missing definition at line 1; Compose `image:` values containing `$` are ignored by
  rules 2-3; rule 3 also covers `redis`, `nginx` and `chrislusf/seaweedfs` literals (any Compose
  repository), as the TASK says.

Carried LOW findings: (1) `logical_lines(yaml=True)` ends a join before a blank, key or list-item line
(`backslash_stray.yml`); (2) Dockerfile continuations skip comment lines
(`Dockerfile.uv_comment_continuation`); (3) one "not seen" list in the docstring, ADD-024 and TS-013
(the TS-013 list: script file, YAML anchor or template, composite actions; findings 1-2 are fixed, so
they are not in it); (4) `--root ""` exits 2 (`test_empty_root_exits_2`).

## QA review round 1 (2026-11-12): CHANGES REQUESTED

Verified: `python3 -m unittest discover -s infra/tests -v` 151 OK (also under Python 3.12.3);
`python3 infra/check_image_pins.py` exit 0. Negative control on a scratch copy (throwaway git
repository): definition `postgres:16` 1 (`:13`); digest dropped 1 (`:13`); CI service `postgres:16` 1
(`ci.yml:51`, twice); CI service other digest 1; stray `"postgres:16"` in `tests/db/conftest.py` 1
(`:37`); old path 1 (`:13`, only once the file is `git add`ed, see LOW 4); implicit and `+`
concatenation, f-string, name, second assignment, missing file 1 each; the four carried LOW forms
1, 1, 2 as claimed. The image rule's per-file output is identical to HEAD on every fixture and
tracked Compose file, Dockerfile and workflow; `run: |` blocks with `\` continuations
(`npx \`, `pip install \ -q \ uv`, `docker run \ -e …`) report as at HEAD. The "not seen" list
is identical in the docstring, ADD-024 and TS-013. Rule 3 has no hit on real `backend/` code
(every `redis:`/`postgres:` literal there is a URL). `traceability-check` on CR-005 (two hops,
170 of 439 records): 0 errors; W5/W6 only on older records or records back in `in_review`.

- **[HIGH] The definition file can carry a floating image and the check passes** —
  `infra/check_image_pins.py:274,319` (`DEFINITION_START = ^POSTGRES_IMAGE\b`) and `:383`
  (`if path == DEFINITION: continue`). Only column-0 assignments are counted, and the whole file
  is exempt from rule 3. Reproduced on a `--root` tree, both exit 0: (a) `POSTGRES_IMAGE = "<pinned>"`
  followed by `if os.getenv("X") is None:` / `    POSTGRES_IMAGE = "postgres:16"`; (b)
  `POSTGRES_IMAGE = "<pinned>"` plus `OTHER = "postgres:16"` (importable by any test). This contradicts
  the TASK, ADR-0020 ("a second assignment is a finding") and TS-013 TC-013.13 for the one file the
  control rests on. → Count every `^\s*POSTGRES_IMAGE\s*(?::[^=]*)?[-+*|]?=` (and `global
  POSTGRES_IMAGE`) after the first as "second POSTGRES_IMAGE assignment", and run the rule-3 literal
  scan over the definition file too, skipping only the recognised literal line. Fixtures for (a), (b).
- **[MEDIUM] Call sites with no literal bring a floating tag back unseen** — rule 3,
  `infra/check_image_pins.py:378-389`. Exit 0 for `PostgresContainer()` (testcontainers default
  `postgres:latest`, `testcontainers/postgres/__init__.py:50`), `PostgresContainer("postgres")`, and
  `"docker.io/library/postgres:16"` / `"library/postgres:16"`. ADR-0020:63, ADD-024:60 and the PRB-040
  Resolution say "a (new) call site cannot bring a floating tag back", and the TS-013 TC-013.14
  coverage note says the ten other call sites are "held to the definition by rule 3": neither holds
  for these forms. → Either (preferred) add to rule 3: every `PostgresContainer(` in `backend/**/*.py`
  must have `POSTGRES_IMAGE` as its first argument, and let the literal pattern take an optional
  `registry/namespace/` prefix and a bare quoted repository inside a `*Container(` call; or narrow the
  claims in ADR-0020 (dated note, human acknowledgement), ADD-024, TS-013 and PRB-040 and add these
  forms to the "not seen" list. Fixtures either way.
- **[LOW 1] Rule 3 also matches `host:port` and log strings** — `"postgres:5432"`, `"redis:6379"`,
  `"redis:connected"` in `backend/` are findings (fail closed; none occurs today; numeric tags such as
  `postgres:16` prevent a simple exclusion). → Name this false-positive form in the docstring,
  ADD-024 and TS-013 so the next author rewrites the literal instead of weakening the rule.
- **[LOW 2] Rule 2 reads only block-style `services.<name>.image`** — `service_images`,
  `infra/check_image_pins.py:279,287`. A flow-style `postgres: {image: "postgres:16"}` service passes
  both rule 2 and the image rule; a job `container:` or `uses: docker://` naming a SOUP repository with
  a different (pinned) digest passes rule 2. → Report a service line with an inline mapping as "not in a
  recognised form", or add these forms to the "not seen" list.
- **[LOW 3] Test module needs Python 3.12** — `infra/tests/test_check_image_pins.py:392`
  `f"redis:7.4.12@sha256:{"b" * 64}"` (PEP 701 nested quotes) makes the whole module a SyntaxError on
  3.11 (HEAD parsed on 3.11); the `image-pins` job uses the runner's unpinned `python3`. →
  `{'b' * 64}`.
- **[LOW 4] PRB-040 Resolution not exact or fully reproducible** — PRB-040:77 shows the one-line form;
  the source has the parenthesised form (literal on line 13). PRB-040:94 "putting a file at
  `backend/tests/postgres_image.py` … exit 1": in default mode rule 3 reads `git ls-files`, so an
  untracked file passes (reproduced: exit 0 until `git add`). → Show the parenthesised form and say the
  scratch-copy files are added to the index (rule 3 reads tracked files, as the image rule does).

Boxes left unticked; PRB-040 stays `open`. Round 2: re-run the negative control above plus (a), (b)
and the MEDIUM forms.

## Round 2 (Software Developer, 2026-11-12)

Verification: `python3 -m unittest discover -s infra/tests -v` 160 tests OK, also under Python 3.11
(`python3.11`, 160 OK); `python3 infra/check_image_pins.py` exit 0 (3.11 too). Negative control on a
throwaway git copy (files `git add`ed, exit codes captured, reset between cases): baseline 0; (a)
indented `POSTGRES_IMAGE = "postgres:16"` under an `if` 1 (`backend/postgres_image.py:16`, second
assignment); (b) `OTHER = "postgres:16"` 1 (`:15`, second image literal); `PostgresContainer()` 1
(`backend/tests/db/conftest.py:15`, `<none>`); `PostgresContainer("postgres")` 1 (`:15`);
`PostgresContainer(IMG)` 1; `"docker.io/library/postgres:16"` 1 (`conftest.py:37`);
`"postgres:5432"` 1 (`:37`); flow-style CI service `postgres: {image: "postgres:16.15"}` 1
(`ci.yml:50`); flow-style Compose service 1 (`docker-compose.yml:125`); final baseline 0.

| Finding | Fix |
|---|---|
| HIGH | `DEFINITION_START` is now `^\s*POSTGRES_IMAGE\s*(?::[^=]*)?[-+*|]?=(?!=)` or `global ... POSTGRES_IMAGE`; every start after the first is "second POSTGRES_IMAGE assignment" at any indentation. Rule 3 scans `backend/postgres_image.py` too, skipping the recognised literal line and the assignment lines (a missing or unrecognised definition is a finding already, so it is not scanned). Message in the definition file: "second image literal in backend/postgres_image.py". Tests: indented-`if`, annotated, augmented, `\|=`, `global`, `==` passes, `OTHER = "postgres:16"` and `docker.io/...` in the definition. |
| MEDIUM | New rule 4: every `PostgresContainer(` in `backend/**/*.py` (not `class PostgresContainer(`) must have `POSTGRES_IMAGE` or `image=POSTGRES_IMAGE` as its first argument, also across lines; else a finding at the call line with the first argument (`<none>` when empty). A line already reported by rule 3 is not reported twice. Rule 3 pattern takes an optional `registry/namespace/` prefix. All eleven real call sites are `PostgresContainer(POSTGRES_IMAGE)` and pass. Tests: no argument, `"postgres"`, another name, `image=` other name, extra first argument, starred, name prefix, multi-line; passes for both forms and multi-line. Rule stated in the docstring, ADD-024 and TS-013 (TC-013.13). |
| LOW 1 | `"postgres:5432"` / `"redis:6379"` / `"redis:connected"` named as a fail-closed false positive in the docstring, ADD-024 and TS-013; test. |
| LOW 2 | Rule 2 reports a service written as an inline mapping (`name: {image: ...}`) in workflows and Compose ("service as an inline mapping, its image is not compared"); test. The "not seen" list now also names a job `container:` / `uses: docker://` image (image rule only), another container class and an import of `POSTGRES_IMAGE` from another module, identically in the docstring, ADD-024 and TS-013. |
| LOW 3 | `f"redis:7.4.12@sha256:{'b' * 64}"`; the module imports and passes on 3.11; no other 3.12-only syntax (whole suite run under 3.11). |
| LOW 4 | PRB-040 Resolution shows the parenthesised form with the literal on line 13 and says the scratch files are `git add`ed because the default mode reads `git ls-files`; it also lists the new rule and `PostgresContainer()` control. |

Claims re-checked: ADR-0020:63 ("a new call site cannot bring a floating tag back"), ADD-024:60,
the PRB-040 Resolution and the TS-013 TC-013.14 note are now true for `PostgresContainer` call sites
(rules 3 and 4). Residual: a container class other than `PostgresContainer` or an import of
`POSTGRES_IMAGE` from another module is not seen; ADD-024, TS-013 and PRB-040 now say
"`PostgresContainer` call site" and list this. ADR-0020 not edited; its wording is slightly broader
than "PostgresContainer" (for the human to note). Boxes left unticked; PRB-040 stays `open`.

## QA review round 2 (2026-11-12): APPROVED

Verified by reproduction (exit codes captured). `python3 -m unittest discover -s infra/tests -v`
160 OK under Python 3.15.2 and under `python3.11` (160 OK; both modules also `ast.parse` on 3.11);
`python3 infra/check_image_pins.py` exit 0 under both. Round-1 findings, on `--root` probe trees
(fixtures `base` + `uses_pass.yml`): HIGH (a) indented `POSTGRES_IMAGE = "postgres:16"` and
`= "postgres"` under an `if` 1 (`:6`, second assignment); (b) `OTHER = "postgres:16"` 1 (`:4`,
second image literal); annotated, `+=`, `global` + rebinding 1 each; `POSTGRES_IMAGE ==` 0. MEDIUM:
`PostgresContainer()` 1 (`<none>`), `("postgres")` 1, `(IMG)` 1, `"docker.io/library/postgres:16"` 1,
`"library/postgres:16"` 1, `testcontainers.postgres.PostgresContainer()` 1, `(POSTGRES_IMAGE + "")` 1,
`(port=5432)` 1, a comment before the argument 1 (fails closed); multi-line
`PostgresContainer(\n    POSTGRES_IMAGE,\n)` 0, `image=POSTGRES_IMAGE` 0,
`(POSTGRES_IMAGE, port=1)` 0. LOW 1: `"postgres:5432"` 1, documented in the docstring, ADD-024 and
TS-013. LOW 2: flow-style CI service (pinned or floating) 1 (`ci.yml:4`), flow-style Compose
`postgres` 1 (plus "no postgres service image"); a service with a trailing comment 0; anchors and
`null` services are reported (fail closed). LOW 3: fixed, module imports on 3.11. LOW 4: PRB-040
Resolution shows the parenthesised form and the `git add` step; reproduced (an untracked copy at the
old path exits 0, `git add`ed exits 1).

Negative control on a throwaway git copy of the repository (`git ls-files -co --exclude-standard`,
`git add -A` per case, `git reset --hard` between cases): baseline 0; definition `postgres:16` 1
(`postgres_image.py:13`); digest dropped 1 (`:13`); CI `postgres` service other digest 1
(`ci.yml:51`); `PostgresContainer("postgres:16")` in `tests/db/conftest.py` 1 (`:15`);
`PostgresContainer()` there 1 (`:15`); `PostgresContainer("postgres")` in
`modules/dicom_viewer/tests/test_audit_module_key.py` 1 (`:79`); indented second assignment 1
(`:16`); `OTHER = "postgres:16"` 1 (`:15`); flow-style CI service 1 (`ci.yml:50`); flow-style Compose
`postgres` 1 (`docker-compose.yml:125`); copy at `backend/tests/postgres_image.py` 1 (`:13`); final
baseline 0.

Regressions: none. The image rule's output and exit code are identical to HEAD on all 52 tracked
Compose files, Dockerfiles, workflows and fixtures (HEAD script with `REPO_ROOT` patched). On the
real files `service_images` reads `infra/docker-compose.yml` (reverse-proxy, postgres :126, redis,
object-store) and `ci.yml` (postgres :51, redis :64) with no inline-mapping finding; all eleven real
`PostgresContainer(POSTGRES_IMAGE)` call sites pass. The "not seen" list is identical in the
docstring, ADD-024 and TS-013. `traceability-check` (fallback parser, CR-005 scope two hops, 171
records): 0 errors; 19 warnings, all W5/W6 on older records or on records kept `in_review` by CR-005
(ADD-024, TS-013, SOUP-001), none new from this task.

Developer notes: (2) ADD-024 1.3 and TS-013 1.6 not bumped is correct: both versions were opened
by TASK-211, stay `in_review`, and their version histories record what TASK-213 added. (1) see
MEDIUM below: the ADR needs a dated note and human acknowledgement.

Findings (none blocking; carried to TASK-216, Checkpoint C):

- **[MEDIUM] ADR-0020 (Accepted) does not describe rule 4 and overclaims "a new call site"** —
  `docs/design/adr/0020-tool-and-test-image-pins-in-the-pin-check.md:62-64`. The Decision lists the
  literal rule only and says it means "a new call site cannot bring a floating tag back". Round 1
  showed the literal rule alone does not give that; the guarantee now rests on rule 4, which the
  Accepted decision does not contain, and it holds for `PostgresContainer` calls only: a
  `DockerContainer(...)` call site already exists (`backend/tests/auth/test_session_cap_concurrency.py:48`,
  Redis), and `DockerContainer("postgres")` or `RedisContainer()` exits 0. A new enforcement rule
  and a narrower guarantee are a change to an Accepted decision, so (as for the TASK-212 amendment)
  this needs a dated note and the human's acknowledgement, not a silent wording fix. → Add under
  that bullet: "> Amended 2026-11-12 (TASK-213 QA): the literal rule alone does not stop a call with
  no literal (`PostgresContainer()` defaults to `postgres:latest`). A fourth rule makes every
  `PostgresContainer(` call in `backend/**/*.py` take `POSTGRES_IMAGE` as its image; the guarantee
  covers `PostgresContainer` call sites. Other container classes (`DockerContainer`, used for Redis
  in `tests/auth/test_session_cap_concurrency.py`) are not checked." Update the README note line and
  have the human acknowledge it, before TASK-216 closes CR-005.
- **[LOW 1] "Every later assignment ... in any form" is broader than the regex** —
  `infra/check_image_pins.py:286-288` (`DEFINITION_START`), docstring, ADD-024, TS-013 TC-013.13 and
  its unit description. In `backend/postgres_image.py`, after the pinned definition, each of these
  exits 0 with a tagless value: `POSTGRES_IMAGE, _X = "postgres", 0`; `_X, POSTGRES_IMAGE = ...`;
  `(POSTGRES_IMAGE := "postgres")`; `for POSTGRES_IMAGE in ["postgres"]:`;
  `from os import sep as POSTGRES_IMAGE`; `x = 1; POSTGRES_IMAGE = "postgres"`;
  `globals()["POSTGRES_IMAGE"] = ...`. None is an accidental form. → Either read the definition
  with `ast.parse` (text, no import, standard library) and report every `Name` store, `alias`
  `asname`, `Global` or `NamedExpr` target named `POSTGRES_IMAGE` after the first top-level
  `Assign`; or say "at the start of a statement line (plain, annotated, augmented, `global`)" and add
  "tuple unpacking, `:=`, `for`, `import ... as` or a `;`-joined rebinding" to the "not seen" list.
- **[LOW 2] Call-site forms missing from the "not seen" list** — rule 4,
  `infra/check_image_pins.py:295,436-442`. Both exit 0: `from testcontainers.postgres import
  PostgresContainer as PC` + `PC()`; and a local `POSTGRES_IMAGE = "postgres"` in a test file +
  `PostgresContainer(POSTGRES_IMAGE)` (a rebinding, not an import from another module). → Report a
  `PostgresContainer as` import and any `POSTGRES_IMAGE` binding in `backend/**/*.py` outside the
  definition file (apply `DEFINITION_START` to every file), or add both forms to the list in the
  docstring, ADD-024 and TS-013.
- **[LOW 3] "none occurs in the repository" is false for one item** — ADD-024 (end of the "not
  seen" sentence) and TS-013 (unit description). The list includes "a container class other than
  `PostgresContainer`", and `DockerContainer(_pinned_redis_image())` occurs at
  `backend/tests/auth/test_session_cap_concurrency.py:48` (it reads the Compose `redis` image at run
  time, so it is pinned today, but the pin check does not see it). → Replace with "none occurs in
  the repository apart from the `DockerContainer` Redis call in
  `tests/auth/test_session_cap_concurrency.py`, which reads the Compose image at run time".

TASK `in_review → approved`; boxes ticked; PRB-040 `open → resolved` (Resolution updated). TS-013
and ADD-024 stay `in_review` (TASK-209..212 pattern).

## Version history

- 1.0 (2026-11-12) — Created at the CR-005 Plan stage (Software Architect role); `draft`.
- 1.1 (2026-11-12) — QA (TASK-211 round 2): four carried LOW findings added; `draft` unchanged.
- 1.2 (2026-11-12) — TASK-212 QA findings (Software Architect role): definition path
  `backend/postgres_image.py` in rules 1 and 3, messages and fixtures (MEDIUM 1); rule 1 reads the
  one-line and the parenthesised form, any other form is a finding, with fixtures (MEDIUM 2,
  ADR-0020 amended); TC-013.14 coverage note added to the records criteria (LOW 3). `draft`
  unchanged; the four carried LOW findings are kept.
- 1.3 (2026-11-12) — Built (Software Developer role); evidence above; `draft → in_review`. Boxes left
  unticked for QA; PRB-040 stays `open`.
- 1.4 (2026-11-12) — QA review round 1: CHANGES REQUESTED (1 HIGH, 1 MEDIUM, 4 LOW, above);
  `in_review → draft`.
- 1.5 (2026-11-12) — Round 2 (Software Developer role): QA round 1 findings fixed (above);
  `draft → in_review`. Boxes left unticked for QA; PRB-040 stays `open`.
- 1.6 (2026-11-12) — QA review round 2: APPROVED (1 MEDIUM, 3 LOW, non-blocking, carried to
  TASK-216 and ADR-0020). `in_review → approved`; boxes ticked; PRB-040 `open → resolved`; TS-013 and
  ADD-024 stay `in_review`.
