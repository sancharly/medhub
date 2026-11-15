---
id: "TASK-225"
type: task
title: "arc42 sections, ADR index and deployment guide for CR-006"
status: approved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-15"
links:
  - target: "SR-013"
    relation: implements
  - target: "SR-016"
    relation: implements
  - target: "SR-017"
    relation: implements
  - target: "SR-026"
    relation: implements
  - target: "SR-030"
    relation: implements
  - target: "CR-006"
    relation: relates_to
  - target: "ADD-016"
    relation: relates_to
  - target: "ADD-014"
    relation: relates_to
tags: ["cr:CR-006", "documentation", "arc42"]
---

# TASK-225 — arc42 sections, ADR index and deployment guide for CR-006

- **Role:** Document Writer (arc42 narrative); the Software Architect reviews consistency with the ADDs.
- **CR:** CR-006. **Depends on:** TASK-135 … TASK-224 and TASK-227 committed (TASK-223 too, for the module-settings accessor) (documents what was built, not the plan).
- **Branch:** `fix/review-2026-07-reliability`.
- **Size:** M (docs only).

## Objective

Keep the arc42 narrative consistent with the ADD records changed at the CR-006 Plan stage and with the code
(the ADD records point to these sections and must not duplicate them).

## Sections to update (`docs/design/`)

| Section | Change | From |
|---|---|---|
| 04 solution strategy | Concurrency model: blocking IO in the thread pool, pools sized together | ADR-0022, TASK-136 |
| 05 building blocks | `U-ATT-Upload` / `U-ATT-Fetch` bounded IO; DICOM module bounds; frontend lazy routes, `useMe`, `useMyModules` | ADD-012, 015, 018, 019, 020/021 |
| 06 runtime views | Attachment download (two passes, `If-Match`, abort); upload size refusal; erasure refused when its e-mail cannot be queued; retention retry | ADR-0021, TASK-141, 217 |
| 07 deployment view | nginx `client_max_body_size`; `API_THREADPOOL_SIZE`, `DB_POOL_*` (values as approved by the human, D-14); migration 0011 locks four tables and migration 0012 locks `attachment` and `consent_grant` while building | TASK-135, 136, 219, 220 |
| 08 cross-cutting concepts | Client session timers from the server expiry; debounced activity; chunk-failure boundary; error contract of the 503 erasure response | TASK-144, 145, 222, 141 |
| 10 quality requirements | Normal load = 20 clients on one worker (D-3); initial-payload budget (SR-026 AC 7 value); 150 MiB / 1 GiB bounds (D-2) | SR-026, SR-017 |
| 11 risks and technical debt | NumPy absent so the frame decode cannot render (PRB-048); two object-store reads per download | P-6, ADR-0021 |
| 12 interfaces | `PlatformServices.attachments.open(..., max_bytes)`; `GET /me` `sessionExpiresInSeconds`; extend `expiresInSeconds`; `POST /auth/password` wrong current password 400; `GET /me/modules` does not slide the session; erasure 503; the module contract names `app.modules.module_settings` and the name-level allow-list | TASK-217, 144, 221, 141, 223 |

Rows added in version 1.2 (items that accumulated after 1.1; the 04 to 11 rows above also cover TASK-143,
145, 146, 219, 220, 221, 222, 227, 228 and 223):

| Item | Change | From |
|---|---|---|
| 05 building blocks, `U-MH-ModuleSettings` | New unit in SI-MODHOST (`backend/app/modules/module_settings.py`); the name-level allow-list of `backend/tests/modules/test_module_boundary.py` | TASK-223 (QA finding R2-3) |
| ADD-014 | Reopened as 1.1 (`approved` record, rule applied): names the unit and records the allow-list | TASK-223 |
| ADD-005, 012, 015, 016 | "CR-006 (planned)" wording confirmed as implemented for TASK-135, 136, 217, 218, 219, 220, 224, 227; ADD-005 "(planned; TASK-224)" removed | TASK-135 … 227 |
| SOUP-024 | nginx text: `client_max_body_size 151m` and the 413-to-400 mapping are relied on | TASK-135 |
| RISK-003, RISK-007 | TS-019 named in the verification column | TASK-218 |
| Record fixes left by QA | TASK-227 (ADR-0023 is Accepted), TS-002 TC-002.10, TS-004, TS-011, TS-001, TS-018, SOUP-028, PRB-019, PRB-032, TASK-145, RISK-008 | QA rounds of TASK-141, 143, 145, 146, 224, 227 |
| `infra/DEPLOY.md` | Pool settings with deployed values 20/20/20/10 and code defaults 15/5/10/30, the start-up invariant, lock windows of 0011 and 0012 | TASK-136, 219, 220 |
| CR-006 1.15 | 30 sites in 14 files for TASK-227; plan row of this task | TASK-227 QA finding 5 |

