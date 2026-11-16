---
id: "PRB-083"
type: problem-report
title: "Erasure e-mail is sent for an erasure that did not commit"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-14"
updated: "2026-11-14"
criticality: minor
links: []
tags: ["reliability", "privacy", "hazard:privacy", "found-in:TASK-141-qa"]
---

# PRB-083 — Erasure e-mail is sent for an erasure that did not commit

## Observed

Found by QA in the TASK-141 review (2026-11-14, LOW finding 1). Since TASK-141, `ErasureService._erase` enqueues
the retrieval-code e-mail before anything outside the database changes (`backend/app/identity/erasure.py:120-135`),
so that a failed enqueue rolls the whole erasure back (SR-024 AC 6). If a later step fails after a successful
enqueue, the worker still sends "Your MedHub account has been erased per your request." with a retrieval code
(`backend/app/workers/email_tasks.py:142-173`, text at `:152`), although the erasure was rolled back and the
requester received a 5xx. CR-006 cause 6, RISK-008 "Risks introduced by controls" and TS-004 TC-004.4 call this
case "harmless".

## Impact

The data subject is told that their account was erased when it was not. The code in the e-mail matches no
dataset. No data is lost or disclosed; a retry by the requester performs the erasure and sends a second, valid
code, so the subject may hold two codes of which only the second works.

## Investigation

Order inside the request (one transaction, `DbSession` with `scope="function"`, committed before the response by
TASK-227 / ADR-0023):

1. PII severed and `AnonymizedDataset` added; the repository flushes (`erasure.py:97-118`), so constraint errors
   surface before the enqueue.
2. `send_erasure_code_email.delay(original_email, raw_code)` (`erasure.py:128`).
3. `self._session_svc.invalidate_all(account_id)` (Redis, `erasure.py:138`; `auth/session.py:233-240`).
4. Two SUCCESS audit inserts (`erasure.py:140-155`).
5. Commit by the `get_db` dependency teardown (`backend/app/db/repositories/session.py`).

Steps 3 to 5 can fail after step 2. The worker task takes only the address and the code and reads no database
row (`email_tasks.py:142-173`), so it cannot tell a committed erasure from a rolled-back one. The order itself is
correct and stays: enqueuing after the commit can lose the code of a committed erasure (forbidden by SR-024
AC 6), and a transactional outbox would persist the raw code (forbidden by SR-024: the raw value is never
stored). The broken assumption is the "harmless" reading of the converse case. Root cause: the e-mail is not
bound to the outcome of the transaction it reports.

## Safety evaluation

No safety-related function or clinical decision is affected; no clinical or personal data is altered, lost or
disclosed. The effect is a false statement to the data subject about the state of their personal data (RISK-008,
privacy and GDPR accountability), corrected only when the requester retries. Reaching it needs a Redis, audit
insert or commit failure inside the few milliseconds after a successful enqueue. Criticality **minor**. No
release exists (CR-004 A-1), so no installation is affected and no notification is needed. The human sets the
final criticality.

## Resolution

Fixed by TASK-228 (CR-006 D-30). The enqueue stays where TASK-141 put it (before `invalidate_all`, inside the
request transaction), so a failed enqueue still rolls the erasure back and no committed erasure loses its code.
What changed:

- `backend/app/identity/erasure.py`: `send_erasure_code_email.delay(original_email, raw_code, str(dataset.id))`;
  the comment no longer calls the converse case "harmless".
- `backend/app/workers/email_tasks.py`: `send_erasure_code_email` reads the `anonymized_dataset` row with that id
  (`_erasure_committed`, own session, closed on every path) before sending. The row is visible to the worker only
  once the erasure's transaction has committed. Absent: `self.retry` up to 14 times (countdown 2, 4, 8, 16, 32 s,
  then 60 s; about 10 minutes; `commit_checks` kept apart from the 3 SMTP retries, which are now an explicit
  `try/except`); absent at the last check: no e-mail, one WARNING with the dataset id only; the check cannot be
  made at the last check: the e-mail is sent with a WARNING (a lost code for a committed erasure is worse).

Why this approach: enqueue after the commit can lose the code of a committed erasure (SR-024 AC 6); a transactional
outbox would store the raw code (SR-024); polling with `sleep` holds a worker slot.

Verified (working tree, 2026-11-14): `backend/tests/workers/test_erasure_code_email_gate.py` (7 tests plus the log
test, one on real PostgreSQL: an open erasure transaction is reported absent, present after the commit),
`backend/tests/workers/test_email_tasks_logging.py`, `backend/tests/identity/test_erasure.py`,
`backend/tests/api/test_erasure_rollback.py` (TC-004.4 unchanged); backend suite 1684 passed, 10 skipped. Negative
control: replacing the check with `True` fails 9 of the gate tests, among them
`test_drops_the_e_mail_when_the_erasure_never_commits`. Reproduce:
`cd backend && uv run pytest tests/workers/test_erasure_code_email_gate.py`. Accepted residual (human, CR-006 P-16):
an erasure that commits more than about 10 minutes after its enqueue has its code dropped (RISK-008 row, cause 14).

## Version history

- 1.0 (2026-11-14) — Created from the TASK-141 QA review (LOW 1) on the human's decision to fix it inside
  CR-006. `open`, `minor`.
- 1.1 (2026-11-14) — Resolved by TASK-228; Resolution written. Awaiting QA confirmation of the verification. `resolved`, `minor`.
