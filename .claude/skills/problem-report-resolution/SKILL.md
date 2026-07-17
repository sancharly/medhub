---
name: problem-report-resolution
description: Investigate, fix, and document a bug or defect in this codebase as an IEC 62304 Problem Report (PRB) design record — root-cause investigation, safety evaluation, the code fix, and correctly linking the resolving Change Request (CR). Use this whenever the user reports a bug, asks to "investigate and resolve" or "fix" a problem report (PRB-*), describes something broken/incorrect in the app and wants it tracked for compliance, or asks how to document a defect under IEC 62304 §9. Also use it if you discover a bug yourself while doing other work in this project and the user wants it formally tracked, not just silently patched. Not for writing brand-new requirements or architecture docs — see design-record-structure for the general element mechanics (ID/frontmatter/folder rules) this skill builds on.
---

# Problem Report Resolution

MedTrace tracks bugs as `problem-report` (PRB) elements and their fixes as
`change-request` (CR) elements, per IEC 62304 §9 (Problem Resolution Process).
This skill covers the whole loop: find or create the PRB, actually diagnose and
fix the bug, then document it so the project's own traceability checks pass —
not just so the prose reads well.

Read [design-record-structure](../design-record-structure/SKILL.md) first for
the generic mechanics (ID generation, frontmatter field order, folder rules).
This skill only covers what's specific to problem reports and change requests.

## The record types

| | Folder | Prefix | Statuses |
|---|---|---|---|
| `problem-report` | `docs/problem-reports/` | `PRB` | `open` → `investigating` → `resolved` → `closed` (or `rejected`) |
| `change-request` | `docs/change-requests/` | `CR` | `open` → `in_progress` → `closed` (or `rejected`) |

A PRB's extra required field is `criticality`: `minor` / `major` / `critical`.
This isn't decorative — a `release` element that ships while a `critical` PRB
created before it is still open blocks the project's own release checks. Set
it honestly from actual impact, not from how embarrassing the bug is.

## The one thing that's easy to get backwards: link direction

The `resolves` relation always lives on the **Change Request**, pointing at
the **Problem Report**:

```yaml
# CR-00X frontmatter
links:
  - target: PRB-00Y
    relation: resolves
```

Not the reverse. The PRB's own `links` array is usually `[]` — it's the CR
that claims "I resolve this problem," not the problem that claims to resolve
itself. This matches how the project's own compliance check works
(`src/main/services/trace.ts`, rule SR-041.3): a PRB with status `resolved` or
`closed` needs an *incoming* link with relation `resolves`, which only exists
if the CR was written with the link on its side. Put the link on the PRB
instead and the traceability report will still show it as unresolved — the
fix is real, but the paper trail is invisible to the compliance tooling and
`docs/reports/gap-report-*.md` will keep flagging it every time it's
regenerated.

Before marking a PRB `resolved` or `closed`, actually open the CR file and
confirm the `resolves` link is there — don't assume you wrote it correctly
just because you mentioned the CR ID somewhere in prose.

## Workflow

### 1. Find or create the PRB

Check `docs/problem-reports/` for an existing PRB describing this bug before
creating a new one. If none exists, create it following
design-record-structure's element-creation checklist: next free `PRB-###`,
`status: open`, `criticality` set from your best read of impact so far (you
can revise it after investigating).

### 2. Investigate — find the actual mechanism, not just the symptom

Optionally move `status: investigating` while you work if the diagnosis will
take a while; for a quick bug this step can be skipped and you can go
straight to `resolved` once done.

Read the relevant code rather than guessing. "The button doesn't work" is a
symptom; the `## Investigation` section (IEC 62304 §9.2 — cause analysis)
should name the actual mechanism: which function, which assumption broke,
why. Cite file paths and line numbers so the reasoning is checkable later.
If you can't find the root cause, say so explicitly rather than describing
only what you observed — a vague investigation section is worse than an
honest "still narrowing this down."

### 3. Safety evaluation — reason about it, don't rubber-stamp it

`## Safety evaluation` (§9.3) asks two things: is this relevant to safety,
and does it warrant notifying affected parties? Actually think about what the
bug touches — does it affect data integrity, a safety-related function, a
clinical decision, or is it purely cosmetic/tooling? Justify the criticality
you set (or revise it now that you understand the bug better) rather than
just restating "minor" without reasoning. If the bug could plausibly affect a
released version already in use, say so — that's what triggers the
notification question, not the severity label alone.

### 4. Fix it

Implement the smallest correct fix for the diagnosed root cause — this
project's own conventions (see the root `CLAUDE.md`) favor surgical, minimal
changes over opportunistic refactors. Then verify it actually works: run the
relevant tests/typecheck, and if it's UI-visible, exercise it (e.g. via the
preview tools) rather than trusting the diff by eye. A Resolution section
describing a fix you haven't verified is a bigger liability than an
unresolved PRB — it tells an auditor the problem was closed out when it may
not have been.

### 5. Document the Resolution

`## Resolution` should say what changed (with file references), why that
approach, and how you verified it — concretely enough that someone could
reproduce the verification later. Replace the template placeholder text
(`"How the problem is resolved; link the resolving change request..."`)
entirely; don't leave it sitting above or below your actual content.

### 6. Write or update the resolving Change Request

Check whether an open CR already covers this problem (the project sometimes
bundles several related problem reports under one CR) before creating a new
one — add this PRB to its `links` with `relation: resolves` rather than
spinning up a duplicate. If none exists, create one: `## Reason` should say
why the change is needed (referencing the PRB in prose is fine, but the
machine-checkable link is what matters — see above), `## Scope` what's
changed, `## Verification approach` how it's/was verified (§8.2.1).

### 7. Close out the PRB

Set `status: resolved` once the fix is implemented and verified in the
working tree, or `closed` if you're confirming it all the way through to a
shipped release. Bump `version` and set `updated` to today per
design-record-structure's editing rules. Leave `rejected` for cases where
investigation concludes it isn't a real bug (duplicate, working as intended,
won't-fix) — the Resolution section should say which and why; the `resolves`
link requirement doesn't apply to `rejected`.

### 8. Self-check before declaring done

- Open the CR and confirm `links` contains `{ target: <this PRB id>,
  relation: resolves }` — this is the step most likely to get skipped.
- If `criticality: critical`, make sure it isn't left open (`open` or
  `investigating`) across a release that was created after it — that's what
  the project's release-safety check looks for.
- If you have a way to run the project's own gap report/traceability
  verification, use it as a final check rather than trusting the prose alone.
