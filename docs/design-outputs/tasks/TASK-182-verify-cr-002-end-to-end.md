---
id: "TASK-182"
type: task
title: "Verify CR-002 end to end on a host with no cached images"
status: draft
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
links:
  - target: "SR-028"
    relation: implements
  - target: "SR-040"
    relation: implements
  - target: "CR-002"
    relation: relates_to
  - target: "TASK-172"
    relation: relates_to
  - target: "TASK-173"
    relation: relates_to
  - target: "TASK-174"
    relation: relates_to
  - target: "TASK-175"
    relation: relates_to
  - target: "TASK-176"
    relation: relates_to
  - target: "TASK-177"
    relation: relates_to
  - target: "TASK-178"
    relation: relates_to
  - target: "TASK-179"
    relation: relates_to
  - target: "TASK-180"
    relation: relates_to
  - target: "TASK-181"
    relation: relates_to
tags: ["verification", "regulatory", "cr:CR-002", "issue:sancharly/medhub#33"]
---

# TASK-182 — Verify CR-002 end to end on a host with no cached images

- **Software item / unit:** all, as verification evidence and gap report. No code change is
  expected.
- **Depends on:** TASK-172..181, all merged on the branch (`relates_to`)
- **Branch:** `bug/minio-object-store`
- **Size:** S
- **Needs:** a Docker host with an empty daemon (a disposable `docker:dind` pinned by digest, or a
  fresh CI runner) and network access (registries, CI on the branch head)
- **Checkpoint C:** this task is the end-to-end checkpoint over the whole CR.

## Objective

Show that CR-002 works end to end on the branch head, on a host that has never cached an image,
and that the records are complete (AC-9, AC-12, AC-15..AC-19). The records then go to the human
gate.

## Implementation detail

1. **Fresh-host run (AC-9, AC-16):**
   - On an empty daemon, check out the branch head. On an arm64 workstation, also run the stack
     under `--platform linux/amd64`, or take the CI runner as the amd64 host.
   - Run `docker compose -f infra/docker-compose.yml build --no-cache --pull`, then
     `docker compose up -d`.
   - Record the architecture (`uname -m` inside a container) and that every image came from a
     registry or a local build.
   - **Do not prune images on the reference workstation.** Its cached MinIO image is the only
     copy, and TASK-178's rollback needs it.
2. `python3 infra/check_image_pins.py` exits 0.
3. `bash infra/smoke-test.sh` reports every check passing: the 17 existing checks plus those
   added by TASK-176 and TASK-177. Record N/N.
4. **Suites (AC-17):**
   - `cd backend && uv run pytest --cov=app --cov-fail-under=85`;
   - `cd frontend && npm test`;
   - lint and type-check in both;
   - every job in `.github/workflows/ci.yml`, including `object-store-integration`, is green on
     the branch head.
5. **Records:**
   - AC-12: SOUP-022 and SOUP-023 are `obsolete`; SOUP-036's `soup_version` equals the deployed
     image; the review is dated and sourced; no non-`obsolete` record links an obsolete SOUP item
     except the retiring ones (the command in TASK-181).
   - AC-15: SR-013, SR-022, SR-028 and SR-040 are `in_review` or later, and TS-007, TS-008,
     TS-013 and TS-014 `verify` them with a test case for each new AC.
   - AC-19: PRB-036, 039, 042 and 043 are `resolved` with `## Investigation` and
     `## Resolution`. None is `closed`. PRB-007 is `open` with its note.
   - CR-002's AC coverage table and "Escalations" are complete.
6. **AC-18:** `traceability-check` over the whole project reports 0 errors. List the warnings,
   with the reason for each (for example W5 for approved records that point at `in_review` ones,
   as in CR-003).

## Acceptance criteria

- [ ] CR-002 **AC-9**, **AC-16**, **AC-17** and **AC-18**, as above.
- [ ] CR-002 **AC-12**, **AC-15** and **AC-19** confirmed.

## Verification

The commands above, with their output, in the evidence section.

## Definition of Done

- [ ] Every check passes, or a PRB is raised for any defect found (`problem-report-resolution`).
- [ ] CR-002 is ready for the human gate. Its status stays `in_progress` until the human closes it.
