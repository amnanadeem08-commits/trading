"""Plugin lifecycle events and manager."""

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

type LifecycleHandler = Callable[["PluginLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "ml_engine_plugins"


class PluginLifecycleEventType(StrEnum):
    """ML engine plugin lifecycle event identifiers."""

    PLUGIN_DISCOVERED = "plugin_discovered"
    PLUGIN_REGISTERED = "plugin_registered"
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_VALIDATED = "plugin_validated"
    PLUGIN_HEALTH_CHECKED = "plugin_health_checked"
    PLUGIN_UNLOADED = "plugin_unloaded"
    PLUGIN_FAILED = "plugin_failed"


class PluginDiscoveredEvent(PlatformModel):
    """Event emitted when a plugin is discovered."""

    event_id: str
    plugin_id: str
    name: str
    version: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class PluginRegisteredEvent(PlatformModel):
    """Event emitted when a plugin is registered."""

    event_id: str
    plugin_id: str
    name: str
    version: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class PluginLoadedEvent(PlatformModel):
    """Event emitted when a plugin is loaded."""

    event_id: str
    plugin_id: str
    name: str
    version: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class PluginValidatedEvent(PlatformModel):
    """Event emitted when a plugin is validated."""

    event_id: str
    plugin_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class PluginHealthCheckedEvent(PlatformModel):
    """Event emitted when a plugin health check completes."""

    event_id: str
    plugin_id: str
    status: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class PluginUnloadedEvent(PlatformModel):
    """Event emitted when a plugin is unloaded."""

    event_id: str
    plugin_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class PluginFailedEvent(PlatformModel):
    """Event emitted when a plugin operation fails."""

    event_id: str
    plugin_id: str
    message: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class PluginLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the plugin framework."""

    event_id: str
    event_type: PluginLifecycleEventType
    plugin_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class PluginLifecycleManager:
    """Manages plugin lifecycle events and EventBus publication."""

    def __init__(self, *, event_bus: EventBus, metrics: MetricRegistry) -> None:
        self._event_bus = event_bus
        self._metrics = metrics
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[PluginLifecycleEvent] = []

    @property
    def events(self) -> tuple[PluginLifecycleEvent, ...]:
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
        event_type: PluginLifecycleEventType,
        *,
        plugin_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> PluginLifecycleEvent:
        event = PluginLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            plugin_id=plugin_id,
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
        self._metrics.counter("ml_engine_plugins.lifecycle.events").inc(1)
        self._metrics.counter(f"ml_engine_plugins.lifecycle.{event_type.value}").inc(1)
        return event

    def _publish_to_event_bus(self, event: PluginLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=INFRASTRUCTURE_ENTITY_ID,
            payload={
                "ml_engine_plugin_event_type": event.event_type.value,
                "plugin_id": event.plugin_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._event_bus.publish(domain_event)

    def emit_plugin_discovered(
        self,
        *,
        plugin_id: str,
        name: str,
        version: str,
        correlation_id: str,
        trace_id: str,
    ) -> PluginDiscoveredEvent:
        event = PluginDiscoveredEvent(
            event_id=str(uuid4()),
            plugin_id=plugin_id,
            name=name,
            version=version,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            PluginLifecycleEventType.PLUGIN_DISCOVERED,
            plugin_id=plugin_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="plugin discovered",
            payload={"name": name, "version": version},
        )
        return event

    def emit_plugin_registered(
        self,
        *,
        plugin_id: str,
        name: str,
        version: str,
        correlation_id: str,
        trace_id: str,
    ) -> PluginRegisteredEvent:
        event = PluginRegisteredEvent(
            event_id=str(uuid4()),
            plugin_id=plugin_id,
            name=name,
            version=version,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            PluginLifecycleEventType.PLUGIN_REGISTERED,
            plugin_id=plugin_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="plugin registered",
            payload={"name": name, "version": version},
        )
        return event

    def emit_plugin_loaded(
        self,
        *,
        plugin_id: str,
        name: str,
        version: str,
        correlation_id: str,
        trace_id: str,
    ) -> PluginLoadedEvent:
        event = PluginLoadedEvent(
            event_id=str(uuid4()),
            plugin_id=plugin_id,
            name=name,
            version=version,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            PluginLifecycleEventType.PLUGIN_LOADED,
            plugin_id=plugin_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="plugin loaded",
            payload={"name": name, "version": version},
        )
        return event

    def emit_plugin_validated(
        self,
        *,
        plugin_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> PluginValidatedEvent:
        event = PluginValidatedEvent(
            event_id=str(uuid4()),
            plugin_id=plugin_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            PluginLifecycleEventType.PLUGIN_VALIDATED,
            plugin_id=plugin_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="plugin validated",
        )
        return event

    def emit_plugin_health_checked(
        self,
        *,
        plugin_id: str,
        status: str,
        correlation_id: str,
        trace_id: str,
    ) -> PluginHealthCheckedEvent:
        event = PluginHealthCheckedEvent(
            event_id=str(uuid4()),
            plugin_id=plugin_id,
            status=status,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            PluginLifecycleEventType.PLUGIN_HEALTH_CHECKED,
            plugin_id=plugin_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="plugin health checked",
            payload={"status": status},
        )
        return event

    def emit_plugin_unloaded(
        self,
        *,
        plugin_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> PluginUnloadedEvent:
        event = PluginUnloadedEvent(
            event_id=str(uuid4()),
            plugin_id=plugin_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            PluginLifecycleEventType.PLUGIN_UNLOADED,
            plugin_id=plugin_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="plugin unloaded",
        )
        return event

    def emit_plugin_failed(
        self,
        *,
        plugin_id: str,
        message: str,
        correlation_id: str,
        trace_id: str,
    ) -> PluginFailedEvent:
        event = PluginFailedEvent(
            event_id=str(uuid4()),
            plugin_id=plugin_id,
            message=message,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            PluginLifecycleEventType.PLUGIN_FAILED,
            plugin_id=plugin_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
        )
        return event
