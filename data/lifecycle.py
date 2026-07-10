"""Dataset lifecycle events."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from threading import RLock
from uuid import uuid4

from models.common import PlatformModel, UTCDateTime, utc_now
from models.events import DomainEvent, EventType
from pipeline.context import PipelineContext

type LifecycleHandler = Callable[["DatasetLifecycleEvent"], None]

INFRASTRUCTURE_MARKET_ID = "platform"
INFRASTRUCTURE_SYMBOL_ID = "data"


class DatasetLifecycleEventType(StrEnum):
    """Dataset lifecycle event identifiers."""

    DATASET_REGISTERED = "dataset_registered"
    DATASET_VALIDATED = "dataset_validated"
    DATASET_LOAD_STARTED = "dataset_load_started"
    DATASET_LOAD_COMPLETED = "dataset_load_completed"
    DATASET_LOAD_FAILED = "dataset_load_failed"
    DATASET_TRANSFORM_STARTED = "dataset_transform_started"
    DATASET_TRANSFORM_COMPLETED = "dataset_transform_completed"
    DATASET_ARCHIVED = "dataset_archived"


class DatasetLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the data layer."""

    event_id: str
    event_type: DatasetLifecycleEventType
    dataset_id: str
    dataset_version: str
    correlation_id: str
    message: str
    occurred_at: UTCDateTime


class DatasetLifecycleManager:
    """Manages dataset lifecycle events and EventBus publication."""

    def __init__(self, context: PipelineContext) -> None:
        self._context = context
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[DatasetLifecycleEvent] = []

    @property
    def events(self) -> tuple[DatasetLifecycleEvent, ...]:
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
        event_type: DatasetLifecycleEventType,
        *,
        dataset_id: str,
        dataset_version: str,
        correlation_id: str,
        message: str,
    ) -> DatasetLifecycleEvent:
        event = DatasetLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            correlation_id=correlation_id,
            message=message,
            occurred_at=utc_now(),
        )
        with self._lock:
            self._events.append(event)
            handlers = tuple(self._handlers.values())
        for handler in handlers:
            handler(event)
        self._publish_to_event_bus(event)
        return event

    def _publish_to_event_bus(self, event: DatasetLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_MARKET_ID,
            symbol_id=event.dataset_id,
            payload={
                "source": "data",
                "lifecycle_event": event.event_type.value,
                "dataset_id": event.dataset_id,
                "dataset_version": event.dataset_version,
                "message": event.message,
            },
        )
        self._context.event_bus.publish(domain_event)
