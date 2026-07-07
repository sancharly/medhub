---
name: design-record-structure
description: Structural rules for IEC 62304 design records managed as Markdown+frontmatter files (MedTrace-compatible) — folder taxonomy, ID generation, frontmatter schema, naming, and linking. Use whenever creating, migrating, or organizing design elements (User Needs, Requirements, Architecture Docs, Tasks, Risks, Test Specs/Plans/Reports) in a project, so files are valid and traceable without manual fixup. Not for writing requirement *content* quality — see requirements-writer for that.
---

# Design Record Structure

Rules for organizing design elements as one Markdown file per item, each valid without
manual correction. Applies to new elements and to migrating existing docs into this
structure.

## Element types, folders, ID prefixes

| `type` | Folder | Prefix |
|---|---|---|
| `user-need` | `docs/design-inputs/user-needs/` | `UN` |
| `nfr` | `docs/design-inputs/system-requirements/non-functional/` | `NFR` |
| `regulatory-requirement` | `docs/design-inputs/system-requirements/regulatory/` | `RR` |
| `software-requirement` | `docs/design-inputs/software-requirements/` | `SR` |
| `architecture-doc` | `docs/design-outputs/architecture/` | `ADD` |
| `task` | `docs/design-outputs/tasks/` | `TASK` |
| `test-specification` | `docs/design-outputs/tests-specifications/` | `TS` |
| `risk` | `docs/risks/` | `RISK` |
| `test-plan` | `docs/test-plans-reports/plans/` | `TP` |
| `test-report` | `docs/test-plans-reports/reports/` | `TR` |

Two non-element folders: `docs/source-links/` (plain reference files, not scanned) and
`docs/reports/` (generated evidence). Optional `docs/templates/<type>.md` supplies default body
content for new elements of that type.

## ID rule

`<PREFIX>-<###>` (digits only, zero-padded to at least 3, e.g. `SR-014`). Sequential per
prefix, gap-free is not required (skip numbers already used by any existing file — never
reuse or renumber). **No letter suffixes** (`TASK-004a` is invalid — see Migrating below).
IDs are permanent: never change or reuse one after creation, even if the element is
retired (use `status: obsolete` instead of deleting/renumbering).

## Filenames

`<ID>-<slug>.md`, slug = lowercased title, non-alphanumerics → hyphens, ~6 words max.
Filenames are cosmetic — elements are identified by frontmatter `id`, never by filename —
but keep this convention for consistency and readability.

## Frontmatter schema

Exact field order, every field mandatory except `tags`:

```yaml
---
id: "SR-014"
type: software-requirement
title: "Short descriptive title, no ID prefix inside it"
status: draft
version: "1.0"
author: "Full name"
created: "2026-01-01"
updated: "2026-01-01"
links:
  - target: "UN-002"
    relation: satisfies
tags: []
---

(Markdown body)
```

- `type` — exact string from the table above.
- `status` — exactly one of `draft`, `in_review`, `approved`, `obsolete`. No synonyms
  (not `Approved`, `Completed`, `In Progress`, etc.) — map any source vocabulary onto
  these four before writing.
- `version` — string, quote it (`"1.0"`) so YAML doesn't coerce it to a number.
- `created`/`updated` — ISO 8601 `YYYY-MM-DD`. New element: both = today. Edit: bump
  `updated` only, never touch `created`.
- `links` — always an array, `[]` when empty, never omitted. Each entry: `target` (an
  element ID) + `relation`, one of `satisfies`, `derives_from`, `implements`, `verifies`,
  `mitigates`, `relates_to`. Only emit a link when the target is an actual element ID —
  never invent a link from vague prose, and never point a link at a section reference,
  a spec ID, or free text that isn't an element.
- `tags` — array of strings. Use for information that has no dedicated field but
  shouldn't be lost (e.g. originating spec ID `spec:CRUD-01`, product goal `goal:G3`,
  a project phase/grouping, provenance like `split-from:SR-025`).
- `id` prefix must match `type`, and the file must live in that type's folder.

## Typical link patterns

- User Need / NFR / Regulatory Requirement might not have any upstream links (they are the top of the traceability tree), but they should have downstream links to the Software Requirements that satisfy them.
- NFR / Regulatory Requirement → `derives_from` → User Need.
- Software Requirement → `satisfies` → User Need / NFR / Regulatory Req.
- Task / Architecture Doc → `implements` → Software Requirement.
- Test Specification / Test Report → `verifies` → Software Requirement (chain should
  reach a `test-report` eventually, or it shows as unverified).
- Software Requirement → `mitigates` → Risk.
- Anything else (dependency ordering, general association) → `relates_to`. There is no
  `depends_on` relation — use `relates_to` and keep the reason in the body.

  ### Required links to enforce traceability

  - Software Requirements must have at least one `satisfies` link to a User Need, NFR, or Regulatory Requirement.
  - Tasks must have at least one `implements` link to a Software Requirement.
  - Test Specifications must have at least one `verifies` link to a Software Requirement.
  - Architecture Docs must have at least one `implements` link to a Software Requirement.

## Creating a new element (agent checklist)

1. Pick the correct `type` and folder.
2. Generate the next free ID for that prefix (scan existing files, don't guess a number).
3. Fill frontmatter: `status: draft`, `version: "1.0"`, `created = updated = today`,
   `author` = current user/config, `links: []` unless known at creation, `tags: []`
   unless applicable.
4. Body: use `templates/<type>.md` as the starting content if one exists for that type;
   otherwise a minimal placeholder is fine — content quality is out of scope here (see
   requirements-writer).
5. Never touch `id`, `type`, or `created` after creation.

## Migrating existing docs into this structure

1. Extract every metadata-like field embedded in prose (status, "implements"/"depends
   on"/"derives from" markers, version, phase, dates) into frontmatter/tags — don't
   leave them duplicated in the body once promoted, except multi-entry histories (e.g.
   a version history log) that don't fit a single `version` field: keep those as a short
   body section.
2. Map free-text status vocabulary onto the four-value enum; if a value doesn't map
   cleanly, ask rather than guess.
3. IDs with letter suffixes (`TASK-004a`): either fold into the parent element's body as
   a subsection, or assign a new sequential ID and link back with `relates_to` — don't
   leave an invalid ID in place.
4. Don't invent elements the source doesn't have (e.g. don't extract inline risk
   analysis into standalone `risk` elements, don't turn narrative architecture docs into
   `architecture-doc` elements) — that's a content decision for a human, not a structural
   migration step.
5. Don't reclassify an element's `type` (e.g. NFR → regulatory-requirement) without
   confirming — it changes the ID prefix and breaks existing references to it.
6. After migrating, verify: every file's `type`/folder/ID-prefix match, every mandatory
   field is present, every `links[].relation` is one of the six values, and no link
   target is a non-ID reference.
