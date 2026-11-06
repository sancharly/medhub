---
id: "TASK-204"
type: task
title: "Serve any attachment file name on download and audit a failed download"
status: approved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-02"
updated: "2026-11-06"
links:
  - target: "SR-013"
    relation: implements
  - target: "SR-023"
    relation: implements
  - target: "RISK-007"
    relation: mitigates
  - target: "RISK-006"
    relation: mitigates
  - target: "PRB-063"
    relation: relates_to
  - target: "CR-004"
    relation: relates_to
  - target: "ADD-012"
    relation: relates_to
  - target: "ADD-005"
    relation: relates_to
  - target: "TS-007"
    relation: relates_to
tags: ["attachments", "cr:CR-004", "hazard:availability", "control:design", "control:protective"]
---

# TASK-204 — Serve any attachment file name on download and audit a failed download

- **Software items / units:** SI-API `U-API-Routers` (ADD-005, `backend/app/api/routers/attachments.py`
  and a new helper beside it); SI-ATTACH `U-ATT-Fetch` (ADD-012, `backend/app/attachments/service.py`).
- **PRB:** PRB-063. **CR:** CR-004 (D-9).
- **Depends on:** no code dependency beyond committed work (ADR-0016's independent FAILURE rows,
  TASK-183; the client address on audit rows, TASK-137). Independent of every open CR-004 task. Its
  commit goes after TASK-196's, because TASK-196's changes are still uncommitted in the working tree
  and each task is its own commit. No file overlap with TASK-196.
- **Branch:** `fix/review-2026-07-security`.
- **Size:** M (3 source files: one new, two changed; 4 test files, one new; records TS-007, ADD-012,
  RISK-007, PRB-063).
- **Needs:** a Docker daemon for the real-database test and the started-stack check.

## Objective

