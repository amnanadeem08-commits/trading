"""Artifact lifecycle events and manager."""

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

type LifecycleHandler = Callable[["ArtifactLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "artifact_management"


class ArtifactLifecycleEventType(StrEnum):
    """Artifact lifecycle event identifiers."""

    ARTIFACT_REGISTERED = "artifact_registered"
    ARTIFACT_RESOLVED = "artifact_resolved"
    ARTIFACT_VALIDATED = "artifact_validated"
    ARTIFACT_CACHED = "artifact_cached"
    ARTIFACT_EXPIRED = "artifact_expired"
    ARTIFACT_FAILED = "artifact_failed"


class ArtifactRegisteredEvent(PlatformModel):
    """Event emitted when an artifact is registered."""

    event_id: str
    artifact_id: str
    name: str
    version: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ArtifactResolvedEvent(PlatformModel):
    """Event emitted when an artifact is resolved."""

    event_id: str
    artifact_id: str
    uri: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ArtifactValidatedEvent(PlatformModel):
    """Event emitted when an artifact is validated."""

    event_id: str
    artifact_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ArtifactCachedEvent(PlatformModel):
    """Event emitted when an artifact is cached."""

    event_id: str
    artifact_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ArtifactExpiredEvent(PlatformModel):
    """Event emitted when an artifact cache entry expires."""

    event_id: str
    artifact_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ArtifactFailedEvent(PlatformModel):
    """Event emitted when an artifact operation fails."""

    event_id: str
    artifact_id: str
    message: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ArtifactLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the artifact management layer."""

    event_id: str
    event_type: ArtifactLifecycleEventType
    artifact_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class ArtifactLifecycleManager:
    """Manages artifact lifecycle events and EventBus publication."""

    def __init__(self, *, event_bus: EventBus, metrics: MetricRegistry) -> None:
        self._event_bus = event_bus
        self._metrics = metrics
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[ArtifactLifecycleEvent] = []

    @property
    def events(self) -> tuple[ArtifactLifecycleEvent, ...]:
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
        event_type: ArtifactLifecycleEventType,
        *,
        artifact_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> ArtifactLifecycleEvent:
        event = ArtifactLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            artifact_id=artifact_id,
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
        self._metrics.counter("artifact_management.lifecycle.events").inc(1)
        self._metrics.counter(f"artifact_management.lifecycle.{event_type.value}").inc(1)
        return event

    def _publish_to_event_bus(self, event: ArtifactLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=INFRASTRUCTURE_ENTITY_ID,
            payload={
                "artifact_management_event_type": event.event_type.value,
                "artifact_id": event.artifact_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._event_bus.publish(domain_event)

    def emit_artifact_registered(
        self,
        *,
        artifact_id: str,
        name: str,
        version: str,
        correlation_id: str,
        trace_id: str,
    ) -> ArtifactRegisteredEvent:
        event = ArtifactRegisteredEvent(
            event_id=str(uuid4()),
            artifact_id=artifact_id,
            name=name,
            version=version,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            ArtifactLifecycleEventType.ARTIFACT_REGISTERED,
            artifact_id=artifact_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="artifact registered",
            payload={"name": name, "version": version},
        )
        return event

    def emit_artifact_resolved(
        self,
        *,
        artifact_id: str,
        uri: str,
        correlation_id: str,
        trace_id: str,
    ) -> ArtifactResolvedEvent:
        event = ArtifactResolvedEvent(
            event_id=str(uuid4()),
            artifact_id=artifact_id,
            uri=uri,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            ArtifactLifecycleEventType.ARTIFACT_RESOLVED,
            artifact_id=artifact_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="artifact resolved",
            payload={"uri": uri},
        )
        return event

    def emit_artifact_validated(
        self,
        *,
        artifact_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> ArtifactValidatedEvent:
        event = ArtifactValidatedEvent(
            event_id=str(uuid4()),
            artifact_id=artifact_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            ArtifactLifecycleEventType.ARTIFACT_VALIDATED,
            artifact_id=artifact_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="artifact validated",
        )
        return event

    def emit_artifact_cached(
        self,
        *,
        artifact_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> ArtifactCachedEvent:
        event = ArtifactCachedEvent(
            event_id=str(uuid4()),
            artifact_id=artifact_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            ArtifactLifecycleEventType.ARTIFACT_CACHED,
            artifact_id=artifact_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="artifact cached",
        )
        return event

    def emit_artifact_expired(
        self,
        *,
        artifact_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> ArtifactExpiredEvent:
        event = ArtifactExpiredEvent(
            event_id=str(uuid4()),
            artifact_id=artifact_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            ArtifactLifecycleEventType.ARTIFACT_EXPIRED,
            artifact_id=artifact_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="artifact expired",
        )
        return event

    def emit_artifact_failed(
        self,
        *,
        artifact_id: str,
        message: str,
        correlation_id: str,
        trace_id: str,
    ) -> ArtifactFailedEvent:
        event = ArtifactFailedEvent(
            event_id=str(uuid4()),
            artifact_id=artifact_id,
            message=message,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            ArtifactLifecycleEventType.ARTIFACT_FAILED,
            artifact_id=artifact_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
        )
        return event
