---
id: "PRB-074"
type: problem-report
title: "Activation tokens, retrieval codes and an erased user's e-mail sit in plaintext in Redis as task arguments"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-11-07"
updated: "2026-11-07"
criticality: major
links: []
tags: ["credentials", "privacy", "hazard:security", "found-in:CR-004-Q-9"]
---

# PRB-074 — Activation tokens, retrieval codes and an erased user's e-mail sit in plaintext in Redis as task arguments

## Observed

Raised by CR-004 Q-9 (Plan stage, 2026-10-31) from the code. Two tasks receive secrets as Celery arguments:
the activation e-mail gets the raw activation token, and the erasure e-mail gets the raw retrieval code and
the erased user's e-mail address. The messages go through the Redis broker without encryption. The content
of Redis and its append-only file was not inspected for this report: the statements below come from the code
and the Compose file.

## Impact

Whoever can read Redis, its `redis_data` volume or a copy of that volume can read:

- **activation tokens:** with the account id, set the password of a pending account during its 72-hour
  validity (RISK-005, the same harm as PRB-068);
- **retrieval codes:** retrieve the anonymized dataset (ADR-0013). The application stores no raw code;
- **the erased user's e-mail address:** personal data that survives outside the erasure machinery after
  the person was erased (RISK-008).

This is not a log, so SR-043 does not apply directly; AC 4 applies by analogy. No requirement covers
credentials at rest in the broker. The application otherwise keeps only a hash of the activation token
(`backend/app/identity/activation.py:41`).

## Investigation

- `backend/app/identity/account_service.py:109` and `backend/app/identity/activation.py:144`:
  `send_activation_email.delay(str(account.id), raw_token)`. Task at
  `backend/app/workers/email_tasks.py:79`.
- `backend/app/identity/erasure.py:140`: `send_erasure_code_email.delay(original_email, raw_code)`. Task at
  `email_tasks.py:142`. The comment at `erasure.py:136` says the code is "discarded after sending — never
  persisted", which does not hold for the broker.
- `backend/app/workers/celery_app.py:44-53`: Redis as broker, JSON serializer, no message encryption, and
  `task_acks_late=True`, so a message also stays in Redis while it runs. `autoretry_for=(Exception,)` keeps it
  there across retries, and with no worker running it waits indefinitely.
- `infra/docker-compose.yml:190-198`: `redis-server --appendonly yes` on the `redis_data` volume, with no
  `requirepass`, and `REDIS_URL` has no credential (`:77`, `infra/.env.example:34`). Redis is reachable only on the
  internal `medhub` network (`expose`, no `ports`). With an append-only file, a message stays on disk after
  it is consumed, until the next rewrite of the file. It is plaintext unless the volume is encrypted.
- Result backend: CR-004 Q-9 also names it, but `result_extended` is not set, so task metas hold no
  arguments. No PRB-worthy copy there, and TASK-207 stops writing them.
- The log side is closed: TASK-138 redacts `args`, `kwargs` and `argsrepr` in Celery's records.
- Root cause: secrets are passed by value through a store that is not meant to hold them.

Fix directions for the later CR: pass ids only and keep the secret in the database encrypted with the
field-encryption key (ADR-0018) until the task reads it; or encrypt the arguments with that key; and decide
whether to keep the append-only file or add Redis authentication.

## Safety evaluation

Confidentiality: a credential and personal data at rest in plaintext. Harm is the same as PRB-068 (RISK-005,
severity 3) plus a retention failure against erasure (RISK-008). It needs access to the internal network, the
host or a volume copy, so it is not `critical`. Criticality **major**, above the `minor` that Q-9 recommended,
because the append-only file keeps these values on disk after delivery, and an erased person's e-mail
address outliving the erasure is a data-protection failure. No release exists (CR-004 A-1), so no notification
is needed. The human sets the final criticality.

## Resolution

Not fixed. Known anomaly outside CR-004 (D-18). It has no `resolves` link yet.

## Source

CR-004 Q-9; human decision 2026-11-07 (CR-004 D-18).

## Version history

- 1.0 (2026-11-07) — Created from CR-004 Q-9. `open`, `major`.
