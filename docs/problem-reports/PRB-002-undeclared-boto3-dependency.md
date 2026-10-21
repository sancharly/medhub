---
id: "PRB-002"
type: problem-report
title: "boto3 is imported at runtime but declared nowhere, so attachment storage fails"
status: open
criticality: major
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
links: []
tags: ["soup", "configuration-management"]
---

# PRB-002 — boto3 is imported at runtime but declared nowhere

## Observed

`ObjectStorageClient.__init__` imports `boto3` lazily and raises `ImportError` with the message
"boto3 is required for object storage" when it is missing
(`backend/app/core/object_storage.py:17-21`). `boto3` appears in no manifest: not in
`backend/pyproject.toml` (runtime or dev group), not in `backend/uv.lock`, and not installed by
`backend/Dockerfile`. A grep over the repository finds it only in that module, in review notes and
in the SOUP list.

## Impact

- Any environment built from the declared dependencies has no `boto3`, so the first attachment
  upload or download raises `ImportError` — **SR-013 (clinical entry attachments) and the DICOM
  path that depends on it are non-functional in a real deployment**. Unit tests pass because they
  substitute a fake storage client.
- **IEC 62304 §8.1.2**: a SOUP item that is not declared has no title/manufacturer/version record
  and cannot be version-controlled or anomaly-reviewed. Its record,
  [SOUP-019](../soup/SOUP-019-boto3.md), is the one with no version.

## Root cause

TASK-045 introduced the storage client with an intentionally lazy import (documented in the module
docstring) so that unit tests and non-storage deployments would not need the SDK, but the
corresponding dependency declaration — as a required dependency or an extra — was never added.

## Safety evaluation

No direct hazard: the failure is loud (an exception) and cannot mis-attribute or corrupt clinical
data. The consequence is unavailability of attachments, which delays access to clinical
information; assessed in the RISK register as an availability contribution, not a data-integrity one.

## Proposed resolution

Declare `boto3` with a pinned lower bound in `backend/pyproject.toml`, refresh `uv.lock`, record the
locked version in SOUP-019, and add a smoke check that instantiates `ObjectStorageClient` against
the MinIO service in CI so a missing SDK fails the build rather than a user request. Alternatively,
keep it optional but declare an extra and fail fast at application startup when object storage is
configured. Requires a CR that links `resolves` → PRB-002.
