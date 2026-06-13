# Context and Scope

Use this template, adapting content as needed for the specific module

```markdown

## Business Context

[Brief description of the business context of the module]
 
[diagram explaining how the module collaborates with different domain entities or actors, like end users, file systems, databases, network nodes, etc...]

### Business Interfaces

[Table describing in detail all the elements from the business context diagram]

| Entity          | Direction | Description                                |
|-----------------|-----------|--------------------------------------------|
| **Surgeon**     | Inbound   | The user interfaces through QML components |
| **PACS server** | Outbound  | Upload dicom images to PACS server         |

## Technical Context

[technical diagram explaining how the module and its main components collaborates with different domain entities or actors. The difference with the business context is that technical context gives more technical details about interfaces and communication protocols]

### Technical Interfaces

[Table describing in detail all the elements from the technical context diagram]

| Component                 | Data/Protocol/Interface | Direction | Description                                               |
|---------------------------|-------------------------|-----------|-----------------------------------------------------------|
| **Surgeon**               | UI interface            | Inbound   | The user interfaces through QML components                |
| **QML component**         | UI interface            | Outbound  | Provides UI controls to interact with the application     |
| **Communications module** | DICOM/ethernet          | Outbound  | Interfaces with the PACS server to upload the DICOMimages |

```
