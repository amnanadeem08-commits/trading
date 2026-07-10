"""Plugin lifecycle states and transitions."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from threading import RLock
from uuid import uuid4

from models.common import PlatformModel, UTCDateTime, utc_now
from models.events import DomainEvent, EventType
from pipeline.context import PipelineContext
from plugins.exceptions import PluginStateError
from plugins.plugin import BasePlugin
from plugins.state import PluginState

type LifecycleHandler = Callable[["PluginLifecycleEvent"], None]

INFRASTRUCTURE_MARKET_ID = "platform"
INFRASTRUCTURE_SYMBOL_ID = "plugin"


class PluginLifecycleEventType(StrEnum):
    """Plugin lifecycle event identifiers."""

    PLUGIN_DISCOVERED = "plugin_discovered"
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_ENABLED = "plugin_enabled"
    PLUGIN_DISABLED = "plugin_disabled"
    PLUGIN_FAILED = "plugin_failed"


class PluginLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the plugin framework."""

    event_id: str
    event_type: PluginLifecycleEventType
    plugin_id: str
    plugin_version: str
    correlation_id: str
    message: str
    occurred_at: UTCDateTime


class PluginLifecycle:
    """Manages initialize/start/stop/dispose transitions for one plugin."""

    def __init__(self, implementation: BasePlugin) -> None:
        self._implementation = implementation
        self._state = PluginState.LOADED

    @property
    def state(self) -> PluginState:
        return self._state

    def initialize(self) -> PluginState:
        """Initialize the plugin implementation."""
        if self._state not in {PluginState.LOADED, PluginState.STOPPED}:
            raise PluginStateError(
                self._implementation.plugin_id(),
                self._state.value,
                "initialize",
            )
        self._state = PluginState.INITIALIZED
        return self._state

    def start(self) -> PluginState:
        """Start the plugin implementation."""
        if self._state not in {PluginState.INITIALIZED, PluginState.DISABLED}:
            raise PluginStateError(
                self._implementation.plugin_id(),
                self._state.value,
                "start",
            )
        self._state = PluginState.ENABLED
        return self._state

    def stop(self) -> PluginState:
        """Stop the plugin implementation."""
        if self._state not in {PluginState.ENABLED, PluginState.INITIALIZED}:
            raise PluginStateError(
                self._implementation.plugin_id(),
                self._state.value,
                "stop",
            )
        self._state = PluginState.STOPPED
        return self._state

    def dispose(self) -> PluginState:
        """Dispose plugin resources."""
        if self._state == PluginState.FAILED:
            raise PluginStateError(
                self._implementation.plugin_id(),
                self._state.value,
                "dispose",
            )
        self._state = PluginState.DISABLED
        return self._state


class PluginLifecycleManager:
    """Manages plugin lifecycle events and EventBus publication."""

    def __init__(self, context: PipelineContext) -> None:
        self._context = context
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
        plugin_version: str,
        correlation_id: str,
        message: str,
    ) -> PluginLifecycleEvent:
        event = PluginLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            plugin_id=plugin_id,
            plugin_version=plugin_version,
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

    def _publish_to_event_bus(self, event: PluginLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_MARKET_ID,
            symbol_id=event.plugin_id,
            payload={
                "source": "plugin",
                "lifecycle_event": event.event_type.value,
                "plugin_id": event.plugin_id,
                "plugin_version": event.plugin_version,
                "message": event.message,
            },
        )
        self._context.event_bus.publish(domain_event)
