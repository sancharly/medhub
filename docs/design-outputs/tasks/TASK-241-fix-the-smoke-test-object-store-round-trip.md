---
id: "TASK-241"
type: task
title: "Fix the smoke test's object-store round trip"
status: approved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-26"
updated: "2026-11-26"
links:
  - target: "SR-040"
    relation: implements
  - target: "CR-008"
    relation: relates_to
  - target: "PRB-096"
    relation: relates_to
  - target: "TS-014"
    relation: relates_to
tags: ["cr:CR-008", "infra", "verification"]
---

# TASK-241 — Fix the smoke test's object-store round trip

- **Software items / units:** SI-DEVINFRA, the smoke test `infra/smoke-test.sh` (a verification tool, not shipped product code).
- **PRB:** PRB-096. **CR:** CR-008 (D-E: PRB-096 taken into CR-008 by the human, 2026-11-26).
- **Requirement:** SR-040 AC 3 and AC 5 (the object store is reachable only from the backend and the bucket initialiser). The check "'backend' stores and reads back an object" is the positive control of that section, and TS-014 TC-014.6 names the section as its started-stack evidence. No new AC.
- **Depends on:** TASK-239 (found the defect; committed d6f58ab). Last task of CR-008.
- **Size:** XS (one script, records).

## Goal

`bash infra/smoke-test.sh` reads "0 failed" on a healthy started stack, so the smoke test is again usable as evidence and as a release gate.

## Files

- `infra/smoke-test.sh` (the inline Python of the round-trip check, around line 232): `import io` and `c.put_object(k, io.BytesIO(b"smoke"), 5, "text/plain")`, the signature of `ObjectStorageClient.put_object(self, key, fileobj, size, content_type)` (`backend/app/core/object_storage.py:40`).
- Records: PRB-096 (Resolution, `resolved`), CR-008 (task table, link, verification summary), TASK-239 / TS-010 / TS-019 (QA-2 to QA-4 of the TASK-239 review).

## Acceptance criteria

- [x] The round-trip check passes on a started stack: `[PASS] 'backend' stores and reads back an object`.
- [x] The whole smoke test reads "0 failed" on a stack built from the branch head plus this change, with every service built (79 checks).
- [x] `bash -n infra/smoke-test.sh` and `python3 -m unittest discover -s infra/tests` pass; no other check changes.

## Verification

1. `bash -n infra/smoke-test.sh`; `python3 -m unittest discover -s infra/tests`.
2. A scratch Compose project (another name, subnet and host port than the dev stack, throwaway secrets, backend and frontend built from the working tree): `bash smoke-test.sh` shows "0 failed".
3. The scratch project is removed with its volumes and local images; the dev `infra` stack is untouched.

## Implementation record (Software Developer, 2026-11-26)

`infra/smoke-test.sh`: `import io` added and the call changed to `put_object(k, io.BytesIO(b"smoke"), 5, "text/plain")` (signature checked at `backend/app/core/object_storage.py:40`). `bash -n` passes; `python3 -m unittest discover -s infra/tests`: 178 passed. Started stack (scratch project `tcheck2`: subnet 10.79.79.0/24, proxy on `127.0.0.1:19443`, throwaway secrets, backend and frontend built from head d6f58ab plus this change, so all services have a build and section 11 runs its frontend checks): **79 passed, 0 failed**, including the round trip and the 401 of check 9b. Removed afterwards with `down -v --rmi local`; no volume or image of the project remains; the dev `infra` stack (8 containers) was not touched. PRB-096 `resolved`; CR-008 summary updated. The earlier 76-check count of TASK-239 is explained there (frontend not built). Hosted CI does not run the smoke test.

## Definition of Done

- [x] PRB-096 `resolved` with a Resolution section citing the 0-failed run; CR-008 verification summary updated; `traceability-check` 0 errors.

## QA review — round 1 (2026-11-26): APPROVED

- **Fix matches the signature.** I ran the round-trip snippet from `infra/smoke-test.sh`, extracted as is,
  against the real `ObjectStorageClient` (`backend/app/core/object_storage.py:40`) with only `__init__`
  replaced by a fake boto client. It printed `ok`: `PutObject` received `ContentLength=5` with a body of 5
  bytes, `ContentType=text/plain` and `ServerSideEncryption=AES256`, and `delete_object` left the store empty.
  The diff is these two lines only.
- `bash -n infra/smoke-test.sh` exits 0, and `python3 -m unittest discover -s infra/tests` passes 178 tests.
- **The 79/0 run is trusted without a new stack.** 79 is the count QA predicted independently in the
  TASK-239 review: 78 as shipped at CR-005, plus check 9b, with the frontend built. The snippet is shown to
  work against the real client code. No `tcheck2` container, volume or image remains.
- **SR-040 is the right target.** The check is the positive control of the AC 3 and AC 5 started-stack
  section, and TS-014 TC-014.6 names that section as its evidence.
- **TASK-239 QA-2 to QA-5 are fixed.** QA-2 is in TASK-239 1.3 and TS-010 1.9, QA-3 in TS-010 1.9, and QA-4
  in TS-019 1.8. For QA-5, PRB-096 now has the timing evidence, and the fix adds `import io`. QA confirmed
  with `git merge-base --is-ancestor` that f645979 and a5fd91a do not contain 3bdd7ee.
- **PRB-096 `resolved` is justified.** CR-008 1.5 has the `resolves` link and records D-E, and the
  Resolution cites the 0-failed run.
- `traceability-check` (fallback parser, all 489 records): 0 errors.
- LOW, not blocking: TS-014 TC-014.6 does not record the 2026-11-26 run. Record it at the next TS-014 change
  if wanted.

## Version history

- 1.0 (2026-11-26) — Created at CR-008 D-E (Software Developer role, on the coordinator's request). `draft`.
- 1.1 (2026-11-26) — Implemented and verified (Software Developer role). `in_review`.
- 1.1 (2026-11-26, QA) — QA review round 1: APPROVED; acceptance criteria and DoD ticked. `approved`.
