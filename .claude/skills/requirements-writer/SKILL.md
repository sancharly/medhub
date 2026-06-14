---
name: requirements-writer
description: Write well-defined product requirements and specifications following medical device regulatory standards. Use this skill whenever you need to create or decompose User Needs, Non-Functional Requirements, or Software Requirements from goals, constraints, user feedback, or other sources. Generates markdown requirement documents with clear acceptance criteria, traceability, and risk analysis suitable for IEC 62304 and FDA compliance in Agile development. Trigger whenever the user asks an agent to write requirements or when requirements creation is needed as part of a workflow.
---

# Requirements Writer Skill

This skill guides the creation of well-defined, testable, and traceable requirements documents following medical device regulatory standards (IEC 62304, FDA) while supporting Agile development cycles.

## Understanding Requirement Types

Requirements exist at three levels, each serving a specific purpose:

### User Needs
**What are they:** Qualitative statements describing a problem, desire, or challenge faced by an end-user (clinician, patient, administrator). They describe what the user must accomplish to achieve their clinical or operational goals within a specific context, *without* dictating technical solutions.

**Characteristics:**
- Focus on the problem or outcome, not the solution
- Written from the user's perspective
- May be expressed in informal language
- Derived from user feedback, interviews, observations, or problem statements

**Example:**
- "A clinician needs to quickly access a patient's complete medical history during an emergency to make informed treatment decisions"
- "A patient wants to understand their treatment plan and expected outcomes"

### Non-Functional Requirements
**What are they:** Statements describing *how* the system performs a task, rather than *what* tasks it performs. They define quality attributes, constraints, and system-wide properties that all or multiple features must satisfy.

**Characteristics:**
- Define system properties: performance, security, usability, reliability, scalability, compliance
- Apply across multiple features or the entire system
- Often impose constraints on implementation
- Critical for medical device compliance and safety

**Examples:**
- "The system shall respond to user actions within 2 seconds under normal load"
- "All patient data shall be encrypted in transit and at rest using AES-256"
- "The system shall be compliant with HIPAA and GDPR regulations"
- "The user interface shall be usable by clinicians with minimal training"

### Software Requirements
**What are they:** Specific, implementable statements that define what the software must do to satisfy User Needs or Non-Functional Requirements. They are derived by decomposing higher-level requirements into concrete, testable features and behaviors.

**Characteristics:**
- Specific and unambiguous
- Testable with clear acceptance criteria
- Traceable to User Needs or Non-Functional Requirements
- Implementable by developers
- Include risk analysis and mitigation strategies

**Examples:**
- "The system shall display the patient's complete medical history in a single view, including diagnoses, medications, allergies, and procedures, within 3 seconds of user request"
- "The authentication system shall enforce password complexity rules (minimum 12 characters, including uppercase, lowercase, numbers, and symbols) and implement account lockout after 5 failed attempts"

## Creating Requirements from Inputs

### Step 1: Analyze Your Inputs

Gather information from available sources:
- **Goals:** What are the business or clinical objectives?
- **Constraints:** What are the limitations (regulatory, technical, resource, timeline)?
- **User feedback:** What problems or features do users request?
- **Problem statements:** What specific issues need solving?
- **Domain context:** What is the clinical or operational environment?

### Step 2: Extract or Create User Needs

For each problem, challenge, or goal identified:

1. **Identify the user role** (clinician, patient, administrator, etc.)
2. **State the problem or goal** they face in their context
3. **Avoid prescribing solutions** — describe the outcome or problem, not how to solve it
4. **Be specific about context** — when, where, and why do they need this?

**Quality checks for User Needs:**
- Does it describe a real user problem or desire?
- Is it free of implementation details or technology assumptions?
- Would a different solution still satisfy this need?
- Is it traceable to user feedback or organizational goals?

### Step 3: Extract or Create Non-Functional Requirements

For each quality attribute, constraint, or system property:

1. **Identify the quality attribute** (performance, security, usability, reliability, compliance, etc.)
2. **Define measurable criteria** where possible (e.g., response time, encryption standard, compliance framework)
3. **Scope the requirement** — does it apply system-wide or to specific features?
4. **Justify from regulatory or business context** — why is this requirement necessary?

**Quality checks for Non-Functional Requirements:**
- Is it measurable or verifiable?
- Does it apply to the system or a specific feature?
- Is it justified by regulatory, business, or user needs?
- Does it conflict with other requirements?

### Step 4: Decompose into Software Requirements

Software Requirements are created by breaking down User Needs and Non-Functional Requirements into specific, implementable features:

