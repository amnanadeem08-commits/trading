"""Decision lifecycle events and manager."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from threading import RLock
from typing import Any
from uuid import uuid4

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from models.events import DomainEvent, EventType
from pipeline.context import PipelineContext

type LifecycleHandler = Callable[["DecisionLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "decision"


class DecisionLifecycleEventType(StrEnum):
    """Decision lifecycle event identifiers."""

    DECISION_STARTED = "decision_started"
    DECISION_COMPLETED = "decision_completed"
    DECISION_REJECTED = "decision_rejected"
    DECISION_FAILED = "decision_failed"


class DecisionLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the decision layer."""

    event_id: str
    event_type: DecisionLifecycleEventType
    decision_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class DecisionStartedEvent(DecisionLifecycleEvent):
    """Emitted when a decision operation starts."""

    event_type: DecisionLifecycleEventType = DecisionLifecycleEventType.DECISION_STARTED


class DecisionCompletedEvent(DecisionLifecycleEvent):
    """Emitted when a decision operation completes."""

    event_type: DecisionLifecycleEventType = DecisionLifecycleEventType.DECISION_COMPLETED


class DecisionRejectedEvent(DecisionLifecycleEvent):
    """Emitted when a decision is rejected by policy evaluation."""

    event_type: DecisionLifecycleEventType = DecisionLifecycleEventType.DECISION_REJECTED


class DecisionFailedEvent(DecisionLifecycleEvent):
    """Emitted when a decision operation fails."""

    event_type: DecisionLifecycleEventType = DecisionLifecycleEventType.DECISION_FAILED


class DecisionLifecycleManager:
    """Manages decision lifecycle events and EventBus publication."""

    def __init__(self, context: PipelineContext) -> None:
        self._context = context
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[DecisionLifecycleEvent] = []

    @property
    def events(self) -> tuple[DecisionLifecycleEvent, ...]:
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
        event_type: DecisionLifecycleEventType,
        *,
        decision_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> DecisionLifecycleEvent:
        event = DecisionLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            decision_id=decision_id,
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
        self._record_metrics(event)
        return event

    def _publish_to_event_bus(self, event: DecisionLifecycleEvent) -> None:
        event_type_map = {
            DecisionLifecycleEventType.DECISION_STARTED: EventType.PREDICTION_CREATED,
            DecisionLifecycleEventType.DECISION_COMPLETED: EventType.VALIDATION_COMPLETED,
            DecisionLifecycleEventType.DECISION_REJECTED: EventType.VALIDATION_COMPLETED,
            DecisionLifecycleEventType.DECISION_FAILED: EventType.VALIDATION_COMPLETED,
        }
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=event_type_map[event.event_type],
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=event.decision_id,
            payload={
                "source": "decision",
                "lifecycle_event": event.event_type.value,
                "decision_id": event.decision_id,
                "trace_id": event.trace_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._context.event_bus.publish(domain_event)

    def _record_metrics(self, event: DecisionLifecycleEvent) -> None:
        self._context.metrics.counter("decision.lifecycle.events").inc(1)
        self._context.metrics.counter(f"decision.lifecycle.{event.event_type.value}").inc(1)
