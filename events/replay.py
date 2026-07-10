"""Event replay scaffold."""

from __future__ import annotations

from collections.abc import Callable

from events.event_types import DomainEvent, EventHandler
from events.persistence import EventPersistenceStore


class EventReplayer:
    """Replays persisted events through handlers without republishing."""

    def __init__(self, persistence: EventPersistenceStore) -> None:
        self._persistence = persistence

    def replay(
        self,
        handler: EventHandler,
        *,
        event_type: str | None = None,
        correlation_id: str | None = None,
    ) -> int:
        """Replay filtered events through a handler. Returns replay count."""
        events = self._persistence.list_events(
            event_type=event_type,
            correlation_id=correlation_id,
        )
        for event in events:
            handler(event)
        return len(events)

    def replay_all(self, handler: EventHandler) -> int:
        """Replay all persisted events."""
        return self.replay(handler)

    def replay_with_filter(
        self,
        handler: EventHandler,
        predicate: Callable[[DomainEvent], bool],
    ) -> int:
        """Replay events matching a custom predicate."""
        events = self._persistence.list_events()
        matched = [event for event in events if predicate(event)]
        for event in matched:
            handler(event)
        return len(matched)