1. **Select a User Need or Non-Functional Requirement** to decompose
2. **Identify the specific behavior or feature** needed to satisfy it
3. **Define acceptance criteria** — measurable, testable conditions that prove the requirement is met
4. **Establish traceability** — link back to the User Need or Non-Functional Requirement
5. **Analyze risks** — what could go wrong, and how will you prevent it?

**Decomposition guidance:**
- One User Need may decompose into multiple Software Requirements
- One Non-Functional Requirement may apply to multiple Software Requirements
- Each Software Requirement should be independently testable
- Acceptance criteria should be objective and verifiable

## Markdown Requirement Template

Use the [template](./assets/requirements-template.md) for each requirement document. Save as `requirement-[ID].md`:

## Writing Quality Requirements

### For User Needs — Focus on the Problem or Outcome

✅ **Good:** "A clinician needs to quickly locate a patient's most recent lab results to determine if treatment adjustment is necessary"

❌ **Bad:** "Build a lab results search feature in the dashboard"

**Why:** The good version describes the user's problem and goal. The bad version prescribes a solution.

### For Non-Functional Requirements — Be Measurable and Justified

✅ **Good:** "The system shall encrypt all patient data at rest using AES-256 encryption, as required by HIPAA Security Rule 45 CFR § 164.312(a)(2)(i)"

❌ **Bad:** "The system shall have good security"

**Why:** The good version is measurable, specific, and justified. The bad version is vague and untestable.

### For Software Requirements — Define Clear Acceptance Criteria

✅ **Good:**
- Acceptance Criteria:
  1. When a user clicks "View Lab Results," results load within 3 seconds
  2. Results are sorted by date (most recent first)
  3. Results include test name, value, reference range, and unit
  4. Results are searchable by test name or date range

❌ **Bad:**
- Acceptance Criteria:
  1. Lab results work well

**Why:** The good version is testable and objective. The bad version is vague and cannot be verified.

## Decomposition Example

**User Need (UN-001):**
"A clinician needs to quickly access a patient's complete medication list during clinical encounters to identify potential drug interactions and ensure safe prescribing."

**Related Non-Functional Requirement (NFR-005):**
"The system shall display medication information within 2 seconds of user request under normal load."

**Decomposed Software Requirements:**

**SR-001:** Display active medications
- Acceptance Criteria: System displays all active medications with name, dose, frequency, and start date within 2 seconds

**SR-002:** Search medications by name
- Acceptance Criteria: User can search by partial name and results appear in real-time

**SR-003:** Flag potential interactions
- Acceptance Criteria: System highlights potential drug-drug interactions using a clinical database

Each Software Requirement traces back to UN-001 and NFR-005, has testable acceptance criteria, and includes risk analysis (e.g., risk of missed interactions, mitigation through clinical validation of the interaction database).

## Medical Device Compliance

### IEC 62304 Alignment

This skill follows the IEC 62304 lifecycle processes for medical device software development:

- **Requirements Analysis** — User Needs and Non-Functional Requirements capture system context and intended use
- **Architectural Design** — Software Requirements define the features that implement the architecture
- **Traceability** — Origin fields ensure bidirectional traceability from User Needs → Software Requirements
- **Risk Management** — Risk Analysis sections integrate with hazard and risk assessment

### FDA 21 CFR Part 11

For regulated environments, ensure:
- Requirements are documented and version-controlled (use Status and Version History fields)
- User Needs are traceable to user feedback or regulatory analysis
- Software Requirements have clear acceptance criteria for validation testing
- Risk Analysis documents safety-critical considerations

## Validation Checklist

Before finalizing requirement documents, verify:

### User Needs
- [ ] Written from user perspective (not technical)
- [ ] Describes a real problem or desired outcome
- [ ] Free of solution prescriptions
- [ ] Specific to a user role and context
- [ ] Traceable to feedback or goals

### Non-Functional Requirements
- [ ] Measurable or objectively verifiable
- [ ] Scoped (system-wide or feature-specific)
- [ ] Justified by regulatory, business, or user drivers
- [ ] Does not conflict with other requirements
- [ ] Implementable by the team

### Software Requirements
- [ ] Specific and unambiguous
- [ ] Acceptance criteria are objective and testable
- [ ] Traceable to User Need or Non-Functional Requirement
- [ ] Risk Analysis identifies plausible risks
- [ ] Control Measures are realistic and verifiable
- [ ] No implicit dependencies on unspecified requirements

## When Requirements Are Ready

Requirements are ready for implementation when they:
1. Pass all validation checks
2. Are approved by Product Owner and (if applicable) Regulatory/Quality
3. Have clear acceptance criteria for QA testing
4. Are organized and version-controlled in the project repository
5. Are communicated to development and QA teams
