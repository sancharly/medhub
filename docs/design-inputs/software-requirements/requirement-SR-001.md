# SR-001 Browser-accessible web application over HTTPS

## Summary

The system shall be delivered as a web application served over HTTPS and usable through a standard web browser without client-side installation.

## Description

This requirement implements the need for browser-based access by providing the application as a server-hosted web application reachable at a URL. All core user workflows are delivered through the browser. Transport is over HTTPS to satisfy security expectations. No browser plugin or desktop client is required.

## Acceptance Criteria

1. The application is reachable by entering a URL in a web browser and loads its interface without requiring any installation.
2. All HTTP traffic is served over HTTPS (TLS); plain-HTTP requests are redirected to HTTPS.
3. A user can complete authentication and reach their role-appropriate landing view entirely within the browser.

## Origin Requirement

Derived from: User Need UN-001 "Web-based access to the health hub" and Non-Functional Requirement NFR-007 "Cybersecurity".

## Risk Analysis

### Rationale

A browser-delivered application served over HTTPS satisfies the access goal while protecting data in transit, a baseline expectation for medical-device cybersecurity and GDPR.

### Potential Risks

- Security risk: serving over plain HTTP would expose credentials and health data.
- Operational risk: an unreachable application blocks all workflows.

### Control Measures

- Enforce HTTPS-only with redirects and HSTS; verify via system testing.
- Monitor availability of the hosted application.

## Status

Approved

## Version History

Version 1.0 - Initial creation
