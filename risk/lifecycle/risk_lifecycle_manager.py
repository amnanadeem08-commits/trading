"""Risk lifecycle events and manager."""

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

type LifecycleHandler = Callable[["RiskLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "risk"


class RiskLifecycleEventType(StrEnum):
    """Risk lifecycle event identifiers."""

    RISK_STARTED = "risk_started"
    RISK_VALIDATED = "risk_validated"
    RISK_APPROVED = "risk_approved"
    RISK_REJECTED = "risk_rejected"
    RISK_COMPLETED = "risk_completed"


class RiskLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the risk layer."""

    event_id: str
    event_type: RiskLifecycleEventType
    risk_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class RiskStartedEvent(RiskLifecycleEvent):
    """Emitted when a risk assessment starts."""

    event_type: RiskLifecycleEventType = RiskLifecycleEventType.RISK_STARTED


class RiskValidatedEvent(RiskLifecycleEvent):
    """Emitted when risk validation completes."""

    event_type: RiskLifecycleEventType = RiskLifecycleEventType.RISK_VALIDATED


class RiskApprovedEvent(RiskLifecycleEvent):
    """Emitted when a risk assessment is approved."""

    event_type: RiskLifecycleEventType = RiskLifecycleEventType.RISK_APPROVED


class RiskRejectedEvent(RiskLifecycleEvent):
    """Emitted when a risk assessment is rejected."""

    event_type: RiskLifecycleEventType = RiskLifecycleEventType.RISK_REJECTED


class RiskCompletedEvent(RiskLifecycleEvent):
    """Emitted when a risk assessment completes."""

    event_type: RiskLifecycleEventType = RiskLifecycleEventType.RISK_COMPLETED


class RiskLifecycleManager:
    """Manages risk lifecycle events and EventBus publication."""

    def __init__(self, context: PipelineContext) -> None:
        self._context = context
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[RiskLifecycleEvent] = []

    @property
    def events(self) -> tuple[RiskLifecycleEvent, ...]:
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
        event_type: RiskLifecycleEventType,
        *,
        risk_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> RiskLifecycleEvent:
        event = RiskLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            risk_id=risk_id,
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

    def _publish_to_event_bus(self, event: RiskLifecycleEvent) -> None:
        event_type_map = {
            RiskLifecycleEventType.RISK_STARTED: EventType.PREDICTION_CREATED,
            RiskLifecycleEventType.RISK_VALIDATED: EventType.VALIDATION_COMPLETED,
            RiskLifecycleEventType.RISK_APPROVED: EventType.VALIDATION_COMPLETED,
            RiskLifecycleEventType.RISK_REJECTED: EventType.VALIDATION_COMPLETED,
            RiskLifecycleEventType.RISK_COMPLETED: EventType.VALIDATION_COMPLETED,
        }
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=event_type_map[event.event_type],
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=event.risk_id,
            payload={
                "source": "risk",
                "lifecycle_event": event.event_type.value,
                "risk_id": event.risk_id,
                "trace_id": event.trace_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._context.event_bus.publish(domain_event)

    def _record_metrics(self, event: RiskLifecycleEvent) -> None:
        self._context.metrics.counter("risk.lifecycle.events").inc(1)
        self._context.metrics.counter(f"risk.lifecycle.{event.event_type.value}").inc(1)
