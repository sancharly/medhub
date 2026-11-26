---
id: "PRB-096"
type: problem-report
title: "The smoke test's object-store round trip calls put_object with its old signature and always fails"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-26"
updated: "2026-11-26"
criticality: minor
links: []
tags: ["test", "infra", "found-in:TASK-239", "outside:CR-008"]
---

# PRB-096 — The smoke test's object-store round trip calls put_object with its old signature and always fails

## Observed

Found by the Software Developer in TASK-239 (2026-11-26) running `bash infra/smoke-test.sh` on a started stack built from the branch: 75 passed, 1 failed. The failure is `[FAIL] 'backend' stores and reads back an object: TypeError: ObjectStorageClient.put_object() missing 1 required positional argument: 'content_type'`. Every other check, including the CR-008 check (9b, 401 on the module route), passed.

## Impact

`infra/smoke-test.sh` can never report "0 failed" on a healthy stack, so a real failure of the object-store round trip (SR-040 AC 3, the backend can reach and use the store) is indistinguishable from this one, and the smoke test cannot serve as a release gate until it is fixed. The product code is not involved.

## Investigation

`infra/smoke-test.sh:236` runs `c.put_object(k, b"smoke", "text/plain")` inside the backend container. Since TASK-135 (commit 3bdd7ee, 2026-11-13, bounded upload memory) the method is `put_object(self, key, fileobj, size, content_type)` (`backend/app/core/object_storage.py:40`), so the call passes three arguments to four parameters and a `bytes` value where a file object is expected. The smoke check was written in TASK-177 (d4cdba0, 2026-10-30) for the earlier signature and was not updated. Not reproduced on a stack that predates TASK-135; the cause is read from the two commits and observed on the 2026-11-26 run.

## Safety evaluation

No safety impact: test tooling only, and a false red, never a false green. It affects no data, no clinical function and no released version (no `release` record exists).

## Resolution

Not resolved. Suggested fix: call `put_object(k, io.BytesIO(b"smoke"), 5, "text/plain")`, and run the smoke test on a started stack to show "0 failed". Outside CR-008; for the human to plan.

## Source

TASK-239 started-stack run, 2026-11-26.

## Version history

- 1.0 (2026-11-26) — Created from TASK-239. `open`, `minor`, outside CR-008.
