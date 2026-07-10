"""Feature store lifecycle events and manager."""

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

type LifecycleHandler = Callable[["FeatureStoreLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "feature_store"


class FeatureStoreLifecycleEventType(StrEnum):
    """Feature store lifecycle event identifiers."""

    DATASET_CREATED = "feature_dataset_created"
    DATASET_UPDATED = "feature_dataset_updated"
    SNAPSHOT_CREATED = "feature_snapshot_created"
    DATASET_VALIDATED = "feature_dataset_validated"


class DatasetCreatedEvent(PlatformModel):
    """Event emitted when a feature dataset is created."""

    event_id: str
    dataset_id: str
    version: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class DatasetUpdatedEvent(PlatformModel):
    """Event emitted when a feature dataset is updated."""

    event_id: str
    dataset_id: str
    record_count: int
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class SnapshotCreatedEvent(PlatformModel):
    """Event emitted when a feature snapshot is created."""

    event_id: str
    snapshot_id: str
    dataset_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class DatasetValidatedEvent(PlatformModel):
    """Event emitted when a feature dataset is validated."""

    event_id: str
    dataset_id: str
    valid: bool
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class FeatureStoreLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the feature store."""

    event_id: str
    event_type: FeatureStoreLifecycleEventType
    dataset_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class FeatureStoreLifecycleManager:
    """Manages feature store lifecycle events and EventBus publication."""

    def __init__(self, *, event_bus: EventBus, metrics: MetricRegistry) -> None:
        self._event_bus = event_bus
        self._metrics = metrics
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[FeatureStoreLifecycleEvent] = []

    @property
    def events(self) -> tuple[FeatureStoreLifecycleEvent, ...]:
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
        event_type: FeatureStoreLifecycleEventType,
        *,
        dataset_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> FeatureStoreLifecycleEvent:
        event = FeatureStoreLifecycleEvent(
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
        self._metrics.counter("feature_store.lifecycle.events").inc(1)
        self._metrics.counter(f"feature_store.lifecycle.{event_type.value}").inc(1)
        return event

    def emit_dataset_created(
        self,
        *,
        dataset_id: str,
        version: str,
        correlation_id: str,
        trace_id: str,
    ) -> DatasetCreatedEvent:
        event = DatasetCreatedEvent(
            event_id=str(uuid4()),
            dataset_id=dataset_id,
            version=version,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            FeatureStoreLifecycleEventType.DATASET_CREATED,
            dataset_id=dataset_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="dataset created",
            payload={"version": version},
        )
        return event

    def emit_dataset_updated(
        self,
        *,
        dataset_id: str,
        record_count: int,
        correlation_id: str,
        trace_id: str,
    ) -> DatasetUpdatedEvent:
        event = DatasetUpdatedEvent(
            event_id=str(uuid4()),
            dataset_id=dataset_id,
            record_count=record_count,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            FeatureStoreLifecycleEventType.DATASET_UPDATED,
            dataset_id=dataset_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="dataset updated",
            payload={"record_count": record_count},
        )
        return event

    def emit_snapshot_created(
        self,
        *,
        snapshot_id: str,
        dataset_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> SnapshotCreatedEvent:
        event = SnapshotCreatedEvent(
            event_id=str(uuid4()),
            snapshot_id=snapshot_id,
            dataset_id=dataset_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            FeatureStoreLifecycleEventType.SNAPSHOT_CREATED,
            dataset_id=dataset_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="snapshot created",
            payload={"snapshot_id": snapshot_id},
        )
        return event

    def emit_dataset_validated(
        self,
        *,
        dataset_id: str,
        valid: bool,
        correlation_id: str,
        trace_id: str,
    ) -> DatasetValidatedEvent:
        event = DatasetValidatedEvent(
            event_id=str(uuid4()),
            dataset_id=dataset_id,
            valid=valid,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            FeatureStoreLifecycleEventType.DATASET_VALIDATED,
            dataset_id=dataset_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="dataset validated",
            payload={"valid": valid},
        )
        return event

    def _publish_to_event_bus(self, event: FeatureStoreLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=INFRASTRUCTURE_ENTITY_ID,
            payload={
                "feature_store_event_type": event.event_type.value,
                "dataset_id": event.dataset_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._event_bus.publish(domain_event)
