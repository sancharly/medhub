# MedHub Architecture & Design Document (Arc42)

This folder contains the MedHub software architecture and design, following the **Arc42** structure, produced by the Architecture design activity of the software development plan (IEC 62304, NFR-006). It is the primary design output developers implement against.

## Contents

| Section                                         | File                                                             |
|-------------------------------------------------|------------------------------------------------------------------|
| 01 Introduction and Goals                       | [01-introduction-and-goals.md](01-introduction-and-goals.md)     |
| 02 Architecture Constraints                     | [02-architecture-constraints.md](02-architecture-constraints.md) |
| 03 Context and Scope                            | [03-context-and-scope.md](03-context-and-scope.md)               |
| 04 Solution Strategy                            | [04-solution-strategy.md](04-solution-strategy.md)               |
| 05 Building Block View (software items & units) | [05-building-blocks.md](05-building-blocks.md)                   |
| 06 Runtime View                                 | [06-runtime-views.md](06-runtime-views.md)                       |
| 07 Deployment View                              | [07-deployment-view.md](07-deployment-view.md)                   |
| 08 Cross-cutting Concepts                       | [08-cross-cutting-concepts.md](08-cross-cutting-concepts.md)     |
| 09 Architecture Decisions (ADR index)           | [adr/README.md](adr/README.md)                                   |
| 10 Quality Requirements                         | [10-quality-requirements.md](10-quality-requirements.md)         |
| 11 Risks and Technical Debt                     | [11-risks-and-technical-debt.md](11-risks-and-technical-debt.md) |
| 12 Interfaces between software items            | [12-interfaces.md](12-interfaces.md)                             |
| Requirements traceability matrix                | [traceability-matrix.md](traceability-matrix.md)                 |

## Related artifacts

- ADRs: [`adr/`](adr/)
- UML diagrams (PlantUML): [`../specifications/`](../specifications/)
- API & interface design: [`../specifications/api-design.md`](../specifications/api-design.md)
- FHIR mapping: [`../specifications/fhir-mapping.md`](../specifications/fhir-mapping.md)

> Diagrams are authored in PlantUML under `docs/specifications/*.puml` and referenced from the relevant sections.