Also: `docs/design/adr/README.md` index lines for ADR-0021, ADR-0022 and ADR-0023 (status as recorded in each
ADR: all three Accepted on 2026-11-13; ADR-0023 refines ADR-0016 for streamed responses);
`infra/DEPLOY.md` (pool settings, body limit, migration 0011 and 0012 window); remove any request-id promise
found by TASK-224.

**ADD-016 (Software Architect, TASK-219 QA finding 5):** the `U-PER-Migrations` entry still says "CR-006
(planned)" for migration 0011. Confirm it as implemented (0011: the four indexes, TASK-219) and add
migration 0012 (`ix_attachment_clinical_entry_id`, `ix_consent_grant_doctor_id_active`, TASK-220, D-29), then
remove the "planned" marker. Do this after TASK-227 has landed its own ADD-016 change, as one edit on top of
it (ADD-016 is `in_review`; version bump and history line).

## Acceptance criteria

- [x] Every row above done or marked "no change" with a reason; links from ADD-005, 008, 009, 012, 015, 016,
  017, 018, 019, 020, 021, 023 resolve.
- [x] ADR index lists ADR-0021, ADR-0022 and ADR-0023 with their recorded status.
- [x] ADD-016 states migrations 0011 and 0012 as implemented, with no "CR-006 (planned)" marker left for them.

## Definition of Done

- [x] `traceability-check` no error for this record

## QA review round 1 (2026-11-15, QA Engineer) — CHANGES REQUESTED

Code is the truth; checked at HEAD `9a352bb` with the docs-only working tree (no source change in `git diff`).
Confirmed against the code: pool settings, defaults and the start-up invariant (`core/config.py:101-144`,
`main.py:53`, `docker-compose.yml:101-104`, `.env.example:119-122`); 0011/0012 plain `op.create_index`; the
OpenAPI claims of section 12 (`MeResponse.sessionExpiresInSeconds`, `SessionExtendResponse.expiresInSeconds`,
password 204/400/401/403/422, delete 503); `client_max_body_size 151m` and `error_page 413 =400` in
`infra/reverse-proxy/nginx.conf:78,83,94-101`; retention sweep and erasure-gate numbers; every RISK-008 test name
exists; the approved-record rule on every reopened record; no SR changed.

- **MEDIUM 1 — erasure runtime view does not match the code order.** `docs/design/06-runtime-views.md:160-167`
  shows the audit rows written before the enqueue and omits the session revocation. `identity/erasure.py:97-157`:
  anonymize and add the dataset, then `send_erasure_code_email.delay` (l. 130), then `invalidate_all` (Redis,
  l. 140, not rolled back by a failed commit), then the two audit rows (l. 142-157), then the `DbSession` commit.
  → Reorder the diagram (enqueue; on failure rollback and 503 with sessions untouched; else `invalidate_all`,
  audit rows, commit, 200) and state in a bullet that the sessions are already revoked if the commit then fails.
- **MEDIUM 2 — "one owner of the session end" overstated.** `05-building-blocks.md:144`, `08-cross-cutting-concepts.md:104`
  and `06-runtime-views.md:187` say the `AuthError` handler and Log out go through `handleExpired`.
  `SessionActivityProvider.tsx`: the `setAuthExpiredHandler` callback (l. 58-66) redirects to `/login?timeout=1`
  without a server logout (the server already answered 401), and `handleLogout` (l. 81-89) awaits the logout
  and goes to `/login`. Client timeout, warning countdown and extend-401 do use `handleExpired`; all paths set
  `sessionEnded`, so the cache clear on unmount holds for all. → Reword the three places accordingly.
- **MEDIUM 3 — stale "CR-006 (planned)" body markers left.** `ADD-009-groups-and-module-enablement.md:37`
  (`groups_of`, TASK-220 approved) and `ADD-026-deployment-configuration-and-runtime-hardening.md:114` (proxy body
  limit TASK-135, pool settings TASK-136; still "values as approved by the human", now 20/20/20/10). ADD-006, 008,
  017, 018, 019, 021 and 023 carry the phrase only in version-history lines (no change needed). → Clear both
  markers under the approved-record rule (version bump, approval record cleared, `in_review`).
- **LOW 4** — `06-runtime-views.md:169` "14 checks" is 15 (first check plus 14 re-checks); `05-building-blocks.md:128`
  and `06-runtime-views.md:175` say an unverifiable check sends with a WARNING, but it is sent only after the 14
  re-checks (`email_tasks.py:181-197`). → "after the last re-check".