SR-013 AC 3: an authorized user can download any attachment they may view, whatever its file name.
Today any character outside Latin-1 in the stored name (`’` U+2019, `–` U+2013, `€`, CJK, ...) makes
`GET /api/v1/attachments/{id}` answer 500 (PRB-063): `backend/app/api/routers/attachments.py:110` puts the
raw name in `Content-Disposition: attachment; filename="{filename}"`, and Starlette encodes header values
as Latin-1 when the `StreamingResponse` is built (`:107`). A `"` or `\` in the name produces a malformed
header, and a CR or LF would be a header-injection vector if a name ever carried one.

SR-023 AC 2 (access to clinical data is recorded): a download that fails on the server today leaves no
audit evidence. `AttachmentService.open` records `ATTACHMENT_ACCESS` SUCCESS in the request
transaction (`service.py:155`), the router then raises, and `get_db` rolls the row back together with the
`AUTHZ_ALLOWED` row. Under ADR-0016 the FAILURE event is the evidence for an access that did not
complete; only the checksum path (`service.py:142`, SR-013 AC 5) writes one now.

## Survey: where a `Content-Disposition` header is built

| Place | Builds the header? | Affected by PRB-063? |
|---|---|---|
| `backend/app/api/routers/attachments.py:110` (`fetch_attachment`) | Yes, from the stored file name | **Yes**: the only builder |
| DICOM module, `backend/modules/dicom_viewer/dicom_viewer/router.py:65` (`/studies/{id}`) | No: `Response(content=..., media_type="application/dicom")`, the file name is discarded (`_filename`) | No. But the frontend's "Open in viewer" link (`frontend/src/core/clinical/AttachmentItem.tsx:33`) points to the attachments route, so DICOM files with such names fail there today and are fixed by this task |
| Exports: `anonymized_data.py`, `lifecycle.py`, `me.py`, `clinical.py` routers | No: JSON bodies only. No file export endpoint exists. `app/export_openapi.py` is a CLI | No |
| `fastapi.responses.FileResponse` | Not used anywhere in `backend/app` or `backend/modules` | No |

Frontend: no code parses `Content-Disposition`. `AttachmentItem.tsx:29` is a plain
`<Link href={url} target="_blank">`, so the browser applies the header itself. Current Chrome, Firefox,
Safari and Edge honour `filename*` (RFC 6266 §4.3) and prefer it over `filename`. No frontend change;
the started-stack check below confirms the saved name in a browser.

## Implementation detail

### File names in the header (SR-013 AC 3)

- New module `backend/app/api/content_disposition.py`, one function
  `content_disposition(filename: str, disposition: str = "attachment") -> str`. It never raises for any
  `str` input. Pure standard library (`unicodedata`, `urllib.parse.quote`): no new dependency (CR-004
  boundary). Starlette's own `FileResponse` logic is not reused: it is not available for a
  `StreamingResponse` and sends no ASCII fallback.
- Steps:
  1. **Neutralise controls first:** every character in Unicode category `Cc` (C0 controls including CR,
     LF and TAB, DEL, C1 controls) or `Cs` (a lone surrogate, which UTF-8 cannot encode) becomes `_`.
     This applies to both parameters, so no form of the name can split the header or make the encoding
     raise.
  2. **`filename*`:** `UTF-8''` + `quote(name, safe="")` of the UTF-8 bytes (RFC 5987 §3.2: what `quote`
     leaves unencoded, `A-Z a-z 0-9 _ . - ~`, is a subset of `attr-char`).
  3. **`filename` (ASCII fallback, RFC 6266 §4.3):** NFKD-normalise, drop combining marks (category
     `Mn`), replace every remaining character outside printable ASCII (0x20–0x7E) with `_`, then replace
     `"` and `\` with `_`, and wrap in double quotes. If the result is empty or only dots and spaces, use
     `"download"`.
  4. Result: `attachment; filename="<fallback>"; filename*=UTF-8''<encoded>`. When the name is
     already safe printable ASCII with no `"` or `\`, both parameters are still sent (one code path).
- `fetch_attachment` uses it: `headers={"Content-Disposition": content_disposition(filename)}`.
- The stored `attachment.filename` is not changed at upload: the record keeps what the user uploaded
  (SR-013 AC 2), and only the HTTP representation is encoded. The list and upload JSON responses already
  carry the name as JSON and are unaffected.
- Worked examples (exact values for the tests):

  | Stored name | `filename=` | `filename*=` |
  |---|---|---|
  | `résumé 患者 #1.txt` | `"resume __ #1.txt"` | `UTF-8''r%C3%A9sum%C3%A9%20%E6%82%A3%E8%80%85%20%231.txt` |
  | `report’s summary.pdf` | `"report_s summary.pdf"` | `UTF-8''report%E2%80%99s%20summary.pdf` |
  | `a"b\c.pdf` | `"a_b_c.pdf"` | `UTF-8''a%22b%5Cc.pdf` |
  | `x\r\nX-Injected: 1.txt` | `"x__X-Injected: 1.txt"` | `UTF-8''x__X-Injected%3A%201.txt` |
  | `患者.dcm` | `"__.dcm"` | `UTF-8''%E6%82%A3%E8%80%85.dcm` |
  | `scan.dcm` | `"scan.dcm"` | `UTF-8''scan.dcm` |

  The developer confirms the encoded column with the implementation; the rule above is normative, the
  table is illustrative.

### Failed download audited (SR-023 AC 2, ADR-0016)

"Fails on the server" means: the actor was authorized and the attachment row exists, but no content is
served. Client-side refusals keep their existing evidence: an unknown attachment id is a 404 with no
access to audit, and a denied access already writes `AUTHZ_DENIED` (independent, ADR-0016).

- `AttachmentService` gets one public method `record_access_failure(actor, attachment_id)` that records
  `ATTACHMENT_ACCESS` with outcome FAILURE, target `attachment`/`<id>`, `ip=None` (so the request's
  client address is used, SR-023 AC 6). It is the same event the checksum path writes today; that path
  calls the new method instead of its inline `record` call (same row, no behaviour change).
  `AuditService.record` makes the row independent because the outcome is FAILURE: no flag, no change to
  `audit/service.py`.
