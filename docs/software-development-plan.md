# Software Development Plan

## Purpose

The purpose of this document is to define a clear plan to be followed for the development of the Medhub application. It shall define the activities to execute in each phase and the records that these activities should produce to verify that the activities have been properly executed following standard IEC 62304.

## Scope

The scope of this document is the Medhub application and all its related activities that must be followed to create a working product following medical device product standards.

## Product Description

Medhub is a web application that serves as a hub for patients and healthcare providers, centralizing all personal health information (PHI) and medical activities in a single application. The platform allows doctors to upload patient clinical data following medical visits or procedures. Patients can access this information, and it can be shared among different specialists to provide a seamless experience for both patients and healthcare providers. The modular architecture of Medhub allows for new plugins to add functionality, with the goal of becoming the central hub for all clinical activities in a hospital or medical center regardless of specialty.

## Plan

While presented sequentially, phases may be executed iteratively in accordance with Agile principles. Each phase contains distinct activities that must be completed, and the artifacts produced must be properly controlled.

This development plan is a living document that shall be updated and improved as the development process evolves. It shall reflect the current status of the process and activities being followed.

### Planning

The planning phase is critical for the correct execution of the project. The correct execution of its activities and the quality of its outputs will lead to a high-quality product. The primary objective of this phase is to transform user feedback, industry analysis, and application goals into clear architectural and design decisions that can be implemented as a working product.

The activities to execute in this phase are the following.

#### Requirements analysis activity

The Product Owner receives inputs regarding what the application should accomplish from various sources, including user feedback, industry needs, and application [goals](./design-inputs/goals.md). The Product Owner then translates this information into design inputs. The higher-level design inputs are [User Needs](./design-inputs/user-needs.md) and [non-functional requirements](./design-inputs/non-functional-requirements.md).

A **User Need** is a qualitative statement of a problem, desire, or challenge faced by an end-user (e.g., clinician, patient). It describes what the user must accomplish to achieve their clinical goals within a specific context, without dictating the technical software solution.

**Non-functional requirements** describe how the system performs a task, rather than what tasks it performs. They are related to the quality attributes of the system.

After defining these design inputs, they shall be decomposed into [software requirements](./design-inputs/software-requirements.md). The Product Owner shall define these requirements with sufficient detail to enable the Software Architect and Software Developers to implement them into working software. It shall be verified that software requirements:

- Implement user needs and non-functional requirements
- Do not contradict each other
- Are expressed in unambiguous terms
- Are expressed in terms that allow the definition of clear acceptance criteria that can be verified during the testing phase
- Can be uniquely identified
- Are traceable to user needs or non-functional requirements

The outputs of this activity are:

- List of approved user needs: [user-needs.md](./design-inputs/user-needs.md)
- List of approved non-functional requirements: [non-functional-requirements.md](./design-inputs/non-functional-requirements)
- List of approved software requirements: [software-requirements.md](./design-inputs/software-requirements.md)

#### Architecture design activity

In this activity, the Software Architect shall transform the list of approved [software requirements](./design-inputs/software-requirements.md) into software architecture and design decisions. These decisions shall be documented with text and/or diagrams (class, components, activity) with sufficient detail to enable the Software Developer to implement decisions without ambiguity. The software system shall be hierarchically decomposed into software items, which are further decomposed until no further decomposition is possible. These software items define the software units. It shall be verified that the architecture implements all requirements. The outputs of this activity are:

- The architecture and design document following Arc42 guidelines in the [design](./design/) folder
- Any additional design specifications in the [specifications](./specifications/) folder
- UML diagrams in the [specifications](./specifications/) folder that describe and define the system
- The list of software items and software units
- The definition of interfaces between software items

### Implementation

#### Coding activities

The Software Developer shall receive all documents generated during architecture design activities and transform them into working code. Coding best practices and style guides shall be followed to produce high-quality code. Upon completion, the code shall be submitted to the QA Engineer for review. The outputs of this activity are:

- Source code (git repository)
- Configuration files (git repository)
- Build, installation, and deployment instructions in one or more files as appropriate (git repository, README.md, INSTRUCTIONS.md, INSTALL.md, DEPLOY.md)

#### Code Review activities

It shall be verified that all software units are implemented following defined coding standards and best practices. This activity is performed by the QA Engineer, who reviews the code generated by the Software Developer to ensure that coding standards and best practices are followed and to identify any errors or security issues. If the review identifies issues, a report is provided to the Software Developer for correction. This code-review cycle shall be repeated until the QA review identifies no issues. The outputs of this activity are:

- Report detailing all issues identified during review
- Confirmation that the code is ready for integration into the main branch (if no issues were found)

#### Integration activities

It shall be verified that all modified software units are properly integrated and that interfaces conform to their specifications. Integration activities may include compilation and linkage of libraries, definition and implementation of interfaces between software units, and any other activities necessary to ensure correct interaction between units.

### Testing

#### Tests definition activities

Validation of working software is critical to ensure that the code performs as expected. Clear validation criteria shall be established for each requirement, and all requirements shall be verified through testing or other means. Testing shall be performed at three levels:

1. **Unit Testing:** Automated testing of individual software units. All software units shall have unit tests that verify core functionality works as expected. High code coverage is expected to produce high-quality software.
2. **Integration Testing:** Verification that software units are properly integrated together and that interfaces between different units function correctly.
3. **System Testing:** Functional and non-functional tests that verify requirements are met and that the application complies with acceptance criteria. All requirements shall be traced to a system test.

When possible, all tests (unit, integration, and system) shall be automated using the selected testing framework(s) to enable early detection of regression errors during the development phase.

The outputs of this activity are:

- Unit tests definitions. Source code in the Git repository.
- Integration tests definitions. Source code in the Git repository or manual test specification in the [tests folder](../test-specifications).
- System tests definitions. Source code in the Git repository or manual test specification in the [tests folder](../test-specifications).

#### Test execution

All defined tests shall meet the established acceptance criteria before committing new functionality to the main branch. The outputs of this activity include:

- Automated test reports, which may be automatically generated reports, console output with test results, or output from the test stage of a CI server
- Manual test report documenting the results of manual test execution

### Git Flow

The project's code and documentation reside in a git repository. When new functionality is implemented, all activities from planning through testing are performed for that functionality, and all outputs are placed under version control. A Git Flow strategy is employed in which a new branch is created for the complete development cycle of each feature:

1. A new branch is created in the repository with a name following the convention: `feature/feature-description`, `user-story/story-description`, `enabler-story/enabler-description`, or `bug/bug-description`, depending on the implementation type.
2. The complete development cycle is executed, committing all artifacts from each activity (specifications, requirements, source code, test definitions, etc.) to the repository. If testing is managed through an external tool or if automated testing results are stored in a CI server, those test reports need not be committed to the repository.
