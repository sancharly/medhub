---
id: "PRB-096"
type: problem-report
title: "The smoke test's object-store round trip calls put_object with its old signature and always fails"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-26"
updated: "2026-11-26"
criticality: minor
links: []
tags: ["test", "infra", "found-in:TASK-239", "cr:CR-008"]
---

# PRB-096 — The smoke test's object-store round trip calls put_object with its old signature and always fails

## Observed

Found by the Software Developer in TASK-239 (2026-11-26) running `bash infra/smoke-test.sh` on a started stack built from the branch: 75 passed, 1 failed. The failure is `[FAIL] 'backend' stores and reads back an object: TypeError: ObjectStorageClient.put_object() missing 1 required positional argument: 'content_type'`. Every other check, including the CR-008 check (9b, 401 on the module route), passed.

## Impact

`infra/smoke-test.sh` can never report "0 failed" on a healthy stack, so a real failure of the object-store round trip (SR-040 AC 3, the backend can reach and use the store) is indistinguishable from this one, and the smoke test cannot serve as a release gate until it is fixed. The product code is not involved.

## Investigation

`infra/smoke-test.sh:236` runs `c.put_object(k, b"smoke", "text/plain")` inside the backend container. Since TASK-135 (commit 3bdd7ee, 2026-11-13, bounded upload memory) the method is `put_object(self, key, fileobj, size, content_type)` (`backend/app/core/object_storage.py:40`), so the call passes three arguments to four parameters and a `bytes` value where a file object is expected. The round-trip lines came in with TASK-177 (d4cdba0, 2026-10-30), written for the earlier signature, and were not updated when TASK-135 changed it. Timing: the last runs that read 0 failed were on `f645979` (TASK-215) and `a5fd91a` (TASK-216), both on the CR-005 branch, which does not contain 3bdd7ee (checked with `git merge-base --is-ancestor`); CR-006 and CR-007 recorded no smoke runs, so the first run after 3bdd7ee was TASK-239 (2026-11-26). The cause is read from the commits and observed on that run.

## Safety evaluation

No safety impact: test tooling only, and a false red, never a false green. It affects no data, no clinical function and no released version (no `release` record exists).

## Resolution

Resolved in CR-008 (D-E; the `resolves` link is on CR-008) by TASK-241, verified in the working tree on 2026-11-26 (head d6f58ab plus the task's change).

What changed: `infra/smoke-test.sh` runs `import io` and `c.put_object(k, io.BytesIO(b"smoke"), 5, "text/plain")` in the round-trip check, the current signature of `ObjectStorageClient.put_object(key, fileobj, size, content_type)`. Nothing else changed.

Verification: `bash -n infra/smoke-test.sh` and `python3 -m unittest discover -s infra/tests` (178 tests) pass. On a started stack (a scratch Compose project beside the dev stack, throwaway secrets, backend and frontend images built from the working tree) the smoke test reads "=== Results: 79 passed, 0 failed ===", including `[PASS] 'backend' stores and reads back an object` and `[PASS] unauthenticated GET /modules/dicom-viewer/studies/<uuid> returns 401`. The scratch project was removed with its volumes and images. Hosted CI does not run the smoke test.

## Source

TASK-239 started-stack run, 2026-11-26.

## Version history

- 1.0 (2026-11-26) — Created from TASK-239. `open`, `minor`, outside CR-008.
- 1.1 (2026-11-26) — Taken into CR-008 (D-E); fixed by TASK-241 and verified on a started stack (79 passed, 0 failed); timing evidence added. `resolved`. The human closes the PRB in MedTrace after the merge.
