"""Connector lifecycle events and manager."""

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

type LifecycleHandler = Callable[["ConnectorLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "connector"


class ConnectorLifecycleEventType(StrEnum):
    """Connector lifecycle event identifiers."""

    CONNECTOR_REGISTERED = "connector_registered"
    CONNECTOR_INITIALIZED = "connector_initialized"
    CONNECTOR_VALIDATED = "connector_validated"
    CONNECTOR_DISPATCH_REQUESTED = "connector_dispatch_requested"
    CONNECTOR_SHUTDOWN = "connector_shutdown"


class ConnectorLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the connector framework."""

    event_id: str
    event_type: ConnectorLifecycleEventType
    connector_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class ConnectorRegisteredEvent(ConnectorLifecycleEvent):
    """Emitted when a connector is registered."""

    event_type: ConnectorLifecycleEventType = ConnectorLifecycleEventType.CONNECTOR_REGISTERED


class ConnectorInitializedEvent(ConnectorLifecycleEvent):
    """Emitted when a connector is initialized."""

    event_type: ConnectorLifecycleEventType = ConnectorLifecycleEventType.CONNECTOR_INITIALIZED


class ConnectorValidatedEvent(ConnectorLifecycleEvent):
    """Emitted when connector validation completes."""

    event_type: ConnectorLifecycleEventType = ConnectorLifecycleEventType.CONNECTOR_VALIDATED


class ConnectorDispatchRequestedEvent(ConnectorLifecycleEvent):
    """Emitted when a dispatch is requested through the bridge."""

    event_type: ConnectorLifecycleEventType = (
        ConnectorLifecycleEventType.CONNECTOR_DISPATCH_REQUESTED
    )


class ConnectorShutdownEvent(ConnectorLifecycleEvent):
    """Emitted when a connector is shut down."""

    event_type: ConnectorLifecycleEventType = ConnectorLifecycleEventType.CONNECTOR_SHUTDOWN


class ConnectorLifecycleManager:
    """Manages connector lifecycle events and EventBus publication."""

    def __init__(self, *, event_bus: EventBus, metrics: MetricRegistry) -> None:
        self._event_bus = event_bus
        self._metrics = metrics
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[ConnectorLifecycleEvent] = []

    @property
    def events(self) -> tuple[ConnectorLifecycleEvent, ...]:
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
        event_type: ConnectorLifecycleEventType,
        *,
        connector_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> ConnectorLifecycleEvent:
        event = ConnectorLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            connector_id=connector_id,
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

    def _publish_to_event_bus(self, event: ConnectorLifecycleEvent) -> None:
        event_type_map = {
            ConnectorLifecycleEventType.CONNECTOR_REGISTERED: EventType.PREDICTION_CREATED,
            ConnectorLifecycleEventType.CONNECTOR_INITIALIZED: EventType.VALIDATION_COMPLETED,
            ConnectorLifecycleEventType.CONNECTOR_VALIDATED: EventType.VALIDATION_COMPLETED,
            ConnectorLifecycleEventType.CONNECTOR_DISPATCH_REQUESTED: (
                EventType.VALIDATION_COMPLETED
            ),
            ConnectorLifecycleEventType.CONNECTOR_SHUTDOWN: EventType.VALIDATION_COMPLETED,
        }
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=event_type_map[event.event_type],
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=event.connector_id,
            payload={
                "source": INFRASTRUCTURE_ENTITY_ID,
                "lifecycle_event": event.event_type.value,
                "connector_id": event.connector_id,
                "trace_id": event.trace_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._event_bus.publish(domain_event)

    def _record_metrics(self, event: ConnectorLifecycleEvent) -> None:
        self._metrics.counter("connector.lifecycle.events").inc(1)
        self._metrics.counter(f"connector.lifecycle.{event.event_type.value}").inc(1)
