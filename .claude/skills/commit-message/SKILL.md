---
name: commit-message
user-invocable: true
description: "Generates commit messages following strict formatting and style guidelines. USE THIS SKILL whenever creating ANY kind of commit message, regardless of context. This includes: feature commits, bug fixes, refactoring, documentation updates, or any other type of change."
---

# Commit message skill

## Purposes

The purpose of this skill is to ensure that all commit messages are clear, concise, and follow a consistent format. This helps maintain a clean and understandable project history, facilitates code reviews, and improves collaboration among team members.

## When to use

Use this skill whenever you need to generate a commit message for any type of change in the codebase. This includes, but is not limited to:
- Adding new features
- Fixing bugs
- Refactoring code
- Updating documentation

## Mandatory Rules — READ BEFORE STARTING

- ALWAYS use american English for commit messages.
- Use the imperative mood in commit messages (e.g., "Add feature" instead of "Added feature").
- Keep the subject line concise and provide a brief summary of the change.
- Include relevant issue or ticket numbers in the commit message if applicable.
- Avoid vague messages like "fix" or "update". Be specific about what was changed and why.
- Use a consistent format for commit messages across the project to improve readability and maintainability of the project history.
- Use the following format for commit messages: `<type>: <subject>`, where `<subject>` is a brief summary of the change and `<type>` is one of the following: 
  - AI: Any change in [Claude](./claude) or [Github](./github) folders, CLAUDE.md, AGENTS.md, or any other file related to the AI agents and their instructions.
  - ENH: New features or enhancements to existing functionality.
  - FIX: Bug fixes or patches.
  - CI: Changes to continuous integration pipelines, build scripts, or related configuration.
  - DOC: Documentation updates or improvements.
- Many types can be used in the same commit message if the changes are related to multiple types of changes. For example, a commit that adds a new feature and updates documentation could use both `ENH` and `DOC` types in the same message (`ENH, DOC: Add new feature and update documentation`):