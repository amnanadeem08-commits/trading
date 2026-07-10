"""Notification scaffolds."""

from notifications.events import (
    NotificationChannel,
    NotificationEvent,
    NotificationResult,
    NotificationSeverity,
)
from notifications.manager import NotificationManager
from notifications.providers import (
    EmailProvider,
    NotificationProvider,
    SlackProvider,
    WebhookProvider,
)

__all__ = [
    "EmailProvider",
    "NotificationChannel",
    "NotificationEvent",
    "NotificationManager",
    "NotificationProvider",
    "NotificationResult",
    "NotificationSeverity",
    "SlackProvider",
    "WebhookProvider",
]
