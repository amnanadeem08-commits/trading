"""Append-only event persistence interface and in-memory scaffold."""

from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock

from events.event_types import DomainEvent


class EventPersistenceStore(ABC):
    """Append-only persistence contract for domain events."""

    @abstractmethod
    def append(self, event: DomainEvent) -> None:
        """Persist a single event. Append-only — no updates or deletes."""

    @abstractmethod
    def list_events(
        self,
        *,
        event_type: str | None = None,
        correlation_id: str | None = None,
    ) -> tuple[DomainEvent, ...]:
        """List persisted events with optional filters."""

    @abstractmethod
    def count(self) -> int:
        """Return total number of persisted events."""


class InMemoryEventPersistenceStore(EventPersistenceStore):
    """Thread-safe in-memory append-only event store for Phase 0."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._events: list[DomainEvent] = []

    def append(self, event: DomainEvent) -> None:
        with self._lock:
            self._events.append(event)

    def list_events(
        self,
        *,
        event_type: str | None = None,
        correlation_id: str | None = None,
    ) -> tuple[DomainEvent, ...]:
        with self._lock:
            events = list(self._events)
        if event_type is not None:
            events = [event for event in events if event.event_type.value == event_type]
        if correlation_id is not None:
            events = [event for event in events if event.correlation_id == correlation_id]
        return tuple(events)

    def count(self) -> int:
        with self._lock:
            return len(self._events)

    def clear(self) -> None:
        """Clear stored events. Intended for tests only."""
        with self._lock:
            self._events.clear()
