---
id: "TASK-031"
type: task
title: "Celery base + email tasks"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-07"
updated: "2026-07-07"
links:
  - target: "SR-033"
    relation: implements
  - target: "SR-035"
    relation: implements
  - target: "TASK-003"
    relation: relates_to
  - target: "TASK-012"
    relation: relates_to
tags: ["audit-verified", "phase:2-auth-session-authorization-identity"]
---

- **Phase:** 2 — Auth, session, authorization, identity, worker base
- **Software item / unit:** SI-WORKER / U-WK-Email
- **Implements:** SR-033 (activation email), SR-035 (appointment notification email); §8.12
  (best-effort `Notification` abstraction with `status` + post-send hook)
- **Depends on:** TASK-003 (config & secrets — SMTP/Redis), TASK-012 (repositories)
- **Branch:** `feature/worker-email`
- **Status:** Completed (audit-verified 2026-06-29)

## Objective

Stand up the Celery worker base (Redis broker, ADR-0002) and the two email tasks the identity and
appointment flows enqueue: `send_activation_email` and `send_appointment_notification`. Delivery
is **best-effort** for the MVP (§8.12): the system sends and relies on Celery retries, performs no
delivery/read tracking, but routes every send through a single `Notification` abstraction carrying
a `status ∈ {QUEUED, SENT, FAILED}` and a post-send hook — the clean extension point for future
delivery receipts without changing callers (§8.12, SR-035). This is the async substrate reused by
session-kill (TASK-034) and retention-erase (TASK-036).

## Interfaces to honor

Provided task interface (from [12-interfaces.md](../../design/12-interfaces.md), SI-WORKER), the
email subset (signatures verbatim):

```python
def send_activation_email(account_id: UUID, activation_token: str) -> None: ...
def send_appointment_notification(appointment_id: UUID) -> None: ...
# propagate_session_kill(account_id) is TASK-034
```

These are Celery task callables enqueued (`.delay(...)`) by `AccountService` (TASK-030/032) and
`AppointmentService` `U-APPT-Notify` (TASK-050). Consumes SMTP config (TASK-003) and the account/
appointment repositories (TASK-012). Email send goes through the `Notification` abstraction.

Must **not**: be on the request's critical path (enqueue-and-return; best-effort, §8.12); block an
operation on delivery success (SR-035 requires sending, not delivery proof); embed secrets in code
(SMTP creds from env, TASK-003); leak the raw activation token into logs/audit (the token is in the
email body only; audit records "link sent", not the token — SR-033.9).

## Implementation detail

- Files to create:
  - `backend/app/workers/celery_app.py` — Celery app, Redis broker/result backend (ADR-0002),
    task autodiscovery, retry defaults.
  - `backend/app/workers/email_tasks.py` — `send_activation_email`, `send_appointment_notification`.
  - `backend/app/workers/notifications.py` — `Notification` abstraction (`status`,
    `post_send_hook`) per §8.12.
  - `backend/app/workers/email_renderer.py` — template rendering for the two emails.
- Celery base: broker + result backend = Redis (the same instance, ADR-0002/0012); task
  serialization JSON; idempotent tasks keyed by `account_id`/`appointment_id`; bounded retries
  (`max_retries`, exponential backoff) — best-effort delivery (§8.12, section 11 retries).
- `Notification` abstraction (§8.12): a small object/record carrying `channel` (EMAIL/IN_APP),
  `recipient`, `status ∈ {QUEUED, SENT, FAILED}`, and a `post_send_hook(notification)` invoked after
  the send attempt. MVP only sets `status`; the hook is the documented extension point for future
  delivery/read tracking — callers never change (§8.12). (In-app appointment notification record is
  created by `U-APPT-Notify`, TASK-050; this task owns the email channel and the abstraction.)
- `send_activation_email`: load account, render the activation email containing the single-use 72 h
  link built from `activation_token` (token issuance is TASK-032), send via SMTP, set
  `status=SENT|FAILED`, run the post-send hook. Audit `ACTIVATION_LINK_SENT` (account email + ts,
  **not** the token — SR-033.9).
- `send_appointment_notification`: load the appointment, render the patient email with doctor name,
  date/time, and a link/path to the appointment view (SR-035.2/3), send, set status, run hook.
- SMTP: `smtplib`/`aiosmtplib` (sync within the Celery worker is acceptable); host/port/creds/TLS
  from config keys `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`,
  `MAIL_FROM`, `PUBLIC_BASE_URL` (for link building) (TASK-003, 12-factor).
- Error cases: SMTP failure → Celery retry up to the cap, then `status=FAILED` (best-effort; no
  user-facing error since it is off the request path); a missing account/appointment → task logs
  and exits (no retry storm).

## Tests (write first — TDD, CLAUDE.md §4)

Run tasks eagerly (`task_always_eager`) with a mocked SMTP transport.

- Unit (`backend/tests/workers/test_email_tasks.py`):
  - `send_activation_email` renders a body containing the 72 h activation link and the doctor/account
    context, sends once, sets `status=SENT`, runs the post-send hook (SR-033.1, §8.12).
  - The activation token never appears in logs or the audit record; `ACTIVATION_LINK_SENT` audits
    email + ts only (SR-033.9).
  - `send_appointment_notification` email contains doctor name, scheduled date/time, and the
    appointment link/path (SR-035.2/3).
  - SMTP failure triggers retry; after the cap, `status=FAILED` and the hook still runs; the caller
    is never blocked (best-effort, §8.12).
  - `Notification.status` transitions QUEUED → SENT / FAILED; the post-send hook is the only place
    delivery state is observed (extension-point contract, §8.12).
- Integration (`backend/tests/workers/test_celery_wiring.py`): the Celery app discovers the tasks and
  enqueues against a real/fake Redis broker (crosses the SI-WORKER↔Redis boundary).

## Acceptance criteria

Distilled from SR-033 / SR-035 / §8.12:

- [x] Celery worker runs against the Redis broker; tasks are autodiscovered and enqueueable (ADR-0002).
- [x] `send_activation_email` sends the single-use 72 h activation link; audited as link-sent without
      the token (SR-033.1, SR-033.9).
- [x] `send_appointment_notification` email carries doctor name, date/time, appointment link (SR-035.2/3).
- [x] Sends are best-effort with bounded retries; the request path is never blocked (§8.12).
- [x] All sends flow through the `Notification` abstraction with `status ∈ {QUEUED, SENT, FAILED}` and
      a post-send hook (extension point) (§8.12).
- [x] SMTP credentials and base URL come from env config, never committed (NFR-007, TASK-003).

## Definition of Done

- [x] Lint + type-check pass (`ruff`/`mypy`)
- [x] Unit (and required integration) tests pass; coverage target met
- [x] OpenAPI regenerated and re-linted (N/A — no HTTP endpoint)
- [x] Audit events emitted for security-relevant actions (ACTIVATION_LINK_SENT — SR-033.9; no token)
- [x] Traceability matrix row updated (SR-033, SR-035, §8.12 → TASK-031 → tests)
- [x] Security review completed (N/A — not auth/session/authz; verify no token/secret leakage)

## Audit verdict (2026-06-29)

- **Verdict:** PASS
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- Acceptance criteria verified met; boxes checked.
