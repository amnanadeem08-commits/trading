"""Registry lifecycle events and manager."""

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

type LifecycleHandler = Callable[["RegistryLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "model_registry"


class RegistryLifecycleEventType(StrEnum):
    """Model registry lifecycle event identifiers."""

    MODEL_REGISTERED = "model_registered"
    VERSION_REGISTERED = "version_registered"
    PROMOTION_REQUESTED = "promotion_requested"
    PROMOTION_APPROVED = "promotion_approved"
    PROMOTION_REJECTED = "promotion_rejected"
    MODEL_ARCHIVED = "model_archived"
    LINEAGE_UPDATED = "lineage_updated"


class ModelRegisteredEvent(PlatformModel):
    """Event emitted when a model is registered."""

    event_id: str
    model_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class VersionRegisteredEvent(PlatformModel):
    """Event emitted when a model version is registered."""

    event_id: str
    model_id: str
    version_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class PromotionRequestedEvent(PlatformModel):
    """Event emitted when promotion approval is requested."""

    event_id: str
    model_id: str
    version_id: str
    to_stage: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class PromotionApprovedEvent(PlatformModel):
    """Event emitted when promotion is approved."""

    event_id: str
    model_id: str
    version_id: str
    to_stage: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class PromotionRejectedEvent(PlatformModel):
    """Event emitted when promotion is rejected."""

    event_id: str
    model_id: str
    version_id: str
    message: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ModelArchivedEvent(PlatformModel):
    """Event emitted when a model is archived."""

    event_id: str
    model_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class LineageUpdatedEvent(PlatformModel):
    """Event emitted when lineage graph is updated."""

    event_id: str
    model_id: str
    version_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class RegistryLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the model registry."""

    event_id: str
    event_type: RegistryLifecycleEventType
    model_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class RegistryLifecycleManager:
    """Manages model registry lifecycle events and EventBus publication."""

    def __init__(self, *, event_bus: EventBus, metrics: MetricRegistry) -> None:
        self._event_bus = event_bus
        self._metrics = metrics
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[RegistryLifecycleEvent] = []

    @property
    def events(self) -> tuple[RegistryLifecycleEvent, ...]:
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
        event_type: RegistryLifecycleEventType,
        *,
        model_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> RegistryLifecycleEvent:
        event = RegistryLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
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
        self._metrics.counter("model_registry.lifecycle.events").inc(1)
        self._metrics.counter(f"model_registry.lifecycle.{event_type.value}").inc(1)
        return event

    def emit_model_registered(
        self,
        *,
        model_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> ModelRegisteredEvent:
        event = ModelRegisteredEvent(
            event_id=str(uuid4()),
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RegistryLifecycleEventType.MODEL_REGISTERED,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="model registered",
        )
        return event

    def emit_version_registered(
        self,
        *,
        model_id: str,
        version_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> VersionRegisteredEvent:
        event = VersionRegisteredEvent(
            event_id=str(uuid4()),
            model_id=model_id,
            version_id=version_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RegistryLifecycleEventType.VERSION_REGISTERED,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="version registered",
            payload={"version_id": version_id},
        )
        return event

    def emit_promotion_requested(
        self,
        *,
        model_id: str,
        version_id: str,
        to_stage: str,
        correlation_id: str,
        trace_id: str,
    ) -> PromotionRequestedEvent:
        event = PromotionRequestedEvent(
            event_id=str(uuid4()),
            model_id=model_id,
            version_id=version_id,
            to_stage=to_stage,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RegistryLifecycleEventType.PROMOTION_REQUESTED,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="promotion requested",
            payload={"version_id": version_id, "to_stage": to_stage},
        )
        return event

    def emit_promotion_approved(
        self,
        *,
        model_id: str,
        version_id: str,
        to_stage: str,
        correlation_id: str,
        trace_id: str,
    ) -> PromotionApprovedEvent:
        event = PromotionApprovedEvent(
            event_id=str(uuid4()),
            model_id=model_id,
            version_id=version_id,
            to_stage=to_stage,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RegistryLifecycleEventType.PROMOTION_APPROVED,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="promotion approved",
            payload={"version_id": version_id, "to_stage": to_stage},
        )
        return event

    def emit_promotion_rejected(
        self,
        *,
        model_id: str,
        version_id: str,
        message: str,
        correlation_id: str,
        trace_id: str,
    ) -> PromotionRejectedEvent:
        event = PromotionRejectedEvent(
            event_id=str(uuid4()),
            model_id=model_id,
            version_id=version_id,
            message=message,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RegistryLifecycleEventType.PROMOTION_REJECTED,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
            payload={"version_id": version_id},
        )
        return event

    def emit_model_archived(
        self,
        *,
        model_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> ModelArchivedEvent:
        event = ModelArchivedEvent(
            event_id=str(uuid4()),
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RegistryLifecycleEventType.MODEL_ARCHIVED,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="model archived",
        )
        return event

    def emit_lineage_updated(
        self,
        *,
        model_id: str,
        version_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> LineageUpdatedEvent:
        event = LineageUpdatedEvent(
            event_id=str(uuid4()),
            model_id=model_id,
            version_id=version_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            RegistryLifecycleEventType.LINEAGE_UPDATED,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="lineage updated",
            payload={"version_id": version_id},
        )
        return event

    def _publish_to_event_bus(self, event: RegistryLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=INFRASTRUCTURE_ENTITY_ID,
            payload={
                "model_registry_event_type": event.event_type.value,
                "model_id": event.model_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._event_bus.publish(domain_event)
