# Prompt: Migrate medhub-01's design record into MedTrace's required structure

Paste everything below this line into a fresh agent session with write access to this
repository (`medhub-01`). It is self-contained: it does not assume the agent has seen
MedTrace's source code, only this repository.

---

## Task

You are migrating the design record of this repository (`medhub-01`) into the exact
folder/file/frontmatter structure required by **MedTrace**, a desktop application that
manages IEC 62304 design records as one Markdown file per design element inside a fixed
folder taxonomy, with structured YAML frontmatter. The goal is for MedTrace to be able to
open this project's design folder directly and show every element as valid (zero invalid
files) with the correct types, statuses, and traceability links.

This is a **format migration**, not a content rewrite. Preserve the substance of every
document (summaries, descriptions, acceptance criteria, rationale, risk analysis,
implementation detail, tests, definition of done, audit notes, etc.) — you are
restructuring *metadata* out of prose into frontmatter fields and normalizing *location*,
not rewording or shortening the technical content.

## 1. Target structure (MedTrace's requirements — do not deviate)

### 1.1 Folder taxonomy and ID prefixes

Every element file lives in exactly one of these folders, matching its `type`:

| `type` value | Folder | ID prefix | ID pattern |
|---|---|---|---|
| `user-need` | `design-inputs/user-needs/` | `UN` | `UN-###` (3+ digits) |
| `nfr` | `design-inputs/system-requirements/non-functional/` | `NFR` | `NFR-###` |
| `regulatory-requirement` | `design-inputs/system-requirements/regulatory/` | `RR` | `RR-###` |
| `software-requirement` | `design-inputs/software-requirements/` | `SR` | `SR-###` |
| `architecture-doc` | `design-outputs/architecture/` | `ADD` | `ADD-###` |
| `task` | `design-outputs/tasks/` | `TASK` | `TASK-###` |
| `test-specification` | `design-outputs/tests-specifications/` | `TS` | `TS-###` |
| `risk` | `risks/` | `RISK` | `RISK-###` |
| `test-plan` | `test-plans-reports/plans/` | `TP` | `TP-###` |
| `test-report` | `test-plans-reports/reports/` | `TR` | `TR-###` |

All ten folders must exist at the project root (even if empty), plus two more:
`source-links/` (plain reference files pointing at external source locations — not
scanned as elements) and `reports/` (MedTrace writes generated evidence there; leave
empty). An optional `templates/` folder can hold one file per type
(`templates/<type>.md`) supplying default body content for *newly created* elements in
the app — not relevant to migrating existing content, skip it.

**Critical validation rule:** the ID's prefix must exactly match the file's folder, and
the numeric part must be 3+ digits with **no letter suffix**. `TASK-004` is valid;
`TASK-004a` is **not** — see §3.5 for how to handle this repository's lettered IDs.

### 1.2 Frontmatter schema (every field is mandatory except `tags`)

Each file starts with a YAML frontmatter block, in this exact field order, followed by a
blank line and the Markdown body:

```yaml
---
id: "UN-005"
type: user-need
title: "Patient ownership and control of their clinical data"
status: approved
version: "1.0"
author: "Migration"
created: "2026-01-01"
updated: "2026-01-01"
links:
  - target: "UN-004"
    relation: relates_to
tags: []
---

(body content here)
```

