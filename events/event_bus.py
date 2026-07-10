"""In-process domain event bus."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from events.event_types import DomainEvent, EventHandler, EventType
from events.persistence import EventPersistenceStore, InMemoryEventPersistenceStore
from models.common import PlatformError


class EventBusError(PlatformError):
    """Raised when event bus operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="event_bus_error")


class EventSubscription:
    """Handle for an active event bus subscription."""

    def __init__(self, subscription_id: str, event_type: EventType, handler: EventHandler) -> None:
        self.subscription_id = subscription_id
        self.event_type = event_type
        self.handler = handler


class EventBus:
    """In-process event bus with append-only persistence."""

    def __init__(self, persistence: EventPersistenceStore | None = None) -> None:
        self._lock = RLock()
        self._subscriptions: dict[str, EventSubscription] = {}
        self._persistence = persistence or InMemoryEventPersistenceStore()

    @property
    def persistence(self) -> EventPersistenceStore:
        return self._persistence

    def publish(self, event: DomainEvent) -> None:
        """Publish an event to subscribers and append to persistence."""
        self._persistence.append(event)
        handlers = self._handlers_for(event.event_type)
        for handler in handlers:
            handler(event)

    def subscribe(self, event_type: EventType, handler: EventHandler) -> str:
        """Subscribe a handler to an event type. Returns subscription id."""
        subscription_id = str(uuid4())
        subscription = EventSubscription(subscription_id, event_type, handler)
        with self._lock:
            self._subscriptions[subscription_id] = subscription
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> None:
        """Remove a subscription by id."""
        with self._lock:
            if subscription_id not in self._subscriptions:
                msg = f"Subscription not found: {subscription_id}"
                raise EventBusError(msg)
            del self._subscriptions[subscription_id]

    def subscription_count(self, event_type: EventType | None = None) -> int:
        """Return active subscription count, optionally filtered by event type."""
        with self._lock:
            if event_type is None:
                return len(self._subscriptions)
            return sum(
                1
                for subscription in self._subscriptions.values()
                if subscription.event_type == event_type
            )

    def _handlers_for(self, event_type: EventType) -> tuple[EventHandler, ...]:
        with self._lock:
            return tuple(
                subscription.handler
                for subscription in self._subscriptions.values()
                if subscription.event_type == event_type
            )


_default_bus: EventBus | None = None
_bus_lock = RLock()


def get_event_bus() -> EventBus:
    """Return the process-wide default event bus."""
    global _default_bus
    with _bus_lock:
        if _default_bus is None:
            _default_bus = EventBus()
        return _default_bus


def reset_event_bus() -> None:
    """Reset default event bus. Intended for tests."""
    global _default_bus
    with _bus_lock:
        _default_bus = None
