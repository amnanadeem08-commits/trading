"""Runtime lifecycle events and manager."""

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

type LifecycleHandler = Callable[["RuntimeLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "ml_runtime"


class RuntimeLifecycleEventType(StrEnum):
    """ML runtime lifecycle event identifiers."""

    RUNTIME_INITIALIZED = "runtime_initialized"
    RUNTIME_STARTED = "runtime_started"
    RUNTIME_COMPLETED = "runtime_completed"
    RUNTIME_FAILED = "runtime_failed"
    RUNTIME_SHUTDOWN = "runtime_shutdown"
    EXECUTOR_REGISTERED = "executor_registered"
    EXECUTOR_LOADED = "executor_loaded"
    EXECUTOR_UNLOADED = "executor_unloaded"


class RuntimeInitializedEvent(PlatformModel):
    """Event emitted when the ML runtime is initialized."""

    event_id: str
    runtime_version: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class RuntimeStartedEvent(PlatformModel):
    """Event emitted when runtime execution starts."""

    event_id: str
    execution_id: str
    request_id: str
    model_id: str
    executor_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class RuntimeCompletedEvent(PlatformModel):
    """Event emitted when runtime execution completes."""

    event_id: str
    execution_id: str
    request_id: str
    model_id: str
    executor_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class RuntimeFailedEvent(PlatformModel):
    """Event emitted when runtime execution fails."""

    event_id: str
    execution_id: str
    request_id: str
    model_id: str
    message: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class RuntimeShutdownEvent(PlatformModel):
    """Event emitted when the ML runtime shuts down."""

    event_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ExecutorRegisteredEvent(PlatformModel):
    """Event emitted when an executor is registered."""

    event_id: str
    executor_id: str
    name: str
    version: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ExecutorLoadedEvent(PlatformModel):
    """Event emitted when an executor loads artifacts."""

    event_id: str
    executor_id: str
    artifact_reference: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ExecutorUnloadedEvent(PlatformModel):
    """Event emitted when an executor unloads artifacts."""

    event_id: str
    executor_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class RuntimeLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the ML runtime."""

    event_id: str
    event_type: RuntimeLifecycleEventType
    request_id: str
    model_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class RuntimeLifecycleManager:
    """Manages ML runtime lifecycle events and EventBus publication."""

    def __init__(self, *, event_bus: EventBus, metrics: MetricRegistry) -> None:
        self._event_bus = event_bus
        self._metrics = metrics
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[RuntimeLifecycleEvent] = []

    @property
    def events(self) -> tuple[RuntimeLifecycleEvent, ...]:
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
        event_type: RuntimeLifecycleEventType,
        *,
        request_id: str,
        model_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> RuntimeLifecycleEvent:
        event = RuntimeLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            request_id=request_id,
            model_id=model_id,
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
        self._metrics.counter("ml_runtime.lifecycle.events").inc(1)
        self._metrics.counter(f"ml_runtime.lifecycle.{event_type.value}").inc(1)
        return event

    def _publish_to_event_bus(self, event: RuntimeLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=INFRASTRUCTURE_ENTITY_ID,
            payload={
                "ml_runtime_event_type": event.event_type.value,
                "request_id": event.request_id,
                "model_id": event.model_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._event_bus.publish(domain_event)

    def emit_runtime_initialized(
        self,
        *,
        runtime_version: str,
        correlation_id: str,
        trace_id: str,
    ) -> RuntimeInitializedEvent:
        event = RuntimeInitializedEvent(
            event_id=str(uuid4()),
            runtime_version=runtime_version,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RuntimeLifecycleEventType.RUNTIME_INITIALIZED,
            request_id="",
            model_id="ml_runtime",
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="runtime initialized",
            payload={"runtime_version": runtime_version},
        )
        return event

    def emit_runtime_started(
        self,
        *,
        execution_id: str,
        request_id: str,
        model_id: str,
        executor_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> RuntimeStartedEvent:
        event = RuntimeStartedEvent(
            event_id=str(uuid4()),
            execution_id=execution_id,
            request_id=request_id,
            model_id=model_id,
            executor_id=executor_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RuntimeLifecycleEventType.RUNTIME_STARTED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="runtime started",
            payload={"execution_id": execution_id, "executor_id": executor_id},
        )
        return event

    def emit_runtime_completed(
        self,
        *,
        execution_id: str,
        request_id: str,
        model_id: str,
        executor_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> RuntimeCompletedEvent:
        event = RuntimeCompletedEvent(
            event_id=str(uuid4()),
            execution_id=execution_id,
            request_id=request_id,
            model_id=model_id,
            executor_id=executor_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RuntimeLifecycleEventType.RUNTIME_COMPLETED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="runtime completed",
            payload={"execution_id": execution_id, "executor_id": executor_id},
        )
        return event

    def emit_runtime_failed(
        self,
        *,
        execution_id: str,
        request_id: str,
        model_id: str,
        message: str,
        correlation_id: str,
        trace_id: str,
    ) -> RuntimeFailedEvent:
        event = RuntimeFailedEvent(
            event_id=str(uuid4()),
            execution_id=execution_id,
            request_id=request_id,
            model_id=model_id,
            message=message,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RuntimeLifecycleEventType.RUNTIME_FAILED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
            payload={"execution_id": execution_id},
        )
        return event

    def emit_runtime_shutdown(self, *, correlation_id: str, trace_id: str) -> RuntimeShutdownEvent:
        event = RuntimeShutdownEvent(
            event_id=str(uuid4()),
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RuntimeLifecycleEventType.RUNTIME_SHUTDOWN,
            request_id="",
            model_id="ml_runtime",
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="runtime shutdown",
        )
        return event

    def emit_executor_registered(
        self,
        *,
        executor_id: str,
        name: str,
        version: str,
        correlation_id: str,
        trace_id: str,
    ) -> ExecutorRegisteredEvent:
        event = ExecutorRegisteredEvent(
            event_id=str(uuid4()),
            executor_id=executor_id,
            name=name,
            version=version,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RuntimeLifecycleEventType.EXECUTOR_REGISTERED,
            request_id="",
            model_id=executor_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="executor registered",
            payload={"name": name, "version": version},
        )
        return event

    def emit_executor_loaded(
        self,
        *,
        executor_id: str,
        artifact_reference: str,
        correlation_id: str,
        trace_id: str,
    ) -> ExecutorLoadedEvent:
        event = ExecutorLoadedEvent(
            event_id=str(uuid4()),
            executor_id=executor_id,
            artifact_reference=artifact_reference,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RuntimeLifecycleEventType.EXECUTOR_LOADED,
            request_id="",
            model_id=executor_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="executor loaded",
            payload={"artifact_reference": artifact_reference},
        )
        return event

    def emit_executor_unloaded(
        self,
        *,
        executor_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> ExecutorUnloadedEvent:
        event = ExecutorUnloadedEvent(
            event_id=str(uuid4()),
            executor_id=executor_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RuntimeLifecycleEventType.EXECUTOR_UNLOADED,
            request_id="",
            model_id=executor_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="executor unloaded",
        )
        return event
