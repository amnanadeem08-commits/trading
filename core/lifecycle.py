"""Core lifecycle events."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from threading import RLock
from uuid import uuid4

from models.common import PlatformModel, UTCDateTime, utc_now
from models.events import DomainEvent, EventType
from pipeline.context import PipelineContext

type LifecycleHandler = Callable[["CoreLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "core"


class CoreLifecycleEventType(StrEnum):
    """Core lifecycle event identifiers."""

    CONTEXT_CREATED = "context_created"
    CONTEXT_UPDATED = "context_updated"
    ENTITY_REGISTERED = "entity_registered"
    ENTITY_VALIDATED = "entity_validated"
    OPERATION_STARTED = "operation_started"
    OPERATION_COMPLETED = "operation_completed"
    OPERATION_FAILED = "operation_failed"
    RUNTIME_INITIALIZED = "runtime_initialized"
    RUNTIME_SHUTDOWN = "runtime_shutdown"


class CoreLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the core layer."""

    event_id: str
    event_type: CoreLifecycleEventType
    entity_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime


class CoreLifecycleManager:
    """Manages core lifecycle events and EventBus publication."""

    def __init__(self, context: PipelineContext) -> None:
        self._context = context
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[CoreLifecycleEvent] = []

    @property
    def events(self) -> tuple[CoreLifecycleEvent, ...]:
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
        event_type: CoreLifecycleEventType,
        *,
        entity_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
    ) -> CoreLifecycleEvent:
        event = CoreLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            entity_id=entity_id,
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

    def _publish_to_event_bus(self, event: CoreLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=event.entity_id,
            payload={
                "source": "core",
                "lifecycle_event": event.event_type.value,
                "entity_id": event.entity_id,
                "trace_id": event.trace_id,
                "message": event.message,
            },
        )
        self._context.event_bus.publish(domain_event)

    def _record_metrics(self, event: CoreLifecycleEvent) -> None:
        self._context.metrics.counter("core.lifecycle.events").inc(1)
        self._context.metrics.counter(f"core.lifecycle.{event.event_type.value}").inc(1)
