"""Notification event contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class NotificationChannel(StrEnum):
    """Supported notification channels."""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


class NotificationSeverity(StrEnum):
    """Notification severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationEvent(PlatformModel):
    """Immutable notification event contract."""

    event_id: str = Field(min_length=1)
    channel: NotificationChannel
    severity: NotificationSeverity
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)
    recipient: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: UTCDateTime = Field(default_factory=utc_now)


class NotificationResult(PlatformModel):
    """Result of a notification delivery attempt."""

    event_id: str = Field(min_length=1)
    success: bool
    message: str = Field(min_length=1)
    delivered_at: UTCDateTime = Field(default_factory=utc_now)
