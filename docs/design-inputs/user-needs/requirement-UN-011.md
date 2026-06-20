# UN-011 Viewing DICOM medical images

## Summary

A doctor needs to open and visualize DICOM medical images (CT, MRI, X-ray) within the platform, with controls to adjust and navigate the images, so they can review imaging studies during clinical work.

## Description

Imaging is central to many clinical decisions. Doctors need to open DICOM images attached to clinical entries or otherwise available to them and inspect them adequately. Adequate inspection requires adjusting brightness/contrast (window level), zooming in and out, panning across the image, and navigating slices for volumetric studies such as CT and MRI. This capability is delivered as the first MedHub module and demonstrates the plugin system.

## Acceptance Criteria

1. A doctor with the DICOM viewer module enabled can open DICOM images (CT, MRI, X-ray) and view them in the platform.
2. The viewer provides level/contrast (window/level) adjustment.
3. The viewer provides zoom in and zoom out.
4. The viewer provides pan.
5. The viewer provides slice navigation for volumetric (multi-slice) studies.

## Risk Analysis

### Rationale

Derived from the MedHub goal "DICOM viewer Module": the first prototype shall include a DICOM viewer with at least level/contrast, zoom, slice navigation, and pan controls, to demonstrate the plugins system.

### Potential Risks

- Safety risk: incorrect rendering (wrong window level, wrong slice order, wrong scaling) could lead to misinterpretation of an image and a clinical error.
- Compliance risk: as a medical-device viewing function, incorrect or misleading display has regulatory consequences (MDR/FDA).

### Control Measures

- Viewer rendering and the required controls are specified in software requirements with testable acceptance criteria traced to this need.
- Correctness of rendering is reinforced by the medical-device regulation NFR (NFR-005) and verified through system testing.

## Status

Approve

## Version History

Version 1.0 - Initial creation
