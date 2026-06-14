# Requirements Template

Use this template for each requirement document. Save as `requirement-[ID].md`:

```markdown
# [Requirement ID and Title]

## Summary
[One-sentence essential statement of what is required. Concise and unambiguous.]

## Description
[Detailed explanation of the requirement. Include context, scope, and what specifically must be delivered. For Software Requirements, explain how this requirement helps satisfy the User Need or Non-Functional Requirement it's derived from.]

## Acceptance Criteria
[List of measurable, objective conditions that must be true for this requirement to be considered complete. Each criterion should be independently verifiable through testing or review. Use numbered or bulleted list format.]

## Origin Requirement
[For Software Requirements only. Reference the User Need or Non-Functional Requirement this decomposes from, including its ID and title. Example: "Derived from: User Need UN-001 'Patient data accessibility' and Non-Functional Requirement NFR-003 'System Performance'".]

## Risk Analysis

### Rationale
[Explain why this requirement exists and what problem or goal it addresses. Reference regulatory drivers, user feedback, or business objectives.]

### Potential Risks
[Identify risks that could arise if this requirement is not properly implemented or if it introduces new system vulnerabilities. Consider:
- Security risks (unauthorized access, data exposure)
- Safety risks (incorrect behavior causing harm)
- Compliance risks (violation of regulations)
- Operational risks (system unavailability, data loss)
- User risks (usability issues, workflow disruption)]

### Control Measures
[Describe how these risks will be mitigated. Include testing strategies, design controls, operational procedures, or monitoring mechanisms. Reference related requirements that provide complementary controls.]

## Status
[Draft / Approved / Implemented / Retired]

## Version History
[Version 1.0 - Initial creation]
```
