---
name: arc42
user-invocable: true
description: "Guidelines for architecture and design documentation following Arc42 framework. When creating diagrams, coordinate with the plantuml skill to ensure diagrams follow both Arc42 architectural principles AND PlantUML formatting rules."
arguments: [module, branch]
---

# arc42 Documentation Generation Skill

## Purpose

- Produce architecture documentation drafts and scaffolds that follow the arc42 template (overview, constraints, context, solution strategy, building blocks, runtime, cross-cutting).
- Generate diagrams, checklists, and Markdown-ready artifacts to accelerate architecture docs for repositories and teams.

## Scope

- Workspace-scoped skill intended for creating or improving architecture documentation using arc42 as the canonical structure.
- Not a replacement for architecture review; intended to produce high-quality drafts, diagrams, and actionable checklists for review.

## When to use

- The project needs a new architecture document or an update to an existing one following arc42.
- The user wants structured sections, links to diagrams, or checklist-driven completeness checks.

## Workflow (step-by-step)

1. Inspect $module repository for existing docs, diagrams, and code structure (packages, modules, entry points).
2. Analyze the code base or $branch modifications, if $branch is provided, to extract architectural insights, design decisions, and relevant information for each arc42 section.
3. Build a draft for arc42 sections using available inputs and sensible defaults:
   1. Introduction and goals: Short description of the requirements, driving forces, extract (or abstract) of requirements. Top three (max five) quality goals for the architecture which have highest priority for the major stakeholders. A table of important stakeholders with their expectation regarding architecture. Use the template in [01-introduction-and-goals](./assets/01-introduction-and-goals.md) for structure and content guidance.
   2. Architecture constraints: Anything that constrains teams in design and implementation decisions or decision about related processes. Can sometimes go beyond individual systems and are valid for whole organizations and companies. Examples include: technology choices, regulatory requirements, organizational policies, team skills and experience, budget and timeline constraints, and existing infrastructure. Constraints can be hard (non-negotiable) or soft (negotiable with trade-offs). They should be clearly documented and communicated to all stakeholders to ensure informed decision-making throughout the project lifecycle. Use the template in [02-architecture-constraints](./assets/02-architecture-constraints.md) for structure and content guidance.
   3. Context and scope: Delimits your system from its (external) communication partners (neighboring systems and users). Specifies the external interfaces. Shown from a business/domain perspective (always) or a technical perspective (optional). Suggested diagrams: context diagram, system boundary diagram, and interface overview. Use the template in [03-context-and-scope](./assets/03-context-and-scope.md) for structure and content guidance.
   4. Solution strategy: Summary of the fundamental decisions and solution strategies that shape the architecture. Can include technology, top-level decomposition, approaches to achieve top quality goals and relevant organizational decisions.
   5. Building block view: Static decomposition of the system, abstractions of source-code, shown as hierarchy of white boxes (containing black boxes), up to the appropriate level of detail. Suggested diagrams: component diagram, module diagram, and package diagram
   6. Runtime view (scenarios):  Behavior of building blocks as scenarios, covering important use cases or features, interactions at critical external interfaces, operation and administration plus error and exception behavior. Suggested diagrams: sequence diagram, communication diagram, and activity diagram.
   7. Cross-cutting concepts: Overall, principal regulations and solution approaches relevant in multiple parts (→ cross-cutting) of the system. Concepts are often related to multiple building blocks. Include different topics like domain models, architecture patterns and -styles, rules for using specific technology and implementation rules.
4. Generate diagrams and insert embedding snippets.
5. Run a lightweight completeness check against arc42 checklist and flag missing or low-confidence sections.
6. Produce a final Markdown. Each section in a dedicated file (e.g., `doc/design/01-introduction-and-goals.md`) with the following structure in the module's root folder:
```
doc/
  design/
    01-introduction-and-goals.md
    02-architecture-constraints.md
    03-context-and-scope.md
    04-solution-strategy.md
    05-building-blocks.md
    06-runtime-views.md
    07-cross-cutting-concepts.md
```

## Guidelines & best practices
- Prefer conservative defaults: produce concise text and TODOs where repository-specific details are missing.
- For runtime views, prioritize critical scenarios that illustrate key interactions, error handling, and operational aspects.
- If a template is available for a section, use it to ensure consistent structure and coverage.
- When creating architecture diagrams:
  1. First consult the PlantUML skill for all diagram syntax and formatting rules
  2. Follow PlantUML best practices from that skill
  3. Then apply Arc42 architecture principles on top
- DO NOT generate diagrams without consulting the PlantUML skill first.



## Common pitfalls & mitigation

- Overly verbose first drafts: offer executive summary and a detailed appendix.
- Missing inputs (e.g., non-obvious runtime scenarios): add clear TODOs and example prompts to elicit missing info.

## Quality criteria / Completion checks

- Each arc42 section is present with at least a short, meaningful paragraph or a TODO indicating needed inputs.
- Each critical architectural aspect (security, scalability, resilience, operability) has at least one addressed point or an explicit gap note.
- Direct references to files and symbols in the repo (relative paths).
- Include at least two design decisions (ADRs) for detailed mode when required.
- Reasonable length: enough to cover the architecture and design without being exhaustive.
- Prefer diagrams and tables to explain complex concepts and relationships.
- Diagrams are generated using PlantUML and embedded in Markdown with proper syntax.
- Check for consistency across sections (e.g., same terminology, aligned decisions).
- Flag any section that relies heavily on assumptions or lacks confidence due to missing information.

## Examples (prompts to try)
- "Generate an architecture documentation for VolumesModule
- "Review the changes in the branch feature/volume-management of module Utils and update the architecture documentation accordingly."