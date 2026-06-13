---
name: plantuml
user-invocable: true
description: "Generates PlantUML diagram code following strict formatting and style guidelines. USE THIS SKILL whenever creating ANY kind of diagram in PlantUML format, regardless of context. This includes: architecture diagrams, sequence diagrams, class diagrams, deployment diagrams,flowcharts, or any visual documentation. Trigger this even if the user mentions diagrams casually or if another skill (like Arc42) mentions creating diagrams. Always consult this skill for diagram syntax, styling, and best practices to ensure consistent, professional output."
---


# PlantUML Diagram Generation Skill

## Purpose

- Convert user requirements, code snippets, or textual descriptions into PlantUML source (`.puml` or code snippets).
- Provide editable, minimal PlantUML code that compiles and follows PlantUML best practices.

## Scope

- Workspace-scoped skill intended for generating UML diagrams (sequence, class, component, activity, state, deployment, C4, timing, and composite diagrams) from user input.
- Not responsible for installing or running local PlantUML tooling; it can recommend commands and configuration for local rendering.

## When to use

- The user wants a PlantUML diagram produced from a description, existing code, or markdown section.
- The user needs source (`.puml`) or embedded diagrams for documentation, design discussions, or architecture reviews.

## Decision points

- Input format: natural language description, code, existing UML, or partial PlantUML.
- Output preference: PlantUML source only.
- Level of detail: high-level overview vs. detailed interactions.

## Workflow (step-by-step)

1. Parse the user's request to extract diagram type, participants, relationships, messages, lifelines, classes, attributes, methods, packages, or components.
2. If input is code, perform a lightweight AST-based extraction (class names, methods, fields, packages) or use heuristics for languages not supported.
3. Choose a diagram type; if ambiguous, ask a clarifying question (see Clarifying Questions).
4. Generate concise PlantUML source that compiles. Prefer readable names and grouping (`package`, `namespace`, `frame`) and avoid excessive detail by default.
5. Validate the PlantUML syntax for common mistakes (unbalanced braces, wrong directives, missing `allowmixing`). If errors detected, produce a corrected variant and explain changes.
6. Provide embedding snippets for Markdown, AsciiDoc, or documentation systems used in the repo.

## Mandatory Rules — READ BEFORE STARTING

- Prefer minimal, correct PlantUML first; add styling (`skinparam`) only when requested.
- For code-to-class-diagram extraction, prioritize explicit class names and visible fields/methods; ask before inferring private/internal members.
- Add the following lines at the beginning of the generated PlantUML diagrams to ensure consistent styling:
```
!include cyber.puml
!include sprites/all.sprite
skinparam linetype ortho
```
- Do not use any theme (as !theme plain) in the diagrams, as the included `cyber.puml` file already defines the necessary styles and sprites for a consistent look across all diagrams.
-  Add the tag `#lightgreen` to all components that form part of the Qt library (e.g., `Qt6::Core`, `Qt6::Quick`, etc.) to visually distinguish them from custom components in the diagrams. Allways at the end of the declaration of the component. For example:
```
rectangle "Qt 6" as Qt #lightgreen
```
- Add the tag `#lightgray` to external components that are not part of the Qt library but are relevant to the diagram (e.g., `ITK`, `VTK`, `OpenGL`) to visually distinguish them from both Qt components and custom components. For example:
```
rectangle "ITK" as ITK #lightgray
```
- Add the tag `#lightblue` to external components developed in-house or by partners that are relevant to the diagram (e.g., `Database`, `ProceduresModule`, `SurgeriesModule`) to visually distinguish them from both Qt components and custom components. For example:
```
rectangle "Database" as Database #lightblue
```
- When declaring a class that is part of the Qt library, use QT_NATIVE_CLASS(name, alias) instead of the regular class declaration. For example:
```
QT_NATIVE_CLASS(QObject,QObject)
```
- When declaring a QML component that is part of the Qt library, use QT_NATIVE_QML(name, alias) instead of the regular class declaration. For example:
```
QT_NATIVE_QML(PushButton,PushButton)
```
- When declaring a class that is part of the module, but derives from a Qt class, use QT_CLASS(name, alias) instead of the regular class declaration. For example:
```
QT_CLASS(MyModel,MyModel)
```
- When declaring a C++ class that is part of the module and is exposed to QML using the QML_ELEMENT(name, alias) macro, use QML_ELEMENT instead of the regular component declaration. For example:
```
QML_ELEMENT(MyModel,MyModel)
```
- When declaring a C++ class that is part of the module and is exposed to QML using the QML_ELEMENT(name, alias) macro and is also a QML singleton (QML_SINGLETON macro), use QML_SINGLETON instead of the regular component declaration. For example:
```
QML_SINGLETON(MySingleton,MySingleton)
```
- When declaring a QML component that is part of the module and is a QML file, use QML_FILE instead of the regular component declaration. For example:
```
QML_FILE(MyComponent,MyComponent)
```
- When declaring a C++ class that is part of the module but does not extend a Qt class, use standard class declaration. For example:
```
class MyClass
```
- Always use explicit declaration for components instead of `[]` to ensure clarity and consistency in the diagrams. For example, instead of using `[tools::TasksManager::Task]`, declare it as a class or component with the appropriate name and relationships.
- When declaring relationships between components, use clear and consistent notation to indicate the type of relationship (e.g., association, aggregation, composition, dependency) and the direction of the relationship. For example, use arrows to indicate dependencies and lines to indicate associations.
- When using a macro, if the name has special characters, use an alias that replaces the special characters with underscores to ensure that the macro can be processed correctly and wrap the name in quotes to void rendering errors. For example:
```
QT_CLASS("cs::tools::math::BoundingBox", cs_tools_math_BoundingBox)
```

## Quality criteria / Completion checks

- PlantUML source compiles (no syntax errors) for the declared diagram type.
- The diagram represents the core intent from the user's input (actors, relationships, sequence flow, structure).
- Source is concise and idiomatic (uses PlantUML features like `skinparam`, `package`, `note`, `activate` judiciously).
- If rendering requested, provide a short guide/command to reproduce locally.

## Clarifying questions (ask when input is ambiguous)

- Which diagram type do you prefer (sequence/class/component/activity/state/C4)?

## Common pitfalls & how the skill handles them

- Long auto-generated names: shorten or alias when possible.
- Overly dense diagrams: offer an option to split diagrams into packages or multiple views.
- Private/confidential info: when input contains credentials or secrets, refuse to send to remote renderers and prompt the user to sanitize.

## Examples (prompts to try)

- "Generate a sequence diagram in PlantUML for a user logging into a web app: browser -> front-end -> auth service -> database. Include error path for invalid credentials and a note describing retries. Provide both `.puml` and a PNG render command."
- "From the following Java classes, produce a class diagram: public class Order { List<Item> items; double total(); } public class Item { String name; double price; }"
- "I have an existing PlantUML fragment; optimize it for readability and split it into packages."
