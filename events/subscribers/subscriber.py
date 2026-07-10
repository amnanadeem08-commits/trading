"""Event subscriber helpers."""

from __future__ import annotations

from events.event_bus import EventBus
from events.event_types import EventHandler, EventType


class EventSubscriber:
    """Thin subscriber wrapper over the event bus."""

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus

    def subscribe(self, event_type: EventType, handler: EventHandler) -> str:
        return self._bus.subscribe(event_type, handler)

    def unsubscribe(self, subscription_id: str) -> None:
        self._bus.unsubscribe(subscription_id)
