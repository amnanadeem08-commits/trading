"""ML lifecycle events and manager."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from threading import RLock
from uuid import uuid4

from models.common import PlatformModel, UTCDateTime, utc_now
from models.events import DomainEvent, EventType
from pipeline.context import PipelineContext

type LifecycleHandler = Callable[["MLLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "ml"


class MLLifecycleEventType(StrEnum):
    """ML lifecycle event identifiers."""

    TRAINING_STARTED = "training_started"
    TRAINING_COMPLETED = "training_completed"
    MODEL_REGISTERED = "model_registered"
    INFERENCE_STARTED = "inference_started"
    INFERENCE_COMPLETED = "inference_completed"
    EVALUATION_COMPLETED = "evaluation_completed"


class MLLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the ML layer."""

    event_id: str
    event_type: MLLifecycleEventType
    model_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime


class MLLifecycleManager:
    """Manages ML lifecycle events and EventBus publication."""

    def __init__(self, context: PipelineContext) -> None:
        self._context = context
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[MLLifecycleEvent] = []

    @property
    def events(self) -> tuple[MLLifecycleEvent, ...]:
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
        event_type: MLLifecycleEventType,
        *,
        model_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
    ) -> MLLifecycleEvent:
        event = MLLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
            occurred_at=utc_now(),
        )
        with self._lock:
            self._events.append(event)
            handlers = tuple(self._handlers.values())
        for handler in handlers:
            handler(event)
        self._publish_to_event_bus(event)
        self._record_metrics(event)
        return event

    def _publish_to_event_bus(self, event: MLLifecycleEvent) -> None:
        event_type_map = {
            MLLifecycleEventType.TRAINING_STARTED: EventType.VALIDATION_COMPLETED,
            MLLifecycleEventType.TRAINING_COMPLETED: EventType.VALIDATION_COMPLETED,
            MLLifecycleEventType.MODEL_REGISTERED: EventType.PREDICTION_CREATED,
            MLLifecycleEventType.INFERENCE_STARTED: EventType.PREDICTION_CREATED,
            MLLifecycleEventType.INFERENCE_COMPLETED: EventType.PREDICTION_CREATED,
            MLLifecycleEventType.EVALUATION_COMPLETED: EventType.VALIDATION_COMPLETED,
        }
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=event_type_map[event.event_type],
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=event.model_id,
            payload={
                "source": "ml",
                "lifecycle_event": event.event_type.value,
                "model_id": event.model_id,
                "trace_id": event.trace_id,
                "message": event.message,
            },
        )
        self._context.event_bus.publish(domain_event)

    def _record_metrics(self, event: MLLifecycleEvent) -> None:
        self._context.metrics.counter("ml.lifecycle.events").inc(1)
        self._context.metrics.counter(f"ml.lifecycle.{event.event_type.value}").inc(1)