- **LOW 5** — ADR-0023 amendment note (`adr/0023-...md:118`) names Context and Decision; Consequences (l. 100,
  "31 sites change") carries the same count. → Name it too. The note still needs the human's acknowledgement
  (as ADR-0020's); record it in the ADR index line when given.
- **LOW 6** — PlantUML colours: "Browser" (`06-runtime-views.md:122`) and "Admin client" (l. 154) are `#lightgreen`
  (framework colour). → `#lightgray` for the browser (third party), or no colour for the SPA. Both diagrams render.
- **LOW 7** — `05-building-blocks.md:152` leaves "design intent ... confirm" for `U-FEM-Registry`/`U-FEM-NavGate`
  (confirmed absent from `frontend/src`), and `12-interfaces.md:112` still lists `ModuleRegistry.register(...)` without
  the caveat. An approved ADD-021 naming units that do not exist is a §9 problem: the orchestrator should raise
  a PRB (or human decision) and both sections should cite it instead of "confirm".
- **LOW 8** — `11-risks-and-technical-debt.md:62` "No limit or check was found in the code (inferred; confirm)":
  confirmed, no check (`grep` for spool/tempfile/disk in `backend/app` and Compose). → Drop "(inferred; confirm)";
  the residual needs a human accept or a PRB.

Writer's findings: ModuleRegistry/NavGate absent — confirmed; planned markers — see MEDIUM 3; upload scratch
space unchecked — confirmed; SOUP-024 413 → 400 — confirmed; PRB-019 count 412 — confirmed (`npx vitest run`,
412 passed in 41 files).

## QA review round 2 (2026-11-15, QA Engineer) — APPROVED

All eight round 1 findings re-checked against the code: the 6.14 diagram follows `identity/erasure.py`
(`.delay`, `invalidate_all`, audit rows, commit) and a bullet states the revoked sessions on a failed commit;
sections 05, 06.16 and 08.15 describe the three `handleExpired` paths, the `AuthError` handler (no server logout)
and Log out (`/login`) as in `SessionActivityProvider.tsx`; ADD-009 1.2 and ADD-026 1.7 have no body marker left
and ADD-026 states 15/5/10/30 and 20/20/20/10; 15 checks and "after the last re-check" match `email_tasks.py`; the
ADR-0023 note names the Consequences (human acknowledgement still pending); `Browser` is `#lightgray`, the SPA
uncoloured, both diagrams pass `plantuml -checkonly`; PRB-091 and PRB-092 are well formed (`open`, `minor`, safety
evaluation and open human decision; claims match `frontend/src/modules/` and the absent spool check) and are cited
in sections 05, 11 and 12. Verification: `tests/test_env_example.py` 18 passed; `infra/tests` 178 OK; trace over
26 records plus linked (199): 0 errors, 215 warnings (W5, approval-without-digest per project convention, and
three pre-existing W6 on the obsolete MinIO SOUP); `git status` shows docs and `infra/DEPLOY.md` only.
TS-001, TS-002, TS-004, TS-011 and TS-018 approved with this review.

## Version history

- 1.0 (2026-11-13) — Created at the CR-006 Plan stage (Software Architect).
- 1.1 (2026-11-13) — CR-006 D-29 (Software Architect role): ADD-016 confirmation added to the scope (0011
  "planned" → implemented; 0012 added; TASK-219 QA finding 5) with a `relates_to` link; ADR index extended to
  ADR-0023; 07 deployment view and DEPLOY.md include the 0012 lock window; depends on TASK-227 too. Stays `draft`.
- 1.2 (2026-11-14) — Scope extended with the items that accumulated after 1.1 (module-settings unit and ADD-014 1.1, session and erasure interface changes, DEPLOY.md pool settings and lock windows, wording and record fixes left by QA); links to SR-016 (`implements`) and ADD-014 (`relates_to`) added. Implemented by the Document Writer; `draft → in_review` at handoff (2026-11-15).
- 1.3 (2026-11-15) — QA review round 1 (QA Engineer): CHANGES REQUESTED (3 MEDIUM, 5 LOW, see "QA review round 1"); `in_review → draft`. The reopened records stay `in_review`; TS-001, TS-002, TS-004, TS-011 and TS-018 are not approved in this round.
- 1.4 (2026-11-15) — QA findings of round 1 fixed (Document Writer): erasure runtime view reordered to the code (`.delay`, `invalidate_all`, audit rows, commit; sessions revoked if the commit fails); session-end paths described as they are (three through `handleExpired`, the `AuthError` handler without a server logout, Log out); stale "planned" markers cleared in ADD-009 1.2 and ADD-026 1.7; e-mail check counts (15 checks, send after the last re-check); ADR-0023 note names the Consequences; PlantUML colours; PRB-091 (unbuilt `U-FEM-Registry`, `U-FEM-NavGate`, `ModuleRegistry`) and PRB-092 (unchecked upload scratch space) raised, both `open`, `minor`, outside CR-006. `draft → in_review`.
- 1.4 (2026-11-15) — QA review round 2 (QA Engineer): APPROVED; checkboxes ticked; `in_review → approved` (status only).
