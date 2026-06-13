# Software Development Plan

## Purpose

The purpose of this document is to define a clear plan to be followed for the development of the Medhub application. It shall define the activities to execute in each phase and the records that these activities should produce to verify that the activities have been properly executed following standard IEC 62304.

## Scope

The scope of this document is the Medhub application and all its related activities that mus be followed to create a working product following medical devices products standards.

## Product description

Medhub is a web application that offers a hub for patients and doctors that centralize all personal health information (PHI) and all medical activities in one single application. At its base it allows doctors to upload patient clinical data after medical visits or any medical procedure. Patients can access this information and it can be share between different specialists to provide a seamless experience for both patients and users. The modular approach of MedHub allow for new plugins to add new functionality with the goal of becoming the central hub for all the clinical activities in a hospital or medical center regardless of the specialty.

## Plan

This plan is presented as sequential but it does not have to be like this. Agile principles are used for the development of the MedHub application so these phases are executed in a cyclical way. However, each phase have different activities that must be done and the artefact that they produced must be correctly controlled.

This development plan is a live document that can be updated and improved as the development process evolves with time. It should reflect the current status of the process and activities that are followed.

### Planning

The planning phase is critical for the correct execution of the project. The correct execution of its activities and the quality of its outputs will lead to high quality product. This phase main goal is to transform user feedback and industry analysis and the main application goals into clear architectural and design decisions that can be implemented into a working product.

The activities to execute in this phase are tha following.

#### Requirements analysis activity

The Product Owner receives as inputs what the application should do from different sources like user feedback, industry needs or application's [goals](./design-inputs/goals.md). He then translates all this information into different design inputs. The higher level fo the design inputs are [User Needs](./design-inputs/user-needs.md) and [non-functional requirements](./design-inputs/non-functional-requirements.md).

A **User Need** is a qualitative statement of a problem, desire, or challenge faced by an end-user (e.g., clinician, patient). It describes what the user must accomplish to achieve their clinical goals within a specific context, without dictating the technical software solution.

**Non-functional requirements** describe how the system performs a task, rather than what tasks it performs. They are related to the quality attributes of the system.

After the definition of these design inputs, they shall be broken down into [software requirements](./design-inputs/software-requirements.md). The Product Owner shall define these requirements to enough detail so that Software Architect and Software Developers and turn these requirements into working software. It shall be verified that software requirements:

- Implement user needs and non-functional requirements
- They not contradict each other
- Are expressed in terms that avoid ambiguity
- Are expressed in terms that allow the definition of clear acceptance criteria that can be verified in the testing phase
- Can be uniquely identified
- Are traceable to user needs or non-functional requirements.

The outputs of this activity are:

- List of approved user needs: [user-needs.md](./design-inputs/user-needs.md)
- List of approved non-functional requirements: [non-functional-requirements.md](./design-inputs/non-functional-requirements)
- List of approved software requirements: [software-requirements.md](./design-inputs/software-requirements.md)

#### Architecture design activity

In this activity, the Software Architect shall transform the list of approved [software requirements](./design-inputs/software-requirements.md) into software architecture and design decisions. These decisions shall be documented with text and/or diagrams (class/components/activity) with enough detail so that the Software Developer can implement the decision without ambiguity. The software system shall be decomposed into software items. These software items shall be, in turn, decomposed into further software items until it cannot be decomposed into mre software items. These software items define the software units. It shall be verified that the architecture implement all the requirements and the outputs of these activity are:

- The architecture and design document following Arc42 guidelines in the [design](./design/) folder
- Any other design specification in the [specifications](./specifications]) folder
- UML Diagrams that can help to describe and define the system in the [specifications](./specifications]) folder
- The list of software items and software units
- The definition of the interface between software items

### Implementation

#### Coding activities

The Software Developer shall receive as inputs all documents generated in the architecture design activities and transform them into working code. Coding best practices and style guides shall be followed to produce high quality code. When the functionality is completed, it can be handed to the QA Engineer for review. The output of this activity are:

- Source code (git repository)
- Configuration files (git repository)
- Build/install/deploy instructions in one or several files depending on the complexity. (git repository, README.md, INSTRUCTIONS.md, INSTALL.md, DEPLOY.md)

#### Code Review activities

It shall be verified that all the software units are implemented following the defined coding standards and best practices. This activity is performed by the QA Engineer. It receives as input the code generated by thr Software Developer and reviews that coding standards, pest practices are followed and searches for error or security issues. If the review generates issues, a report is handed to the Software Developer se he can correct them. This code-review cycle will be repeated un til the QA review outputs no issues. The outputs of this activity are:

- Report with all the issues found during review
- If no issues were found, confirmation that the code is ready to be integrated into the main branch.

#### Integration activities

It must be verified that all the modified software units are integrated together and that interfaces implement their definitions. Integration activities might include compilation and linkage of libraries, definition and implementation of interfaces between different software unit or any other activity whose goal is the correct interaction between different units.

### Testing

#### Tests definition activities

Validation of working software is critical to ensure that the code performs as expected. Clear validation criteria shall be established for each requirement and all requirements shall be verified through testing or other means. Testing will be performed at three levels:

1. **Unit Testing:** Automatic testing of software units. All software units shall have unit tests that verifies that core functionality works as expected. High code coverage is expected to produce high quality software.
2. **Integration Testing:** Verify that software units are integrated together and test, the interfaces between different units.
3. **System Testing**: Functional and non functional tests that verify that the requirements are met the application complies with their acceptance criteria. All the requirements shall be traced to a system test.

When possible, all tests (unit, Integration, amd System) shall be automatic, and implemented using the selected testing framework(s) so regression errors can be found earlier during the development phase.

The outputs of this activity are:

- Unit tests definitions. Source code in the Git repository.
- Integration tests definitions. Source code in the Git repository or manual test specification in the [tests folder](../test-specifications).
- System tests definitions. Source code in the Git repository or manual test specification in the [tests folder](../test-specifications).

#### Test execution

All test defined tests shall meet the defined acceptance criteria before committing a new functionality into the main branch. The outputs of this activity include:

- Automatic tests reports. This can be an automatic generated report or a console outputs with test results or the output of the tests stage of a CI server.
- Manual tests report. A report with the result of the execution of the manual tests.

### Git Flow

The code and the documentation of the project lives in a git repository. When a new functionality is implemented all activities from planning to testing are performed for the functionality and all the outputs are put under control management. We follow a Git Flow in which a new branch is created for all the cycle of the functionality:

1. A new branch is created in the repository: feature/feature-description, or user-story/story-description, or enabler-story/enabler-description, or bug/bug-description, depending on the implementation type.
2. All the cycle is executed, committing all the artifacts from each activity (specifications, requirements, source code, test definitions, etc..) to the repository. If testing is executed through an external tool that manages the test execution records, or automatic testing is performed in a CI server that stores internally the test results, then test reports included in these systems do not need to be committed into the repository.
