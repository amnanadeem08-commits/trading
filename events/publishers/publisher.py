"""Event publisher helpers."""

from __future__ import annotations

from events.event_bus import EventBus
from events.event_types import DomainEvent


class EventPublisher:
    """Thin publisher wrapper over the event bus."""

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus

    def publish(self, event: DomainEvent) -> None:
        self._bus.publish(event)
