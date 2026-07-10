"""Historical lifecycle events and manager."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from threading import RLock
from typing import Any
from uuid import uuid4

from pydantic import Field

from events.event_bus import EventBus
from metrics.registry import MetricRegistry
from models.common import PlatformModel, UTCDateTime, utc_now
from models.events import DomainEvent, EventType

type LifecycleHandler = Callable[["HistoricalLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "historical"


class HistoricalLifecycleEventType(StrEnum):
    """Historical lifecycle event identifiers."""

    DATASET_REGISTERED = "historical_dataset_registered"
    DATASET_STORED = "historical_dataset_stored"
    DATASET_VALIDATED = "historical_dataset_validated"
    REPLAY_STARTED = "historical_replay_started"
    REPLAY_COMPLETED = "historical_replay_completed"
    QUERY_EXECUTED = "historical_query_executed"


class HistoricalLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the historical repository."""

    event_id: str
    event_type: HistoricalLifecycleEventType
    dataset_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class HistoricalLifecycleManager:
    """Manages historical lifecycle events and EventBus publication."""

    def __init__(self, *, event_bus: EventBus, metrics: MetricRegistry) -> None:
        self._event_bus = event_bus
        self._metrics = metrics
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[HistoricalLifecycleEvent] = []

    @property
    def events(self) -> tuple[HistoricalLifecycleEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def on_event(self, handler: LifecycleHandler) -> str:
        subscription_id = str(uuid4())
        with self._lock:
            self._handlers[subscription_id] = handler
        return subscription_id

    def off_event(self, subscription_id: str) -> None:
        with self._lock:
            self._handlers.pop(subscription_id, None)

    def emit(
        self,
        event_type: HistoricalLifecycleEventType,
        *,
        dataset_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> HistoricalLifecycleEvent:
        event = HistoricalLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            dataset_id=dataset_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
            occurred_at=utc_now(),
            payload=payload or {},
        )
        with self._lock:
            self._events.append(event)
            handlers = tuple(self._handlers.values())
        for handler in handlers:
            handler(event)
        self._publish_to_event_bus(event)
        self._metrics.counter("historical.lifecycle.events").inc(1)
        self._metrics.counter(f"historical.lifecycle.{event.event_type.value}").inc(1)
        return event

    def _publish_to_event_bus(self, event: HistoricalLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=INFRASTRUCTURE_ENTITY_ID,
            payload={
                "historical_event_type": event.event_type.value,
                "dataset_id": event.dataset_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._event_bus.publish(domain_event)