Field rules:
- `id` — string, unique, matches the ID pattern for its folder.
- `type` — one of the ten values in the table above (exact string, e.g. `user-need`, not `User Need`).
- `title` — non-empty string, no ID prefix inside it (the ID already carries that).
- `status` — **exactly** one of: `draft`, `in_review`, `approved`, `obsolete`. No other spellings are accepted (not `Approved`, not `Completed`, not `Not started` — see §3.2 for the mapping table).
- `version` — non-empty string (quote it, e.g. `"1.0"`, so YAML doesn't coerce it to a number).
- `author` — non-empty string.
- `created`, `updated` — ISO 8601 dates (`YYYY-MM-DD`).
- `links` — **always an array, use `[]` when empty, never omit the field.** Each entry is `{ target: "<ID>", relation: <one of the six below> }`. `target` must be an ID that will exist somewhere in the migrated set — a link to a non-existent ID is not a hard error in MedTrace (it shows up as a "broken link" finding in the Verification view), but a link to a section reference or free-text label (not an element ID) is invalid input and must not be emitted as a link at all — see §3.4.
- Allowed `relation` values: `satisfies`, `derives_from`, `implements`, `verifies`, `mitigates`, `relates_to`. There is no `depends_on` relation — see §3.4 for the mapping.
- `tags` — array of strings, optional content-wise but the field itself must be present (use `[]` if none).

## 2. Source format in this repository

Based on sampled files (`requirement-UN-005.md`, `requirement-NFR-004.md`,
`requirement-SR-005.md`, `TASK-004-docker-compose-topology.md`), the current design
record has **no YAML frontmatter at all** — every field is embedded as prose or Markdown
headings inside the body. Two distinct source formats exist:

### 2.1 Requirement files (`design-inputs/user-needs/`, `design-inputs/non-functional-requirements/`, `design-inputs/software-requirements/`)

Filenames: `requirement-<PREFIX>-<###>.md`. Structure observed:

```
# <PREFIX>-<###> <Title>

## Summary
<one paragraph>

## Description
<prose>

## Acceptance Criteria
<numbered list>

## Origin Requirement           <- SR files only
Derived from: User Need UN-003 "...", UN-004 "...", and NFR-004 "...".

## Risk Analysis
### Rationale
<prose>
### Potential Risks
<bullet list>
### Control Measures
<bullet list>

## Status
Approved                        <- also seen as "Approve" (typo) — treat as approved

## Version History
Version 1.0 - Initial creation
(may have multiple lines, e.g. "Version 1.1 - Clarified ... " when a requirement was revised or split)
```

`design-inputs/non-functional-requirements/` has no separate regulatory folder — GDPR,
audit-log and similar compliance-driven NFRs (e.g. `NFR-004`) live here alongside purely
technical NFRs (performance, availability). **Do not** auto-reclassify any NFR as
`regulatory-requirement` — see §3.6.

### 2.2 Task files (`implementation-plan/phase-*/TASK-*.md`)

Filenames: `TASK-<###>[<letter>]-<slug>.md`, nested under a phase subfolder
(`phase-0-foundation/`, `phase-1-persistence-audit/`, … `phase-9-integration-test-compliance/`).
Structure observed:

```
# TASK-004 — Docker Compose topology + reverse proxy

- **Phase:** 0 — Foundation & toolchain
- **Software item / unit:** ...
- **Implements:** SR-001, SR-022, §07 (Deployment View)
- **Depends on:** TASK-002 (must be merged first)
- **Branch:** `enabler-story/docker-compose-topology`
- **Status:** Completed

## Objective
## Interfaces to honor
## Implementation detail
## Tests (write first — TDD, CLAUDE.md §4)
## Acceptance criteria
## Definition of Done
## Audit verdict (2026-06-29)        <- present only on some tasks, e.g. remediated ones
```

Two files at `implementation-plan/` root (`TASK-TEMPLATE.md`, `AUDIT-FINDINGS.md`,
`AUDIT-LEDGER.md`, `SMOKE-RESULTS.md`, `README.md`) are **not** individual task records —
do not migrate them as elements; leave them where they are.

## 3. Field-by-field mapping and decision rules

### 3.1 `id`, `type`, folder, filename

The prefixes already match MedTrace's convention (`UN`, `NFR`, `SR`, `TASK`), so the
numeric ID is unchanged. Set:
- `design-inputs/user-needs/requirement-UN-###.md` → `type: user-need`, destination `design-inputs/user-needs/`
- `design-inputs/non-functional-requirements/requirement-NFR-###.md` → `type: nfr`, destination `design-inputs/system-requirements/non-functional/`
- `design-inputs/software-requirements/requirement-SR-###.md` → `type: software-requirement`, destination `design-inputs/software-requirements/`
- `implementation-plan/phase-*/TASK-###[letter]-*.md` → `type: task`, destination `design-outputs/tasks/` (drop the phase subfolder — see §3.3 for where that information goes instead)

Rename each file to MedTrace's convention `<ID>-<slug>.md` (slug = lowercased title,
non-alphanumerics to hyphens, ~6 words) for consistency with how MedTrace itself names
files it creates. This is cosmetic only — MedTrace discovers elements by scanning
frontmatter `id`, never by filename — so if renaming every file is inconvenient, keeping
the original filenames is also acceptable; just don't skip this without deciding either
way.

