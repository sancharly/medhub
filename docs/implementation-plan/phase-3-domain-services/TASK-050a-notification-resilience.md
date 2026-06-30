# TASK-050a — Appointment notification resilience (remediation)

- **Phase:** 3 — Domain services
- **Implements / restores:** SR-035.1–2; remediates TASK-050
- **Depends on:** TASK-050
- **Branch:** `feature/notification-resilience`
- **Status:** Completed
- **Source:** `AUDIT-LEDGER.md` — TASK-050 verdict **PARTIAL**

## Objective

In `send_appointment_notification`, the SMTP send runs **before** the in-app notification row is
written, so an email failure raises/retries and the in-app notification is **never recorded** — the
opposite of the dual-channel resilience the AC requires. Email failure also never marks the notification
`FAILED`.

## Implementation detail

- Write the in-app `InAppNotification` row **first**; then attempt `_send_smtp`. On send failure, mark
  the in-app notification `status=FAILED` (use the existing `mark_failed`) without losing the in-app record.
- Add a real assertion that the notify task is enqueued exactly once after commit (the current test only
  checks `repo.add.called`).

## Acceptance criteria

- [x] Email-send failure does not roll back / suppress the in-app notification (it is recorded, marked FAILED).
- [x] The in-app notification content (recipient, appointment, datetime) is correct and contains no clinical data.
- [x] The notify task is enqueued exactly once after commit (asserted).

## Definition of Done

- [x] Lint + type-check pass
- [x] Tests cover email-failure → in-app still recorded (FAILED), and enqueue-once
- [x] Traceability row updated (SR-035 → TASK-050a → tests)
- [x] Security review N/A
