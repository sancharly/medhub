# TASK-050 — Appointment notification dispatch

- **Phase:** 3 — Domain services
- **Software item / unit:** SI-APPT / U-APPT-Notify
- **Implements:** SR-035 (AC-2 notify immediately on create, AC-3 dual-channel in-app + email)
- **Depends on:** TASK-047 (appointment create), TASK-031 (Celery worker / `SI-WORKER` task interface + SMTP email task) — must be merged first
- **Branch:** `feature/appointment-notify`
- **Status:** Completed

## Objective

On appointment creation, notify the associated patient through two channels — an in-application notification visible in the patient's appointment view and an email to the registered address — best-effort. Dispatch is funneled through a single `Notification` abstraction with a `status` field and a post-send hook (the documented MVP extension point, §8.12) so delivery/read tracking can be added later without changing callers. Traces to SR-035 criteria 2 and 3.

## Interfaces to honor

Consumes the `SI-WORKER` task interface from [12-interfaces.md](../../design/12-interfaces.md) §12.1:

```python
def send_appointment_notification(appointment_id: UUID) -> None: ...   # Celery task (SR-035)
```

- Per §8.12, dispatch goes through a `Notification` abstraction carrying `status` (`QUEUED` | `SENT` | `FAILED`) and a post-send hook; the MVP only sets `status`, performs **no** delivery/read acknowledgement, and relies on Celery retries (section 11). The single abstraction is the extension point — callers (this unit) **must not** be changed when delivery tracking is later added.
- Only `SI-AUTH`/`SI-WORKER` talk to Redis (§12.3 rule 3); enqueueing uses the Celery/Redis broker via the worker interface, not a direct Redis call from SI-APPT.
- Notification carries no clinical data — only doctor name, scheduled datetime, and a link/path to the appointment view (SR-035 AC-2), keeping it within the admin/scheduling privacy boundary (SR-010 AC-4).

## Implementation detail

- Files to create / modify:
  - `backend/app/appointments/service.py` — in `create` (TASK-047), after commit, enqueue `send_appointment_notification(appointment.id)`. Enqueue **after** the DB commit so the task always finds the row.
  - `backend/app/appointments/notification.py` — the `Notification` abstraction: `Notification(channel, recipient, payload, status, post_send_hook)`; `status` enum `QUEUED|SENT|FAILED`; a no-op `post_send_hook` default (the §8.12 extension seam).
  - `backend/app/db/models/notification.py` — in-app `Notification` row (recipient account, appointment id, message, `status`, `created_at`, `read_at` nullable — `read_at` reserved, not tracked in MVP) so it is visible in the patient appointment view (SR-035 AC-3 in-app channel).
  - `backend/app/workers/tasks/appointment_notification.py` — Celery task: load appointment + patient, write the in-app notification row, render and send the email via the `U-WK-Email` SMTP task (TASK-031); set `status`/`FAILED` and invoke `post_send_hook`.
  - `backend/app/db/alembic/versions/<rev>_notification.py` — migration.
- Notification content (SR-035 AC-2): doctor's name, scheduled date/time, direct link/path to the appointment view. No clinical content.
- Config keys: SMTP settings inherited from TASK-031 (env-injected, NFR-007); `APP_BASE_URL` for the appointment link.
- Audit: notification dispatch is operational, not security-relevant per SR-023's list; do not over-audit. (The appointment create audit is TASK-047.)
- Error cases: email send failure → Celery retry (best-effort, §8.12); after retries exhausted, `status=FAILED` recorded, but appointment creation is **not** rolled back (notification is best-effort, decoupled from the create transaction). The in-app notification is written even if email fails, so the patient still sees it in-app (dual-channel resilience, SR-035 AC-3).
- Edge cases: enqueue is fire-and-forget from the request path so appointment creation latency is unaffected (SR-026); a missing/blank patient email still produces the in-app notification and marks email `FAILED`.

## Tests (write first — TDD, CLAUDE.md §4)

- Unit (`backend/tests/appointments/test_notify.py`):
  - `create` enqueues `send_appointment_notification` exactly once, after commit (SR-035 AC-2).
  - the task writes an in-app `Notification` row for the patient with doctor name, datetime, and appointment link (SR-035 AC-2/AC-3 in-app).
  - the task sends an email to the patient's registered address (SR-035 AC-3 email) — assert the SMTP/email task is invoked with the right recipient/content.
  - notification payload contains **no** clinical data (privacy boundary).
  - email send failure → `status=FAILED`, in-app notification still written, appointment not rolled back (best-effort, §8.12).
  - `Notification` abstraction exposes `status` and `post_send_hook`; hook is invoked post-send (§8.12 extension point).
- Integration (`backend/tests/api/test_appointment_notify_api.py`): `POST /appointments` results (via eager/synchronous Celery in tests) in an in-app notification row and a captured outbound email.

## Acceptance criteria

- [ ] Immediately after creation, the patient is notified (SR-035 AC-2).
- [ ] The notification includes the doctor's name, scheduled date/time, and a link to the appointment view (SR-035 AC-2).
- [ ] Notification is dual-channel: an in-app notification in the appointment view and an email to the registered address (SR-035 AC-3).
- [ ] Dispatch is best-effort via the `Notification` abstraction with `status` + post-send hook; no delivery tracking in MVP (§8.12).
- [ ] Email failure does not roll back appointment creation; the in-app notification is still recorded.

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit + integration tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (in-app notifications surfaced via appointment view DTO)
- [ ] Audit events emitted for security-relevant actions (N/A — notification dispatch is operational; create audit in TASK-047)
- [ ] Traceability matrix row updated (SR-035 AC-2/AC-3 → TASK-050 → tests)
- [ ] Security review N/A (no auth/session/authz code)
