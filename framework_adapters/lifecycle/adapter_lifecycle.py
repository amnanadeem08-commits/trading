"""Adapter lifecycle events and manager."""

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

type LifecycleHandler = Callable[["AdapterLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "framework_adapters"


class AdapterLifecycleEventType(StrEnum):
    """Framework adapter lifecycle event identifiers."""

    ADAPTER_INITIALIZED = "adapter_initialized"
    ADAPTER_DISCOVERED = "adapter_discovered"
    ADAPTER_REGISTERED = "adapter_registered"
    ADAPTER_VALIDATED = "adapter_validated"
    ADAPTER_SELECTED = "adapter_selected"
    ADAPTER_LOADED = "adapter_loaded"
    ADAPTER_UNLOADED = "adapter_unloaded"
    ADAPTER_SHUTDOWN = "adapter_shutdown"
    ADAPTER_FAILED = "adapter_failed"
    MODEL_LOADING = "model_loading"
    MODEL_READY = "model_ready"
    MODEL_REUSED = "model_reused"
    MODEL_RELOADED = "model_reloaded"
    MODEL_UNLOADED = "model_unloaded"
    MODEL_LOAD_FAILED = "model_load_failed"


class AdapterDiscoveredEvent(PlatformModel):
    """Event emitted when an adapter is discovered."""

    event_id: str
    adapter_id: str
    name: str
    version: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class AdapterRegisteredEvent(PlatformModel):
    """Event emitted when an adapter is registered."""

    event_id: str
    adapter_id: str
    name: str
    version: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class AdapterValidatedEvent(PlatformModel):
    """Event emitted when an adapter is validated."""

    event_id: str
    adapter_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class AdapterLoadedEvent(PlatformModel):
    """Event emitted when an adapter is loaded."""

    event_id: str
    adapter_id: str
    name: str
    version: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class AdapterShutdownEvent(PlatformModel):
    """Event emitted when an adapter shuts down."""

    event_id: str
    adapter_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class AdapterFailedEvent(PlatformModel):
    """Event emitted when an adapter operation fails."""

    event_id: str
    adapter_id: str
    message: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class AdapterLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the framework adapter layer."""

    event_id: str
    event_type: AdapterLifecycleEventType
    adapter_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class AdapterLifecycleManager:
    """Manages adapter lifecycle events and EventBus publication."""

    def __init__(self, *, event_bus: EventBus, metrics: MetricRegistry) -> None:
        self._event_bus = event_bus
        self._metrics = metrics
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[AdapterLifecycleEvent] = []

    @property
    def events(self) -> tuple[AdapterLifecycleEvent, ...]:
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
        event_type: AdapterLifecycleEventType,
        *,
        adapter_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> AdapterLifecycleEvent:
        event = AdapterLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            adapter_id=adapter_id,
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
        self._metrics.counter("framework_adapters.lifecycle.events").inc(1)
        self._metrics.counter(f"framework_adapters.lifecycle.{event_type.value}").inc(1)
        return event

    def _publish_to_event_bus(self, event: AdapterLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=INFRASTRUCTURE_ENTITY_ID,
            payload={
                "framework_adapter_event_type": event.event_type.value,
                "adapter_id": event.adapter_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._event_bus.publish(domain_event)

    def emit_adapter_initialized(
        self,
        *,
        adapter_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterLifecycleEvent:
        return self.emit(
            AdapterLifecycleEventType.ADAPTER_INITIALIZED,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="adapter runtime initialized",
        )

    def emit_adapter_selected(
        self,
        *,
        adapter_id: str,
        engine_type: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterLifecycleEvent:
        return self.emit(
            AdapterLifecycleEventType.ADAPTER_SELECTED,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="adapter selected",
            payload={"engine_type": engine_type},
        )

    def emit_adapter_unloaded(
        self,
        *,
        adapter_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterLifecycleEvent:
        return self.emit(
            AdapterLifecycleEventType.ADAPTER_UNLOADED,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="adapter unloaded",
        )

    def emit_adapter_discovered(
        self,
        *,
        adapter_id: str,
        name: str,
        version: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterDiscoveredEvent:
        event = AdapterDiscoveredEvent(
            event_id=str(uuid4()),
            adapter_id=adapter_id,
            name=name,
            version=version,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            AdapterLifecycleEventType.ADAPTER_DISCOVERED,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="adapter discovered",
            payload={"name": name, "version": version},
        )
        return event

    def emit_adapter_registered(
        self,
        *,
        adapter_id: str,
        name: str,
        version: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterRegisteredEvent:
        event = AdapterRegisteredEvent(
            event_id=str(uuid4()),
            adapter_id=adapter_id,
            name=name,
            version=version,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            AdapterLifecycleEventType.ADAPTER_REGISTERED,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="adapter registered",
            payload={"name": name, "version": version},
        )
        return event

    def emit_adapter_validated(
        self,
        *,
        adapter_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterValidatedEvent:
        event = AdapterValidatedEvent(
            event_id=str(uuid4()),
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            AdapterLifecycleEventType.ADAPTER_VALIDATED,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="adapter validated",
        )
        return event

    def emit_adapter_loaded(
        self,
        *,
        adapter_id: str,
        name: str,
        version: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterLoadedEvent:
        event = AdapterLoadedEvent(
            event_id=str(uuid4()),
            adapter_id=adapter_id,
            name=name,
            version=version,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            AdapterLifecycleEventType.ADAPTER_LOADED,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="adapter loaded",
            payload={"name": name, "version": version},
        )
        return event

    def emit_adapter_shutdown(
        self,
        *,
        adapter_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterShutdownEvent:
        event = AdapterShutdownEvent(
            event_id=str(uuid4()),
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            AdapterLifecycleEventType.ADAPTER_SHUTDOWN,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="adapter shutdown",
        )
        return event

    def emit_adapter_failed(
        self,
        *,
        adapter_id: str,
        message: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterFailedEvent:
        event = AdapterFailedEvent(
            event_id=str(uuid4()),
            adapter_id=adapter_id,
            message=message,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            AdapterLifecycleEventType.ADAPTER_FAILED,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
        )
        return event

    def emit_model_loading(
        self,
        *,
        adapter_id: str,
        model_id: str,
        artifact_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterLifecycleEvent:
        return self.emit(
            AdapterLifecycleEventType.MODEL_LOADING,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="model loading",
            payload={"model_id": model_id, "artifact_id": artifact_id},
        )

    def emit_model_ready(
        self,
        *,
        adapter_id: str,
        model_id: str,
        artifact_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterLifecycleEvent:
        return self.emit(
            AdapterLifecycleEventType.MODEL_READY,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="model ready",
            payload={"model_id": model_id, "artifact_id": artifact_id},
        )

    def emit_model_reused(
        self,
        *,
        adapter_id: str,
        model_id: str,
        artifact_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterLifecycleEvent:
        return self.emit(
            AdapterLifecycleEventType.MODEL_REUSED,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="model session reused",
            payload={"model_id": model_id, "artifact_id": artifact_id},
        )

    def emit_model_reloaded(
        self,
        *,
        adapter_id: str,
        model_id: str,
        artifact_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterLifecycleEvent:
        return self.emit(
            AdapterLifecycleEventType.MODEL_RELOADED,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="model reloaded",
            payload={"model_id": model_id, "artifact_id": artifact_id},
        )

    def emit_model_unloaded(
        self,
        *,
        adapter_id: str,
        model_id: str,
        artifact_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterLifecycleEvent:
        return self.emit(
            AdapterLifecycleEventType.MODEL_UNLOADED,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="model unloaded",
            payload={"model_id": model_id, "artifact_id": artifact_id},
        )

    def emit_model_load_failed(
        self,
        *,
        adapter_id: str,
        model_id: str,
        message: str,
        correlation_id: str,
        trace_id: str,
    ) -> AdapterLifecycleEvent:
        return self.emit(
            AdapterLifecycleEventType.MODEL_LOAD_FAILED,
            adapter_id=adapter_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
            payload={"model_id": model_id},
        )
