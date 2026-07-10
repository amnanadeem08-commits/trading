"""Workflow lifecycle events."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from threading import RLock
from uuid import uuid4

from models.common import PlatformModel, UTCDateTime, utc_now
from models.events import DomainEvent, EventType
from pipeline.context import PipelineContext

type LifecycleHandler = Callable[["WorkflowLifecycleEvent"], None]

INFRASTRUCTURE_MARKET_ID = "platform"
INFRASTRUCTURE_SYMBOL_ID = "workflow"


class WorkflowLifecycleEventType(StrEnum):
    """Workflow lifecycle event identifiers."""

    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"


class WorkflowLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the workflow runtime."""

    event_id: str
    event_type: WorkflowLifecycleEventType
    workflow_id: str
    workflow_version: str
    correlation_id: str
    job_id: str | None = None
    message: str
    occurred_at: UTCDateTime


class WorkflowLifecycleManager:
    """Manages workflow lifecycle events and EventBus publication."""

    def __init__(self, context: PipelineContext) -> None:
        self._context = context
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[WorkflowLifecycleEvent] = []

    @property
    def events(self) -> tuple[WorkflowLifecycleEvent, ...]:
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
        event_type: WorkflowLifecycleEventType,
        *,
        workflow_id: str,
        workflow_version: str,
        correlation_id: str,
        message: str,
        job_id: str | None = None,
    ) -> WorkflowLifecycleEvent:
        event = WorkflowLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            workflow_id=workflow_id,
            workflow_version=workflow_version,
            correlation_id=correlation_id,
            job_id=job_id,
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

    def _publish_to_event_bus(self, event: WorkflowLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_MARKET_ID,
            symbol_id=event.job_id or event.workflow_id,
            payload={
                "source": "workflow",
                "lifecycle_event": event.event_type.value,
                "workflow_id": event.workflow_id,
                "workflow_version": event.workflow_version,
                "job_id": event.job_id,
                "message": event.message,
            },
        )
        self._context.event_bus.publish(domain_event)
