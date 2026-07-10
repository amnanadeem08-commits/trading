"""Notification manager scaffold."""

from __future__ import annotations

from models.common import ContractViolationError
from notifications.events import NotificationChannel, NotificationEvent, NotificationResult
from notifications.providers import (
    EmailProvider,
    NotificationProvider,
    SlackProvider,
    WebhookProvider,
)


class NotificationManager:
    """Routes notification events to configured providers."""

    def __init__(
        self,
        *,
        email: EmailProvider | None = None,
        slack: SlackProvider | None = None,
        webhook: WebhookProvider | None = None,
        enabled: bool = True,
    ) -> None:
        self._providers: dict[NotificationChannel, NotificationProvider] = {}
        if email is not None:
            self._providers[NotificationChannel.EMAIL] = email
        if slack is not None:
            self._providers[NotificationChannel.SLACK] = slack
        if webhook is not None:
            self._providers[NotificationChannel.WEBHOOK] = webhook
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    def register(self, channel: NotificationChannel, provider: NotificationProvider) -> None:
        self._providers[channel] = provider

    def send(self, event: NotificationEvent) -> NotificationResult:
        if not self._enabled:
            return NotificationResult(
                event_id=event.event_id,
                success=False,
                message="Notifications are disabled",
            )
        provider = self._providers.get(event.channel)
        if provider is None:
            msg = f"No provider registered for channel: {event.channel.value}"
            raise ContractViolationError(msg)
        return provider.send(event)
