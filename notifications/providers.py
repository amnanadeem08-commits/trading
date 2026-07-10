"""Notification provider interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod

from notifications.events import NotificationEvent, NotificationResult


class NotificationProvider(ABC):
    """Base interface for notification providers."""

    @abstractmethod
    def send(self, event: NotificationEvent) -> NotificationResult:
        """Send a notification event."""


class EmailProvider(NotificationProvider):
    """Email notification provider interface."""

    @abstractmethod
    def send(self, event: NotificationEvent) -> NotificationResult:
        """Send an email notification."""


class SlackProvider(NotificationProvider):
    """Slack notification provider interface."""

    @abstractmethod
    def send(self, event: NotificationEvent) -> NotificationResult:
        """Send a Slack notification."""


class WebhookProvider(NotificationProvider):
    """Webhook notification provider interface."""

    @abstractmethod
    def send(self, event: NotificationEvent) -> NotificationResult:
        """Send a webhook notification."""
