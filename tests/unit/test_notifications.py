"""Unit tests for notification scaffolds."""

from __future__ import annotations

import pytest

from models.common import ContractViolationError
from notifications import (
    NotificationChannel,
    NotificationEvent,
    NotificationManager,
    NotificationResult,
    NotificationSeverity,
)


class _StubWebhookProvider:
    def send(self, event: NotificationEvent) -> NotificationResult:
        return NotificationResult(event_id=event.event_id, success=True, message="sent")


@pytest.mark.unit
def test_notification_manager_sends_via_provider() -> None:
    manager = NotificationManager(webhook=_StubWebhookProvider())  # type: ignore[arg-type]
    manager.register(NotificationChannel.WEBHOOK, _StubWebhookProvider())
    event = NotificationEvent(
        event_id="evt-1",
        channel=NotificationChannel.WEBHOOK,
        severity=NotificationSeverity.INFO,
        subject="Health",
        body="All healthy",
        recipient="https://example.com/hook",
    )
    result = manager.send(event)
    assert result.success is True


@pytest.mark.unit
def test_notification_manager_disabled() -> None:
    manager = NotificationManager(enabled=False)
    event = NotificationEvent(
        event_id="evt-2",
        channel=NotificationChannel.WEBHOOK,
        severity=NotificationSeverity.WARNING,
        subject="Alert",
        body="Degraded",
        recipient="https://example.com/hook",
    )
    result = manager.send(event)
    assert result.success is False


@pytest.mark.unit
def test_notification_manager_missing_provider_raises() -> None:
    manager = NotificationManager()
    event = NotificationEvent(
        event_id="evt-3",
        channel=NotificationChannel.EMAIL,
        severity=NotificationSeverity.ERROR,
        subject="Error",
        body="Failed",
        recipient="ops@example.com",
    )
    with pytest.raises(ContractViolationError):
        manager.send(event)
