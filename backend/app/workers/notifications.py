"""Notification abstraction (TASK-031).

Wraps the concept of a notification in flight: channel, recipient,
status, and an optional post-send hook.
"""

from __future__ import annotations

import enum
from collections.abc import Callable
from dataclasses import dataclass, field


class NotificationChannel(enum.Enum):
    EMAIL = "EMAIL"


class NotificationStatus(enum.Enum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    FAILED = "FAILED"


@dataclass
class Notification:
    channel: NotificationChannel
    recipient: str
    subject: str
    body: str
    status: NotificationStatus = NotificationStatus.QUEUED
    post_send_hook: Callable[[], None] | None = field(default=None, repr=False)

    def mark_sent(self) -> None:
        self.status = NotificationStatus.SENT
        if self.post_send_hook is not None:
            self.post_send_hook()

    def mark_failed(self) -> None:
        self.status = NotificationStatus.FAILED