- In `AttachmentService.open`, after authorization:
  - `storage.get_object` raises → `record_access_failure`, then re-raise (still a 500 through the
    generic handler).
  - `storage.get_object` returns `None` (row without object) → `record_access_failure`, then the existing
    `NotFoundError` (status unchanged).
  - checksum mismatch → unchanged (502), now through `record_access_failure`.
- In `fetch_attachment`, building the response after `svc.open` returns is wrapped in one
  `try/except Exception`: on an exception, `svc.record_access_failure(actor, attachment_id)` and re-raise.
  With the header fix this path should no longer fail. The guard is kept because PRB-063 is exactly an
  unforeseen failure at this point, and it costs four lines. The `ATTACHMENT_ACCESS` SUCCESS and
  `AUTHZ_ALLOWED` rows of such a request still roll back, as ADR-0016 ("Unchanged") intends: the FAILURE
  row is the record of the attempt.
- Because the DICOM route calls the same `services.attachments.open`, a storage failure on
  `/studies/{id}` now also leaves an `ATTACHMENT_ACCESS` FAILURE row. No change to the DICOM router.

## Tests (write first)

- **New** `backend/tests/api/test_content_disposition.py` (unit, no services):
  - every row of the worked-examples table;
  - round trip: each header value parsed with the standard library (`email.message.Message`, header set
    to the value, `get_params(header="content-disposition")`, the `filename` entry that is an RFC 2231
    tuple passed to `email.utils.collapse_rfc2231_value`) returns the original name with controls
    replaced by `_`. Note that `Message.get_filename()` returns the first `filename` parameter, the ASCII
    fallback, so it is not the round-trip check;
  - the value is always `value.encode("latin-1")`-safe and in fact pure ASCII, and contains no CR or LF,
    for a generated sample covering categories `Cc`, `Cs` (lone surrogates), `Cf`, `Zl`, `Zp` and
    astral-plane characters;
  - empty string and `"..."` give `filename="download"`;
  - **static check** `test_content_disposition_is_built_only_by_the_helper`: no file under `backend/app`
    or `backend/modules` other than `app/api/content_disposition.py` contains the literal
    `Content-Disposition` except as a dictionary key whose value is a call to `content_disposition(`
    (simple text scan, like TASK-189's static check). It fails if a new endpoint builds the header by hand.
- `backend/tests/api/test_attachments_router.py`, new class `TestFetchAttachmentFileNames`:
  - downloads of `résumé 患者 #1.txt` and `report’s summary.pdf` answer 200, with identical bytes and
    the header of the table;
  - `a"b\c.pdf` and `x\r\nX-Injected: 1.txt`: 200, exactly one `content-disposition` header, no
    `x-injected` header in the response;
  - `test_response_build_failure_records_access_failure`: the helper is monkeypatched to raise; the
    response is 500 and `record_access_failure` was called once with the actor and the id.
- `backend/tests/attachments/test_attachment_fetch.py`:
  - `get_object` raises → the exception propagates and one FAILURE `ATTACHMENT_ACCESS` event is
    recorded for the attachment and the actor, no SUCCESS event;
  - `get_object` returns `None` → `NotFoundError` and one FAILURE event;
  - existing checksum and success tests (TC-007.6, TC-007.7) unchanged and green.
- `backend/tests/attachments/test_attachment_integrity_persistence.py` (*real DB*, runtime role,
  pattern of `test_failure_audit_row_persists_after_502`):
  - `test_failure_audit_row_persists_after_storage_error`: `get_object` raises → 500; in a fresh session
    exactly one `ATTACHMENT_ACCESS` FAILURE row for the id and the actor;
  - `test_failure_audit_row_persists_when_response_cannot_be_built`: helper monkeypatched to raise → 500;
    exactly one FAILURE row and no SUCCESS row for the id;
  - `test_non_latin1_name_downloads_and_commits_success_row`: stored name `résumé 患者 #1.txt` → 200 and
    one committed SUCCESS row.
  Each test cleans `audit_log` with the owner connection, as the existing test does.

Negative controls (record the results in this task):

1. Run the new router and real-DB file-name tests against the current router: they fail with 500
   (`UnicodeEncodeError`), which reproduces PRB-063.
2. Remove the `try/except` in `fetch_attachment`: `test_failure_audit_row_persists_when_response_cannot_be_built`
   fails (no row).
3. Make `record_access_failure` record SUCCESS instead of FAILURE: the real-DB storage-error test fails
   (the row is rolled back with the request).
4. Revert step 1 of the helper (controls kept): the CR/LF test fails.

## Acceptance criteria

- [x] **AC-1 (SR-013 AC 3, PRB-063):** an attachment whose file name contains characters outside Latin-1
      downloads with 200, identical bytes, and `Content-Disposition: attachment; filename="<ASCII
      fallback>"; filename*=UTF-8''<percent-encoded UTF-8>` per RFC 6266/5987, for at least
      `résumé 患者 #1.txt` and `report’s summary.pdf`
      (`backend/tests/api/test_content_disposition.py`,
      `backend/tests/api/test_attachments_router.py::TestFetchAttachmentFileNames`,
      `backend/tests/attachments/test_attachment_integrity_persistence.py::test_non_latin1_name_downloads_and_commits_success_row`).
- [x] **AC-2 (SR-013 AC 3, header integrity):** a name containing `"`, `\`, CR, LF or any other control
      character produces exactly one well-formed, pure-ASCII `Content-Disposition` header and no other
      header; no file under `backend/app` or `backend/modules` builds the header except through the helper
      (`backend/tests/api/test_content_disposition.py`, including
      `test_content_disposition_is_built_only_by_the_helper`;
      `backend/tests/api/test_attachments_router.py::TestFetchAttachmentFileNames`).
- [x] **AC-3 (SR-023 AC 2, ADR-0016):** a download of an authorized, existing attachment that fails on the
      server (storage error, missing object, checksum mismatch, or a failure while building the response)
      leaves exactly one committed `ATTACHMENT_ACCESS` FAILURE row for the attachment and the actor, still
      present after the error response
      (`backend/tests/attachments/test_attachment_fetch.py`,
      `backend/tests/api/test_attachments_router.py::TestFetchAttachmentFileNames::test_response_build_failure_records_access_failure`,
      `backend/tests/attachments/test_attachment_integrity_persistence.py` *real DB*; TC-007.6 to TC-007.8
      unchanged and green).

## Verification

```sh
cd backend && uv run pytest tests/api/test_content_disposition.py tests/api/test_attachments_router.py tests/attachments -v
cd backend && uv run pytest modules/dicom_viewer/tests -v
cd backend && uv run pytest --cov=app --cov-fail-under=85 && uv run ruff check . && uv run mypy app
cd frontend && npm test -- --run src/core/clinical
```

The real-DB tests in `test_attachment_integrity_persistence.py` need Docker (testcontainers PostgreSQL 16).
No object-store test is needed: the defect is in header construction, which happens before any byte is
sent and is identical under the in-memory fake and SeaweedFS.

**Started-stack check** (needed: PRB-063 was observed on a started stack, and the check covers gunicorn,
uvicorn and the nginx proxy in the path). Recorded in this task:

1. `docker compose -f infra/docker-compose.yml up -d --build` from the current template (DEPLOY.md).
2. As a doctor with consent, upload `résumé 患者 #1.txt` and `report’s summary.pdf` to a clinical entry
   through the proxy.
3. `curl -sS -D - -o out.bin -b <session> https://<host>/api/v1/attachments/<id>` for each: status 200,
   the header of the table, `sha256sum out.bin` equals the uploaded file's.
4. In a browser (Chrome and Firefox at least), click "Download" in the clinical entry view: the saved
   file is named `résumé 患者 #1.txt` / `report’s summary.pdf`.
5. `audit_log` holds an `ATTACHMENT_ACCESS` SUCCESS row per download with the client address, not the
   proxy's.

## Records

- **TS-007** 1.4 → 1.5 (content change: approval cleared, back to `in_review`): TC-007.9 (file names
  outside Latin-1 and header integrity, AC-1, AC-2, `verifies` SR-013) and TC-007.10 (server-side
  download failure audited and committed, AC-3, `verifies` SR-013 and adds `verifies` SR-023). Update the
  "Preconditions and environment" build line to `fix/review-2026-07-security` (CR-004) for TC-007.9 and
  TC-007.10. Fault-handling acceptance criterion extended: a failed download is never unaudited.
- **ADD-012** 1.3 → 1.4 (`in_review`): `U-ATT-Fetch` records an `ATTACHMENT_ACCESS` FAILURE on every
  server-side failure after authorization (not only a checksum mismatch). ADD-005 needs no change: the
  helper is part of `U-API-Routers`. The arc42 narrative, if any sentence describes the download header,
  is TASK-201's.
- **RISK-007** 1.5 → 1.6 (`in_review`): cause "a stored file name that cannot be represented in an HTTP
  header makes the attachment undownloadable (PRB-063)" added to the sequence of events, and one control
  row: "File names encoded per RFC 6266/5987 with an ASCII fallback; the header is built in one place |
  Design | SR-013 AC 3; TASK-204 | TS-007 TC-007.9". Residual unchanged (3 × 2, `alarp`); this cause was
  never part of the scored estimate.
- **RISK-006**: no record change. The FAILURE row on a failed download is an instance of the existing
  ADR-0016 control row, verified by TC-007.10.
- **PRB-063**: `## Investigation` (the survey above: one header builder, DICOM route unaffected, no
  frontend parsing) and `## Resolution` (this task, commit). Status `resolved` on QA approval (CR-004
  D-8). Fix the frontmatter `version`, which says `"1.0"` while the history records 1.1.
- **SOUP**: none touched (standard library only; Starlette's header encoding is the behaviour relied on
  and is not changed).

## Definition of Done

- [x] AC-1 to AC-3 met; the four negative controls recorded.
- [x] Backend suite passes with coverage ≥ 85 %; DICOM-module and frontend suites green; `ruff` and
      `mypy` clean.
- [ ] Started-stack check recorded (steps 1 to 5).
- [x] TS-007 1.5, ADD-012 1.4 and RISK-007 1.6 `in_review`.
- [x] On QA approval: this task `approved`, PRB-063 `resolved` (CR-004 D-8). `closed` stays the human's
      step at release.
- [x] `traceability-check` shows no error for TASK-204, TS-007, SR-013, SR-023, ADD-012, RISK-007,
      PRB-063.
- [ ] `graphify update .` run after the code change.

## Implementation notes (Software Developer, 2026-11-06)

- Files: `backend/app/api/content_disposition.py` (new); `backend/app/api/routers/attachments.py`;
  `backend/app/attachments/service.py`; tests `backend/tests/api/test_content_disposition.py` (new),
  `backend/tests/api/test_attachments_router.py`, `backend/tests/attachments/test_attachment_fetch.py`,
  `backend/tests/attachments/test_attachment_integrity_persistence.py`. No change to `audit/service.py`:
  `target_type="attachment"` with the id is an existing shape.
- The worked-examples table was confirmed against the implementation unchanged.
- The persistence tests share a `_download` helper and `_rows_and_clean`; the existing 502 test keeps its name.

### Negative controls (results)

1. Pre-fix router, `résumé 患者 #1.txt` and `report’s summary.pdf`: HTTP 500 in the router tests and in
   the real-DB `test_non_latin1_name_downloads_and_commits_success_row`;
   `UnicodeEncodeError: 'latin-1' codec can't encode characters in position 29-30` reproduced directly.
2. `try/except` in `fetch_attachment` removed: `test_failure_audit_row_persists_when_response_cannot_be_built`
   and `test_response_build_failure_records_access_failure` fail.
3. `record_access_failure` records SUCCESS: the real-DB `test_failure_audit_row_persists_after_storage_error`
   fails (also the 502 persistence test and four unit tests).
4. Control-character step of the helper reverted: 5 tests in `test_content_disposition.py` fail, including the
   CR/LF worked example and `test_crlf_replaced_so_no_header_can_be_injected`.

### Started-stack check (scratch project `task204`, scratch env file, `infra/.env` untouched)

1. `db-migrate` via `up --build --exit-code-from db-migrate db-migrate` (exit 0), then `up -d --build`: all
   services up, backend healthy.
2. A doctor and a patient (generated password) created inside the backend container; the patient granted the
   doctor MANUAL consent; the doctor created a clinical entry and uploaded both files through
   `https://localhost` (nginx).
3. `curl -D -` for each: 200; `résumé 患者 #1.txt` gives
   `attachment; filename="resume __ #1.txt"; filename*=UTF-8''r%C3%A9sum%C3%A9%20%E6%82%A3%E8%80%85%20%231.txt`;
   `report’s summary.pdf` gives
   `attachment; filename="report_s summary.pdf"; filename*=UTF-8''report%E2%80%99s%20summary.pdf`.
   SHA-256 of the downloaded bytes equals the uploaded file for both
   (`c9909ba5...9c39452`, `2d225852...f62df0`).
4. Browser saved name: **not checked** (no headless browser session was available; Firefox is installed
   but was not driven). Only the header was verified, not the name a browser saves.
5. `audit_log`: one `ATTACHMENT_ACCESS` SUCCESS row per download with `ip` 172.28.77.128 (the Docker Desktop
   gateway the proxy saw as client), not the proxy's 172.28.77.2. Extra: with `object-store` stopped the
   download answered 500 and one `ATTACHMENT_ACCESS` FAILURE row with the same client address was committed.
6. Teardown: `down -v --remove-orphans`; `task204-*` images removed; no container, volume or network left
   (`peaceful_pike` untouched); `infra/.env` SHA-256 identical before and after.

## QA review (QA Engineer, 2026-11-06)

**Verdict: APPROVED.** No CRITICAL or HIGH finding. The started-stack DoD item stays unticked only
because the browser step was checked in Firefox against a header server, not in Chrome on the stack
(item C-2).

Verification:
- Targeted 59 passed. DICOM module 25 passed. Full backend suite 1467 passed and 6 skipped, coverage
  94.41 %. TASK-138's tests did not fail in this run. Frontend 209 passed. `ruff check .` and `mypy app`
  clean; `ruff` and `black --check` clean on the 7 TASK-204 files.
- Fuzz: 200,000 random names (C0/C1 controls, lone surrogates, `Cf`, `Zl`, astral characters,
  U+FDFA). Every value is ASCII with no CR or LF and has exactly the shape `attachment; filename="…";
  filename*=UTF-8''…`. The fallback is printable ASCII without `"` or `\`. `filename*` contains only
  attr-char plus `%HH`, and `unquote` and `email.message` with `collapse_rfc2231_value` both return the
  name with Cc/Cs mapped to `_`. Starlette `Response` accepts every value. 0 failures.
- Audit probes (real PostgreSQL, runtime role): storage error gives 500 with one FAILURE row, `ip` set.
  Checksum mismatch gives 502 with one FAILURE row, `ip` set. Success gives one SUCCESS row, `ip` set.
  A denial writes only `AUTHZ_DENIED`, with no `ATTACHMENT_ACCESS` and no storage read. A missing row
  writes nothing.
- Mutation controls (pytest plugins, tree untouched):
  - old f-string header: 4 tests fail.
  - `record_access_failure` made a no-op: 8 fail.
  - fallback returns the raw name: 15 fail.
- Browser: headless Firefox 159.0.1 against a local server that sends the helper's header saved
  `résumé 患者 #1.txt`, `report’s summary.pdf` and `患者.txt` (content identical). It used `filename*`:
  `é‮gpj.exe` was saved as `é_gpj.exe`, so Firefox replaces the bidi override itself.
- `traceability-check` (fallback parser) for TASK-204, TS-007, ADD-012, RISK-007, PRB-063, SR-013,
  SR-023 and CR-004: 0 errors, 1 warning (W5: SR-023 approved and linked to RISK-005, which is
  `in_review`; not from this task).

Findings (not blocking):
1. **MEDIUM: no length bound, and the fallback can grow 18×.** `backend/app/api/content_disposition.py:21-31,34-38`
   produces values up to ~10 KB, for example 255 × U+FDFA gives 6,927 bytes. NFKD expands one character
   into up to 18 fallback characters, and the stored name is unbounded (`backend/app/api/routers/attachments.py:60`,
   `Attachment.filename` with no length limit). Behind nginx 1.31.8 with the default
   `proxy_buffer_size` of 4 KB (`infra/reverse-proxy/nginx.conf:31-37`), a header of 4,042 bytes or more
   returns **502 "upstream sent too big header"**. Reproduced with 400 CJK characters and with
   255 × U+FDFA; 255 CJK characters (2,592 bytes) and 255 emoji (3,357 bytes) still pass. The backend has
   already committed the SUCCESS row by then. Names taken from real file systems (≤ 255 units) pass, so
   only API-crafted or unusual names are affected.
   → Truncate the ASCII fallback to a fixed length, for example 150 characters keeping the extension,
   and bound the stored name at upload (for example 255 UTF-8 bytes, which matches SR-013), or drop
   `filename*` above a byte budget. Carry as a new PRB, or as an item of TASK-201/202. Orchestrator
   to decide.
2. **LOW: the FAILURE row's address is not asserted.** `backend/tests/attachments/test_attachment_integrity_persistence.py:130,142,157`
   checks outcome, action and actor but not `ip`, although SR-023 AC 6 relies on it. The QA probe shows
   `ip == "testclient"`. → Add `assert rows[0].ip == "testclient"` to the three FAILURE tests.
3. **LOW: bidi and format characters (`Cf`, for example U+202E) are kept in `filename*`.** Firefox
   replaces them with `_` when saving; Chrome, Safari and Edge are not verified. → Check this at TASK-202
   (C-2). If a browser keeps them, map `Cf` to `_` in `_neutralise_controls` as well.

Observations:
- The `try/except` in `fetch_attachment` cannot fire in practice: the helper never raises, and the
  value is ASCII. The task kept it on purpose and it is tested.
- `disposition="inline"` has no production caller. The DICOM route builds a plain `Response` with no
  `Content-Disposition`. The static scan of `backend/app` and `backend/modules` holds: there is no other
  `StreamingResponse` or `FileResponse`.

Carried to TASK-202:
- C-1: finding 1, unless a PRB is raised.
- C-2: saved file name in Chrome (and Safari/Edge if available) through "Download" on a started stack,
  including a name with U+202E.

## Version history

- 1.0 (2026-11-02) — Created by the Software Architect role for PRB-063 (CR-004 D-9). `draft`.
- 1.1 (2026-11-06) — Implemented by the Software Developer role; `in_review`. Notes and negative-control results added.
- 1.2 (2026-11-06) — QA review: APPROVED (1 MEDIUM, 2 LOW, not blocking; C-1 and C-2 carried to TASK-202). `approved`.
