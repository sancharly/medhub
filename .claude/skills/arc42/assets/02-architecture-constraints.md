# Architecture Constraints

Use this template, adapting content as needed for the specific module

```markdown

# Architecture Constraints

## Technical Constraints

[Table with all the technical constraints for the module. These might include (but not limited to): C++ versions, external libraries dependencies, multi-platform support, and other technical limitations to take into account when developing the module]

| Constraint         | Description                                                                   | Rationale                                                        |
|--------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------|
| **TC-01: Qt 6.5+** | Module requires Qt 6.5 or later with Quick, Qml, and LinguistTools components | QML type registration (QML_ELEMENT) and modern Qt Quick features |

## Organizational Constraints

[Table with all the organizational constraints for the module. These might include (but not limited to): Medical device regulations, folder structure, Code review policies, Code and documentation language]

| Constraint                            | Description                                           | Impact                                            |
|---------------------------------------|-------------------------------------------------------|---------------------------------------------------|
| **OC-01: Medical Device Regulations** | Must comply with MDR (EU) and FDA 510(k) requirements | Extensive documentation, traceability, validation |

## Conventions

[Table with all the conventions to follow when developing this module. These might include (but not limited to): Namespace to use, API exports, patterns used across all the module(s), Style Guide compliance]

| Convention           | Description                                 |
|----------------------|---------------------------------------------|
| **CV-01: Namespace** | All classes reside in `cs::spine` namespace |

## Dependencies

### Internal Dependencies

[Table with all the internal (in-house developed) dependencies and whether they are direct or inherited]

| Module  | Purpose                                               | Type      |
|---------|-------------------------------------------------------|-----------|
| `Math`  | Type definitions, Eigen aliases, geometric primitives | Direct    |
| `Tools` | Entity-component framework, logging, utilities        | Inherited |

### External Dependencies

[Table with all the external (SOUP) dependencies]

| Library | Version | Purpose                                         |
|---------|---------|-------------------------------------------------|
| Qt      | ≥ 6.5   | UI framework, signals/slots, JSON, translations |
```
