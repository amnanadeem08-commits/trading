"""Execution lifecycle events and manager."""

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

type LifecycleHandler = Callable[["ExecutionLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "execution"


class ExecutionLifecycleEventType(StrEnum):
    """Execution lifecycle event identifiers."""

    EXECUTION_STARTED = "execution_started"
    EXECUTION_VALIDATED = "execution_validated"
    EXECUTION_QUEUED = "execution_queued"
    EXECUTION_DISPATCHED = "execution_dispatched"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_CANCELLED = "execution_cancelled"


class ExecutionLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the execution layer."""

    event_id: str
    event_type: ExecutionLifecycleEventType
    execution_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class ExecutionStartedEvent(ExecutionLifecycleEvent):
    """Emitted when an execution operation starts."""

    event_type: ExecutionLifecycleEventType = ExecutionLifecycleEventType.EXECUTION_STARTED


class ExecutionValidatedEvent(ExecutionLifecycleEvent):
    """Emitted when execution validation completes."""

    event_type: ExecutionLifecycleEventType = ExecutionLifecycleEventType.EXECUTION_VALIDATED


class ExecutionQueuedEvent(ExecutionLifecycleEvent):
    """Emitted when an execution contract is queued."""

    event_type: ExecutionLifecycleEventType = ExecutionLifecycleEventType.EXECUTION_QUEUED


class ExecutionDispatchedEvent(ExecutionLifecycleEvent):
    """Emitted when an execution contract is dispatched."""

    event_type: ExecutionLifecycleEventType = ExecutionLifecycleEventType.EXECUTION_DISPATCHED


class ExecutionCompletedEvent(ExecutionLifecycleEvent):
    """Emitted when an execution operation completes."""

    event_type: ExecutionLifecycleEventType = ExecutionLifecycleEventType.EXECUTION_COMPLETED


class ExecutionFailedEvent(ExecutionLifecycleEvent):
    """Emitted when an execution operation fails."""

    event_type: ExecutionLifecycleEventType = ExecutionLifecycleEventType.EXECUTION_FAILED


class ExecutionCancelledEvent(ExecutionLifecycleEvent):
    """Emitted when an execution operation is cancelled."""

    event_type: ExecutionLifecycleEventType = ExecutionLifecycleEventType.EXECUTION_CANCELLED


class ExecutionLifecycleManager:
    """Manages execution lifecycle events and EventBus publication."""

    def __init__(self, context: PipelineContext) -> None:
        self._context = context
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[ExecutionLifecycleEvent] = []

    @property
    def events(self) -> tuple[ExecutionLifecycleEvent, ...]:
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
        event_type: ExecutionLifecycleEventType,
        *,
        execution_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> ExecutionLifecycleEvent:
        event = ExecutionLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            execution_id=execution_id,
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

    def _publish_to_event_bus(self, event: ExecutionLifecycleEvent) -> None:
        event_type_map = {
            ExecutionLifecycleEventType.EXECUTION_STARTED: EventType.PREDICTION_CREATED,
            ExecutionLifecycleEventType.EXECUTION_VALIDATED: EventType.VALIDATION_COMPLETED,
            ExecutionLifecycleEventType.EXECUTION_QUEUED: EventType.VALIDATION_COMPLETED,
            ExecutionLifecycleEventType.EXECUTION_DISPATCHED: EventType.VALIDATION_COMPLETED,
            ExecutionLifecycleEventType.EXECUTION_COMPLETED: EventType.VALIDATION_COMPLETED,
            ExecutionLifecycleEventType.EXECUTION_FAILED: EventType.VALIDATION_COMPLETED,
            ExecutionLifecycleEventType.EXECUTION_CANCELLED: EventType.VALIDATION_COMPLETED,
        }
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=event_type_map[event.event_type],
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=event.execution_id,
            payload={
                "source": INFRASTRUCTURE_ENTITY_ID,
                "lifecycle_event": event.event_type.value,
                "execution_id": event.execution_id,
                "trace_id": event.trace_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._context.event_bus.publish(domain_event)

    def _record_metrics(self, event: ExecutionLifecycleEvent) -> None:
        self._context.metrics.counter("execution.lifecycle.events").inc(1)
        self._context.metrics.counter(f"execution.lifecycle.{event.event_type.value}").inc(1)
