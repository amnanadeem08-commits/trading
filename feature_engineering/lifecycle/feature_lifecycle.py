"""Feature engineering lifecycle events and manager."""

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

type LifecycleHandler = Callable[["FeatureLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "feature_engineering"


class FeatureLifecycleEventType(StrEnum):
    """Feature engineering lifecycle event identifiers."""

    EXTRACTION_STARTED = "feature_extraction_started"
    EXTRACTION_COMPLETED = "feature_extraction_completed"
    VALIDATION_COMPLETED = "feature_validation_completed"
    FEATURE_REGISTERED = "feature_registered"


class FeatureExtractionStartedEvent(PlatformModel):
    """Event emitted when feature extraction starts."""

    event_id: str
    pipeline_id: str
    dataset_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class FeatureExtractionCompletedEvent(PlatformModel):
    """Event emitted when feature extraction completes."""

    event_id: str
    pipeline_id: str
    dataset_id: str
    vectors_extracted: int
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class FeatureValidationCompletedEvent(PlatformModel):
    """Event emitted when feature validation completes."""

    event_id: str
    dataset_id: str
    valid: bool
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class FeatureRegisteredEvent(PlatformModel):
    """Event emitted when a feature definition is registered."""

    event_id: str
    feature_id: str
    schema_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class FeatureLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the feature engineering framework."""

    event_id: str
    event_type: FeatureLifecycleEventType
    dataset_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class FeatureLifecycleManager:
    """Manages feature engineering lifecycle events and EventBus publication."""

    def __init__(self, *, event_bus: EventBus, metrics: MetricRegistry) -> None:
        self._event_bus = event_bus
        self._metrics = metrics
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[FeatureLifecycleEvent] = []

    @property
    def events(self) -> tuple[FeatureLifecycleEvent, ...]:
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
        event_type: FeatureLifecycleEventType,
        *,
        dataset_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> FeatureLifecycleEvent:
        event = FeatureLifecycleEvent(
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
        self._metrics.counter("feature_engineering.lifecycle.events").inc(1)
        self._metrics.counter(f"feature_engineering.lifecycle.{event_type.value}").inc(1)
        return event

    def emit_extraction_started(
        self,
        *,
        pipeline_id: str,
        dataset_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> FeatureExtractionStartedEvent:
        event = FeatureExtractionStartedEvent(
            event_id=str(uuid4()),
            pipeline_id=pipeline_id,
            dataset_id=dataset_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            FeatureLifecycleEventType.EXTRACTION_STARTED,
            dataset_id=dataset_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="extraction started",
            payload={"pipeline_id": pipeline_id},
        )
        return event

    def emit_extraction_completed(
        self,
        *,
        pipeline_id: str,
        dataset_id: str,
        vectors_extracted: int,
        correlation_id: str,
        trace_id: str,
    ) -> FeatureExtractionCompletedEvent:
        event = FeatureExtractionCompletedEvent(
            event_id=str(uuid4()),
            pipeline_id=pipeline_id,
            dataset_id=dataset_id,
            vectors_extracted=vectors_extracted,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            FeatureLifecycleEventType.EXTRACTION_COMPLETED,
            dataset_id=dataset_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="extraction completed",
            payload={"pipeline_id": pipeline_id, "vectors_extracted": vectors_extracted},
        )
        return event

    def emit_validation_completed(
        self,
        *,
        dataset_id: str,
        valid: bool,
        correlation_id: str,
        trace_id: str,
    ) -> FeatureValidationCompletedEvent:
        event = FeatureValidationCompletedEvent(
            event_id=str(uuid4()),
            dataset_id=dataset_id,
            valid=valid,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            FeatureLifecycleEventType.VALIDATION_COMPLETED,
            dataset_id=dataset_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="validation completed",
            payload={"valid": valid},
        )
        return event

    def emit_feature_registered(
        self,
        *,
        feature_id: str,
        schema_id: str,
        dataset_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> FeatureRegisteredEvent:
        event = FeatureRegisteredEvent(
            event_id=str(uuid4()),
            feature_id=feature_id,
            schema_id=schema_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            FeatureLifecycleEventType.FEATURE_REGISTERED,
            dataset_id=dataset_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="feature registered",
            payload={"feature_id": feature_id, "schema_id": schema_id},
        )
        return event

    def _publish_to_event_bus(self, event: FeatureLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=INFRASTRUCTURE_ENTITY_ID,
            payload={
                "feature_event_type": event.event_type.value,
                "dataset_id": event.dataset_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._event_bus.publish(domain_event)