### 3.2 `status`

Map source status text to MedTrace's four-value enum. Do not invent new statuses.

| Source text (requirements) | → `status` |
|---|---|
| `Approved`, `Approve` (typo variant seen in the corpus) | `approved` |

| Source text (tasks, `**Status:**` line) | → `status` |
|---|---|
| `Completed`, `Completed (audit-verified ...)`, `Completed (fix/... )`, `Completed (remediated by TASK-###a)` | `approved` |
| `Not started` | `draft` |
| anything indicating active work-in-progress, if found (e.g. "In progress") | `in_review` |

The parenthetical qualifiers on `Completed` (audit-verified, remediated-by, fix branch)
are traceability detail worth keeping — do not discard them: fold the qualifier into the
body (e.g. as a line under a `## Migration Note` or keep the existing "Audit verdict"
section verbatim) or into a tag (e.g. `tag: audit-verified`), rather than only keeping
`status: approved` and losing the nuance.

If you encounter a status value not covered by this table, **stop and ask** rather than
guessing a mapping.

### 3.3 `tags` — preserve information that has no frontmatter field of its own

MedTrace's frontmatter has no `Phase` field. To avoid silently dropping that grouping
information when tasks are flattened out of their `phase-N-*/` subfolders, add a tag
per task, e.g.:

```yaml
tags: ["phase:0-foundation"]
```

derived from the task's `**Phase:**` line and/or its parent folder name. Similarly, if a
requirement's Version History shows it was split from another (e.g. "split from combined
SR-025"), add a tag such as `tag: "split-from:SR-025"` so that provenance survives even
though MedTrace has no dedicated field for it — do not just drop this note.

### 3.4 `links` — extracting structured links from labeled prose

Only promote a reference to a `links` entry when it unambiguously names an **element
ID that will exist after migration**. Never invent a link from vague prose (e.g. a
"Control Measures" bullet that only says "software requirements traced to this need" with
no ID) — leave that as plain body text.

Apply these mappings:

| Source marker | Found in | → `relation` |
|---|---|---|
| `## Origin Requirement` / "Derived from: User Need UN-x, ..., NFR-y" | Software Requirements | `derives_from`, one link per ID named |
| `- **Implements:** SR-a, SR-b, §07 (Deployment View)` | Tasks | `implements`, one link per **element ID** named. `§07 (Deployment View)` is a reference to an arc42 design section, not an element ID — do **not** turn it into a link (there is no such element and inventing an `architecture-doc` to match it is a content decision, not a format migration — see §3.7). Keep the section reference as plain text in the body (e.g. leave the existing sentence intact, or move it to a short "References" line) so the citation isn't lost. |
| `- **Depends on:** TASK-x (must be merged first)` | Tasks | There is no `depends_on` relation in MedTrace. Use `relates_to` as the closest fit, and keep the qualifier ("must be merged first", "the counter is incremented/reset there", etc.) in the body — do not compress it into just the bare link. Flag this mapping choice in your migration report (§5) since it's a judgment call, not a spec-given equivalence. |
| `- **Depends on:** **all** prior tasks` (seen on at least one aggregation/summary task) | Tasks | Do not attempt to enumerate "all prior tasks" as individual links — that is not a real traceability claim about specific IDs. Leave it as body prose and note it in your migration report as intentionally not linked. |

Every `target` ID referenced this way must be a real element that exists (or will exist)
in the migrated set. If a referenced ID doesn't correspond to any file you're migrating
(e.g. a typo, or an ID from a part of the project not covered by this pass), still emit
the link — MedTrace will surface it as a "broken link" finding for a human to resolve,
which is the intended, visible way to surface this rather than silently dropping it.

### 3.5 IDs with a letter suffix (e.g. `TASK-004a`, `TASK-024a`, `TASK-086a`) — not valid MedTrace IDs

This repository has ~24 "remediation" tasks named `TASK-###a` (occasionally the base
letter appears mid-sequence, e.g. `TASK-066a`, `TASK-066b`). MedTrace's ID pattern
requires digits only after the prefix, so `TASK-004a` cannot be used as-is. Two
compliant options — **pick one and apply it consistently across all lettered IDs**,
stating your choice in the migration report:

