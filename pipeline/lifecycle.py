"""Pipeline lifecycle events and cancellation."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from threading import RLock
from uuid import uuid4

from models.common import PlatformModel, UTCDateTime, utc_now
from models.events import DomainEvent, EventType
from pipeline.context import PipelineContext
from pipeline.request import PipelineRequest

type LifecycleHandler = Callable[["PipelineLifecycleEvent"], None]

INFRASTRUCTURE_MARKET_ID = "platform"
INFRASTRUCTURE_SYMBOL_ID = "pipeline"


class PipelineLifecycleEventType(StrEnum):
    """Pipeline lifecycle event identifiers."""

    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"
    STAGE_SKIPPED = "stage_skipped"


class PipelineLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the pipeline engine."""

    event_id: str
    event_type: PipelineLifecycleEventType
    pipeline_name: str
    pipeline_version: str
    request_id: str
    correlation_id: str
    stage_name: str | None = None
    message: str
    occurred_at: UTCDateTime


class CancellationToken:
    """Cancellation token for pipeline execution."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._cancelled = False

    def cancel(self) -> None:
        with self._lock:
            self._cancelled = True

    def is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled


class PipelineLifecycleManager:
    """Manages pipeline lifecycle events and EventBus publication."""

    def __init__(self, context: PipelineContext) -> None:
        self._context = context
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[PipelineLifecycleEvent] = []

    @property
    def events(self) -> tuple[PipelineLifecycleEvent, ...]:
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
        event_type: PipelineLifecycleEventType,
        *,
        pipeline_name: str,
        pipeline_version: str,
        request: PipelineRequest,
        message: str,
        stage_name: str | None = None,
    ) -> PipelineLifecycleEvent:
        event = PipelineLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            pipeline_name=pipeline_name,
            pipeline_version=pipeline_version,
            request_id=request.request_id,
            correlation_id=request.correlation_id,
            stage_name=stage_name,
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

    def _publish_to_event_bus(self, event: PipelineLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_MARKET_ID,
            symbol_id=event.stage_name or event.pipeline_name,
            payload={
                "source": "pipeline",
                "lifecycle_event": event.event_type.value,
                "pipeline_name": event.pipeline_name,
                "pipeline_version": event.pipeline_version,
                "request_id": event.request_id,
                "stage_name": event.stage_name,
                "message": event.message,
            },
        )
        self._context.event_bus.publish(domain_event)
