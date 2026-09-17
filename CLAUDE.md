# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## Project configuration

sdlc-extensions:
  - medical-records:iec62304-sdlc
software-safety-class: B
docs-root: docs/
arc42-root: docs/design/
arc42-sections: 1-8, 10-12

Agents and skills come from the [agentic-os](https://github.com/sancharly/agentic-os) plugins
(`core-engineering`, `medical-records`, `web-fullstack`, `design-studio`), enabled in
`.claude/settings.json`. Never hand-edit an installed plugin copy — change it in agentic-os,
bump the bundle version and reinstall. `/ship-feature` drives the pipeline; the
`medical-records:iec62304-sdlc` overlay above turns on the IEC 62304 stages, records and gates.

Notes on the settings above:

- **arc42 section 9** (architecture decisions) is the ADR log in `docs/design/adr/`, which is
  why it is excluded from `arc42-sections`. Sections 1-8 and 10-12 use the canonical filenames.
- **`docs/medtrace.yml`** mirrors `software-safety-class` for the MedTrace desktop app. The two
  must stay in sync: change both or neither.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```bash
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Backend/Frontend Contract

**The OpenAPI schema is the source of truth. Never hand-write types.**

When changing a backend Pydantic schema:

1. Edit the schema in `backend/app/api/schemas/` (or the relevant router)
2. Regenerate the schema: `cd backend && uv run python -m app.export_openapi --output openapi/openapi.json`
3. Regenerate frontend types: `cd frontend && npm run generate:types`
4. Fix any TypeScript errors that surface — they are real contract violations
5. Commit `backend/openapi/openapi.json` and `frontend/src/api/generated/openapi.ts` alongside the backend change

**Import types from `frontend/src/api/generated/types.ts`** (named aliases), not from `openapi.ts` directly. Never hand-edit either generated file.

CI enforces this: the `openapi-lint` job regenerates `openapi.ts` after exporting the schema and fails if the committed file differs.

**UserType enum values are uppercase**: `"PATIENT"`, `"DOCTOR"`, `"ADMIN"`, `"SYSADMIN"`. Use these constants everywhere in the frontend.

## 6. graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
