"""Provider lifecycle events and manager."""

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

type LifecycleHandler = Callable[["ProviderLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "storage_providers"


class ProviderLifecycleEventType(StrEnum):
    """Storage provider lifecycle event identifiers."""

    PROVIDER_REGISTERED = "provider_registered"
    PROVIDER_STARTUP = "provider_startup"
    PROVIDER_RESOLVED = "provider_resolved"
    PROVIDER_VALIDATED = "provider_validated"
    PROVIDER_SHUTDOWN = "provider_shutdown"
    PROVIDER_FAILED = "provider_failed"
    CHECKSUM_VERIFIED = "checksum_verified"
    FILESYSTEM_FAILURE = "filesystem_failure"


class ProviderRegisteredEvent(PlatformModel):
    """Event emitted when a provider is registered."""

    event_id: str
    provider_id: str
    name: str
    version: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ProviderResolvedEvent(PlatformModel):
    """Event emitted when a provider resolves a URI."""

    event_id: str
    provider_id: str
    uri: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ProviderValidatedEvent(PlatformModel):
    """Event emitted when a provider is validated."""

    event_id: str
    provider_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ProviderShutdownEvent(PlatformModel):
    """Event emitted when a provider shuts down."""

    event_id: str
    provider_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ProviderFailedEvent(PlatformModel):
    """Event emitted when a provider operation fails."""

    event_id: str
    provider_id: str
    message: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ProviderLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the storage provider layer."""

    event_id: str
    event_type: ProviderLifecycleEventType
    provider_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class ProviderLifecycleManager:
    """Manages storage provider lifecycle events and EventBus publication."""

    def __init__(self, *, event_bus: EventBus, metrics: MetricRegistry) -> None:
        self._event_bus = event_bus
        self._metrics = metrics
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[ProviderLifecycleEvent] = []

    @property
    def events(self) -> tuple[ProviderLifecycleEvent, ...]:
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
        event_type: ProviderLifecycleEventType,
        *,
        provider_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> ProviderLifecycleEvent:
        event = ProviderLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            provider_id=provider_id,
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
        self._metrics.counter("storage_providers.lifecycle.events").inc(1)
        self._metrics.counter(f"storage_providers.lifecycle.{event_type.value}").inc(1)
        return event

    def _publish_to_event_bus(self, event: ProviderLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=INFRASTRUCTURE_ENTITY_ID,
            payload={
                "storage_provider_event_type": event.event_type.value,
                "provider_id": event.provider_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._event_bus.publish(domain_event)

    def emit_provider_registered(
        self,
        *,
        provider_id: str,
        name: str,
        version: str,
        correlation_id: str,
        trace_id: str,
    ) -> ProviderRegisteredEvent:
        event = ProviderRegisteredEvent(
            event_id=str(uuid4()),
            provider_id=provider_id,
            name=name,
            version=version,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            ProviderLifecycleEventType.PROVIDER_REGISTERED,
            provider_id=provider_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="provider registered",
            payload={"name": name, "version": version},
        )
        return event

    def emit_provider_resolved(
        self,
        *,
        provider_id: str,
        uri: str,
        correlation_id: str,
        trace_id: str,
    ) -> ProviderResolvedEvent:
        event = ProviderResolvedEvent(
            event_id=str(uuid4()),
            provider_id=provider_id,
            uri=uri,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            ProviderLifecycleEventType.PROVIDER_RESOLVED,
            provider_id=provider_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="provider resolved",
            payload={"uri": uri},
        )
        return event

    def emit_provider_validated(
        self,
        *,
        provider_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> ProviderValidatedEvent:
        event = ProviderValidatedEvent(
            event_id=str(uuid4()),
            provider_id=provider_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            ProviderLifecycleEventType.PROVIDER_VALIDATED,
            provider_id=provider_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="provider validated",
        )
        return event

    def emit_provider_shutdown(
        self,
        *,
        provider_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> ProviderShutdownEvent:
        event = ProviderShutdownEvent(
            event_id=str(uuid4()),
            provider_id=provider_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            ProviderLifecycleEventType.PROVIDER_SHUTDOWN,
            provider_id=provider_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="provider shutdown",
        )
        return event

    def emit_provider_failed(
        self,
        *,
        provider_id: str,
        message: str,
        correlation_id: str,
        trace_id: str,
    ) -> ProviderFailedEvent:
        event = ProviderFailedEvent(
            event_id=str(uuid4()),
            provider_id=provider_id,
            message=message,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            ProviderLifecycleEventType.PROVIDER_FAILED,
            provider_id=provider_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
        )
        return event

    def emit_provider_startup(
        self,
        *,
        provider_id: str,
        correlation_id: str,
        trace_id: str,
        artifact_root: str = "",
    ) -> None:
        self.emit(
            ProviderLifecycleEventType.PROVIDER_STARTUP,
            provider_id=provider_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="provider startup",
            payload={"artifact_root": artifact_root},
        )

    def emit_checksum_verified(
        self,
        *,
        provider_id: str,
        uri: str,
        correlation_id: str,
        trace_id: str,
    ) -> None:
        self.emit(
            ProviderLifecycleEventType.CHECKSUM_VERIFIED,
            provider_id=provider_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="checksum verified",
            payload={"uri": uri},
        )

    def emit_filesystem_failure(
        self,
        *,
        provider_id: str,
        message: str,
        correlation_id: str,
        trace_id: str,
    ) -> None:
        self.emit(
            ProviderLifecycleEventType.FILESYSTEM_FAILURE,
            provider_id=provider_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
        )