- **(Recommended) Fold into the parent task.** Append the lettered file's content into
  the parent task's body (e.g. under a `## Remediation (originally TASK-004a)`
  subsection), then delete the lettered file. This preserves the "004a is a
  correction of 004" relationship without inventing a new ID scheme. Simple, and
  matches how the parent task's own "Audit verdict" section already references the
  remediation task by name.
- **(Alternative) Give it its own sequential ID.** Assign the next free number in that
  prefix's overall sequence (not reusing "004" with a suffix) and link it back to the
  parent with a `relates_to` link, tagging it (e.g. `tag: "remediation-of:TASK-004"`)
  so the relationship isn't lost. Use this option if you'd rather keep remediation
  work as separately trackable/verifiable elements (e.g. because some have their own
  "Audit verdict" and Definition of Done distinct from the parent's).

Either way, do not leave a `TASK-004a.md` file with an invalid ID in the migrated output.

### 3.6 Requirement types with no source-side equivalent — do not reclassify automatically

This repository has no `design-inputs/regulatory-requirements/`-style folder — all
compliance-driven requirements (e.g. `NFR-004` "GDPR compliance") live under
`non-functional-requirements/` as NFRs. MedTrace has a distinct `regulatory-requirement`
type (`RR-###`) for exactly this kind of content. **Do not** silently move `NFR-004` (or
any other NFR) into `regulatory-requirement` during this pass — changing an element's
type also changes its ID prefix and folder, which would break any existing cross-
reference to `NFR-004` elsewhere in the corpus (including ones you haven't seen yet).
Migrate it as `nfr` exactly as it is today. If the user later wants a subset of NFRs
reclassified as regulatory requirements, that is a separate, deliberate follow-up pass —
raise it as an open question in your migration report, don't decide it here.

### 3.7 Element types with no source-side content at all — leave the folders empty

This repository has no standalone `Risk`, `Architecture/Design Document`,
`Test Specification`, `Test Plan`, or `Test Report` elements as MedTrace defines them:

- **Risk.** Every requirement embeds its own `## Risk Analysis` (Rationale / Potential
  Risks / Control Measures) as prose. **Do not** auto-extract these into standalone
  `RISK-###` elements — deciding the right granularity (one Risk per bullet? per
  requirement? per hazard category?) is a content-design judgment call, not a format
  conversion, and doing it silently would invent a risk taxonomy no one has reviewed.
  Keep the `## Risk Analysis` section exactly as-is inside each requirement's body.
- **Architecture/Design Document.** This repository already documents architecture via
  `docs/design/*.md` (arc42-style narrative sections), `docs/design/adr/*.md` (ADRs),
  and `docs/specifications/*.md` (API design, FHIR mapping, PlantUML diagrams). None of
  these are per-item element files with the required frontmatter, and none should be
  forced into that shape just to populate `design-outputs/architecture/` — leave them
  where they are as narrative reference documents (this mirrors how MedTrace's own
  project keeps its own arc42 docs in `docs/design/*.md` outside the element taxonomy,
  referencing them from element bodies as plain Markdown links instead of turning each
  section into an `ADD-###` element).
- **Test Specification / Test Plan / Test Report.** Tasks carry an inline `## Tests`
  section and, on completed tasks, an `## Audit verdict`, but there is no separate,
  reviewable Test Specification or Test Report record. Leave these three folders present
  but empty after migration; do not fabricate `TS-###`/`TP-###`/`TR-###` elements from
  task subsections.

Note in your migration report that these five folders will exist (per §1.1) but contain
zero elements, and that populating them is future design work, not part of this
migration.

### 3.8 Fields with no source equivalent — `author`, `created`, `updated`

None of the sampled files record an author or a creation date. Before writing any files,
**ask the user** (don't assume):

1. What `author` value to use for every migrated element (a real name, or a neutral
   value like `"Migration"` if the original author is unrecorded/unknown).
2. Whether `created`/`updated` should both be set to today's migration date (simplest,
   recommended default — subsequent edits will naturally update `updated` going
   forward), or whether they should be backfilled from this repository's own Git
   history per file, e.g.:
   ```bash
   # first commit date that touched the file (best-effort "created")
   git log --follow --format=%ad --date=short -- <path> | tail -1
   # most recent commit date (best-effort "updated")
   git log -1 --format=%ad --date=short -- <path>
   ```
   This is more historically accurate but slower and file-by-file; only do it if asked.

## 4. Execution plan

1. **Inventory.** Enumerate every source file per category and produce counts (user
   needs, NFRs, software requirements, tasks including lettered ones). Confirm the counts
   against what's expected (e.g. `ls docs/design-inputs/user-needs | wc -l`).
2. **Ask the clarifying questions from §3.8**, and confirm your chosen approach for
   §3.5 (lettered task IDs) and the `depends_on` → `relates_to` mapping in §3.4, before
   writing any files. State your assumptions explicitly if the user has no strong
   preference, per usual practice — don't silently pick one, don't block indefinitely
   either; propose the recommended default and proceed unless corrected.
3. **Convert requirements** (`user-need`, `nfr`, `software-requirement`): for each file,
   parse the sections described in §2.1, build frontmatter per §1.2 using the mapping
   rules in §3, and keep `Summary`, `Description`, `Acceptance Criteria`, `Risk Analysis`
   as the body (drop the now-redundant `# <ID> <Title>` H1, `## Status`, and
   `## Version History` headings from the body since those are now frontmatter fields —
   but if `Version History` has more than one line, i.e. the element was revised, keep
   the full history as a short body section, e.g. `## Revision History`, since
   frontmatter `version` can only hold the *current* version number, not the whole log).
4. **Convert tasks**: for each file (including lettered ones, resolved per §3.5), build
   frontmatter per §1.2, moving `Implements`/`Depends on` into `links` (§3.4) and `Phase`
   into `tags` (§3.3), and keep `Objective`, `Interfaces to honor`, `Implementation
   detail`, `Tests`, `Acceptance criteria`, `Definition of Done`, and `Audit verdict` (if
   present) as the body.
5. **Do not touch** `TASK-TEMPLATE.md`, `AUDIT-FINDINGS.md`, `AUDIT-LEDGER.md`,
   `SMOKE-RESULTS.md`, `implementation-plan/README.md`, or anything under
   `docs/design/`, `docs/design/adr/`, `docs/specifications/` (per §3.7).
6. **Create the remaining required folders** even though empty:
   `design-inputs/system-requirements/regulatory/`, `design-outputs/architecture/`,
   `design-outputs/tests-specifications/`, `risks/`, `test-plans-reports/plans/`,
   `test-plans-reports/reports/`, `source-links/`, `reports/`.
7. **Verify.**
   - Every migrated file must be valid per §1.2 — spot-check a sample by hand against
     the rules (mandatory fields present, enum values exact, ID pattern, folder match).
   - Open the resulting folder in MedTrace (or point `MEDTRACE_PROJECT` at it if running
     from source) and confirm **zero invalid files** are reported.
   - Run MedTrace's Verification view and review the findings — expect some
     `unverified_requirement` and similar findings given §3.7 (no test specs/reports
     exist yet); that's expected, not a migration bug. Broken-link findings, however,
     should be reviewed one by one: each should trace to either a real gap worth fixing
     later, or a mapping decision made in §3.4/§3.6 that's worth double-checking.
8. **Report.** Produce a short migration report covering: final counts per type, the
   decisions made for §3.5/§3.6/§3.8, every link that could not be resolved to an
   existing ID (and why), and the list of items explicitly left for later (regulatory
   reclassification, risk extraction, architecture/test-spec/test-plan/test-report
   population).

## 5. Ground rules while executing this

- State assumptions explicitly rather than guessing silently, especially for §3.2 status
  mapping edge cases, §3.5 lettered IDs, and §3.6/§3.7 type boundaries.
- Do not invent element content (no new Risks, no new Architecture Documents, no new
  Test Specifications) — this is a structural migration of what already exists, not a
  content-authoring pass.
- Do not lose information that has no frontmatter home (phase, split-from notes, audit
  qualifiers, section references like `§07`) — park it in the body or in `tags` rather
  than dropping it.
- Prefer a dry run over a small batch (e.g. the 4 sample files already reviewed) before
  running the full conversion across all ~150+ files, so the mapping can be corrected
  cheaply if something's off.
