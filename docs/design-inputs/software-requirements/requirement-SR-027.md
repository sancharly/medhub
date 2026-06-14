# SR-027 Usability controls

## Summary

The system shall provide consistent navigation, confirmation of destructive actions, and clear error messaging so that each user type can complete its core tasks with minimal training.

## Description

This requirement implements the usability NFR through concrete controls. Navigation and terminology are consistent across modules; destructive or safety-relevant actions require explicit confirmation; failures and invalid inputs produce clear, actionable messages. These controls make core tasks learnable and reduce user error.

## Acceptance Criteria

1. Navigation structure and terminology are consistent across screens and modules.
2. Destructive or safety-relevant actions (e.g., revoking access, deleting data) require an explicit confirmation step before execution.
3. When an operation fails or input is invalid, the system shows a clear, actionable message identifying the problem.
4. In usability evaluation, each user type can complete its primary core task using only on-screen guidance.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-009 "Usability".

## Risk Analysis

### Rationale

Usability controls reduce user error and support safe operation, consistent with medical-device usability expectations.

### Potential Risks

- Safety risk: unconfirmed destructive actions could cause unintended data loss or access change.
- User risk: unclear errors lead to confusion or unsafe workarounds.

### Control Measures

- Apply consistent UI patterns, confirmation dialogs, and clear error messages; verify through usability review and system testing.
- Confirmation requirement supports SR-008 (revoke) and SR-024 (erasure).

## Status

Approved

## Version History

Version 1.0 - Initial creation
