"""Training lifecycle events and manager."""

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

type LifecycleHandler = Callable[["TrainingLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "training_pipeline"


class TrainingLifecycleEventType(StrEnum):
    """Training pipeline lifecycle event identifiers."""

    TRAINING_QUEUED = "training_queued"
    TRAINING_STARTED = "training_started"
    TRAINING_COMPLETED = "training_completed"
    TRAINING_FAILED = "training_failed"
    TRAINING_CANCELLED = "training_cancelled"
    CHECKPOINT_CREATED = "checkpoint_created"
    ARTIFACT_STORED = "artifact_stored"


class TrainingQueuedEvent(PlatformModel):
    """Event emitted when a training job is queued."""

    event_id: str
    job_id: str
    experiment_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class TrainingStartedEvent(PlatformModel):
    """Event emitted when a training job starts."""

    event_id: str
    job_id: str
    experiment_id: str
    run_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class TrainingCompletedEvent(PlatformModel):
    """Event emitted when a training job completes."""

    event_id: str
    job_id: str
    experiment_id: str
    run_id: str
    artifact_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class TrainingFailedEvent(PlatformModel):
    """Event emitted when a training job fails."""

    event_id: str
    job_id: str
    experiment_id: str
    message: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class TrainingCancelledEvent(PlatformModel):
    """Event emitted when a training job is cancelled."""

    event_id: str
    job_id: str
    experiment_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class CheckpointCreatedEvent(PlatformModel):
    """Event emitted when a training checkpoint is created."""

    event_id: str
    checkpoint_id: str
    job_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ArtifactStoredEvent(PlatformModel):
    """Event emitted when a model artifact is stored."""

    event_id: str
    artifact_id: str
    job_id: str
    experiment_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class TrainingLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the training pipeline."""

    event_id: str
    event_type: TrainingLifecycleEventType
    job_id: str
    experiment_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class TrainingLifecycleManager:
    """Manages training lifecycle events and EventBus publication."""

    def __init__(self, *, event_bus: EventBus, metrics: MetricRegistry) -> None:
        self._event_bus = event_bus
        self._metrics = metrics
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[TrainingLifecycleEvent] = []

    @property
    def events(self) -> tuple[TrainingLifecycleEvent, ...]:
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
        event_type: TrainingLifecycleEventType,
        *,
        job_id: str,
        experiment_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> TrainingLifecycleEvent:
        event = TrainingLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            job_id=job_id,
            experiment_id=experiment_id,
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
        self._metrics.counter("training_pipeline.lifecycle.events").inc(1)
        self._metrics.counter(f"training_pipeline.lifecycle.{event_type.value}").inc(1)
        return event

    def emit_queued(
        self,
        *,
        job_id: str,
        experiment_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> TrainingQueuedEvent:
        event = TrainingQueuedEvent(
            event_id=str(uuid4()),
            job_id=job_id,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            TrainingLifecycleEventType.TRAINING_QUEUED,
            job_id=job_id,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="training queued",
        )
        return event

    def emit_started(
        self,
        *,
        job_id: str,
        experiment_id: str,
        run_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> TrainingStartedEvent:
        event = TrainingStartedEvent(
            event_id=str(uuid4()),
            job_id=job_id,
            experiment_id=experiment_id,
            run_id=run_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            TrainingLifecycleEventType.TRAINING_STARTED,
            job_id=job_id,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="training started",
            payload={"run_id": run_id},
        )
        return event

    def emit_completed(
        self,
        *,
        job_id: str,
        experiment_id: str,
        run_id: str,
        artifact_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> TrainingCompletedEvent:
        event = TrainingCompletedEvent(
            event_id=str(uuid4()),
            job_id=job_id,
            experiment_id=experiment_id,
            run_id=run_id,
            artifact_id=artifact_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            TrainingLifecycleEventType.TRAINING_COMPLETED,
            job_id=job_id,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="training completed",
            payload={"run_id": run_id, "artifact_id": artifact_id},
        )
        return event

    def emit_failed(
        self,
        *,
        job_id: str,
        experiment_id: str,
        message: str,
        correlation_id: str,
        trace_id: str,
    ) -> TrainingFailedEvent:
        event = TrainingFailedEvent(
            event_id=str(uuid4()),
            job_id=job_id,
            experiment_id=experiment_id,
            message=message,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            TrainingLifecycleEventType.TRAINING_FAILED,
            job_id=job_id,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
        )
        return event

    def emit_cancelled(
        self,
        *,
        job_id: str,
        experiment_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> TrainingCancelledEvent:
        event = TrainingCancelledEvent(
            event_id=str(uuid4()),
            job_id=job_id,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            TrainingLifecycleEventType.TRAINING_CANCELLED,
            job_id=job_id,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="training cancelled",
        )
        return event

    def emit_checkpoint_created(
        self,
        *,
        checkpoint_id: str,
        job_id: str,
        experiment_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> CheckpointCreatedEvent:
        event = CheckpointCreatedEvent(
            event_id=str(uuid4()),
            checkpoint_id=checkpoint_id,
            job_id=job_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            TrainingLifecycleEventType.CHECKPOINT_CREATED,
            job_id=job_id,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="checkpoint created",
            payload={"checkpoint_id": checkpoint_id},
        )
        return event

    def emit_artifact_stored(
        self,
        *,
        artifact_id: str,
        job_id: str,
        experiment_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> ArtifactStoredEvent:
        event = ArtifactStoredEvent(
            event_id=str(uuid4()),
            artifact_id=artifact_id,
            job_id=job_id,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            TrainingLifecycleEventType.ARTIFACT_STORED,
            job_id=job_id,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="artifact stored",
            payload={"artifact_id": artifact_id},
        )
        return event

    def _publish_to_event_bus(self, event: TrainingLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=INFRASTRUCTURE_ENTITY_ID,
            payload={
                "training_pipeline_event_type": event.event_type.value,
                "job_id": event.job_id,
                "experiment_id": event.experiment_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._event_bus.publish(domain_event)
