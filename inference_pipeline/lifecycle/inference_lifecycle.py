"""Inference lifecycle events and manager."""

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

type LifecycleHandler = Callable[["InferenceLifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "inference_pipeline"


class InferenceLifecycleEventType(StrEnum):
    """Inference pipeline lifecycle event identifiers."""

    INFERENCE_QUEUED = "inference_queued"
    INFERENCE_STARTED = "inference_started"
    INFERENCE_COMPLETED = "inference_completed"
    INFERENCE_FAILED = "inference_failed"
    INFERENCE_CANCELLED = "inference_cancelled"
    MODEL_RESOLVED = "model_resolved"
    RUNTIME_INITIALIZED = "runtime_initialized"
    INFERENCE_REQUEST_RECEIVED = "inference_request_received"
    FEATURES_BOUND = "features_bound"
    MODEL_EXECUTION_STARTED = "model_execution_started"
    MODEL_EXECUTION_COMPLETED = "model_execution_completed"
    OUTPUT_NORMALIZED = "output_normalized"


class InferenceQueuedEvent(PlatformModel):
    """Event emitted when an inference request is queued."""

    event_id: str
    request_id: str
    model_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class InferenceStartedEvent(PlatformModel):
    """Event emitted when inference orchestration starts."""

    event_id: str
    request_id: str
    model_id: str
    version_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class InferenceCompletedEvent(PlatformModel):
    """Event emitted when inference orchestration completes."""

    event_id: str
    request_id: str
    model_id: str
    version_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class InferenceFailedEvent(PlatformModel):
    """Event emitted when inference orchestration fails."""

    event_id: str
    request_id: str
    model_id: str
    message: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class InferenceCancelledEvent(PlatformModel):
    """Event emitted when inference is cancelled."""

    event_id: str
    request_id: str
    model_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class ModelResolvedEvent(PlatformModel):
    """Event emitted when a production model is resolved."""

    event_id: str
    model_id: str
    version_id: str
    artifact_id: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class RuntimeInitializedEvent(PlatformModel):
    """Event emitted when inference runtime is initialized."""

    event_id: str
    pipeline_version: str
    correlation_id: str
    trace_id: str
    occurred_at: UTCDateTime


class InferenceLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the inference pipeline."""

    event_id: str
    event_type: InferenceLifecycleEventType
    request_id: str
    model_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class InferenceLifecycleManager:
    """Manages inference lifecycle events and EventBus publication."""

    def __init__(self, *, event_bus: EventBus, metrics: MetricRegistry) -> None:
        self._event_bus = event_bus
        self._metrics = metrics
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[InferenceLifecycleEvent] = []

    @property
    def events(self) -> tuple[InferenceLifecycleEvent, ...]:
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
        event_type: InferenceLifecycleEventType,
        *,
        request_id: str,
        model_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> InferenceLifecycleEvent:
        event = InferenceLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            request_id=request_id,
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
        self._metrics.counter("inference_pipeline.lifecycle.events").inc(1)
        self._metrics.counter(f"inference_pipeline.lifecycle.{event_type.value}").inc(1)
        return event

    def emit_queued(
        self,
        *,
        request_id: str,
        model_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> InferenceQueuedEvent:
        event = InferenceQueuedEvent(
            event_id=str(uuid4()),
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            InferenceLifecycleEventType.INFERENCE_QUEUED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="inference queued",
        )
        return event

    def emit_started(
        self,
        *,
        request_id: str,
        model_id: str,
        version_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> InferenceStartedEvent:
        event = InferenceStartedEvent(
            event_id=str(uuid4()),
            request_id=request_id,
            model_id=model_id,
            version_id=version_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            InferenceLifecycleEventType.INFERENCE_STARTED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="inference started",
            payload={"version_id": version_id},
        )
        return event

    def emit_completed(
        self,
        *,
        request_id: str,
        model_id: str,
        version_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> InferenceCompletedEvent:
        event = InferenceCompletedEvent(
            event_id=str(uuid4()),
            request_id=request_id,
            model_id=model_id,
            version_id=version_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            InferenceLifecycleEventType.INFERENCE_COMPLETED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="inference completed",
            payload={"version_id": version_id},
        )
        return event

    def emit_failed(
        self,
        *,
        request_id: str,
        model_id: str,
        message: str,
        correlation_id: str,
        trace_id: str,
    ) -> InferenceFailedEvent:
        event = InferenceFailedEvent(
            event_id=str(uuid4()),
            request_id=request_id,
            model_id=model_id,
            message=message,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            InferenceLifecycleEventType.INFERENCE_FAILED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
        )
        return event

    def emit_cancelled(
        self,
        *,
        request_id: str,
        model_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> InferenceCancelledEvent:
        event = InferenceCancelledEvent(
            event_id=str(uuid4()),
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            InferenceLifecycleEventType.INFERENCE_CANCELLED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="inference cancelled",
        )
        return event

    def emit_model_resolved(
        self,
        *,
        model_id: str,
        version_id: str,
        artifact_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> ModelResolvedEvent:
        event = ModelResolvedEvent(
            event_id=str(uuid4()),
            model_id=model_id,
            version_id=version_id,
            artifact_id=artifact_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            InferenceLifecycleEventType.MODEL_RESOLVED,
            request_id="",
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="model resolved",
            payload={
                "version_id": version_id,
                "artifact_id": artifact_id,
            },
        )
        return event

    def emit_runtime_initialized(
        self,
        *,
        pipeline_version: str,
        correlation_id: str,
        trace_id: str,
    ) -> RuntimeInitializedEvent:
        event = RuntimeInitializedEvent(
            event_id=str(uuid4()),
            pipeline_version=pipeline_version,
            correlation_id=correlation_id,
            trace_id=trace_id,
            occurred_at=utc_now(),
        )
        self.emit(
            InferenceLifecycleEventType.RUNTIME_INITIALIZED,
            request_id="",
            model_id="inference_pipeline",
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="runtime initialized",
            payload={"pipeline_version": pipeline_version},
        )
        return event

    def emit_inference_request_received(
        self,
        *,
        request_id: str,
        model_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> InferenceLifecycleEvent:
        return self.emit(
            InferenceLifecycleEventType.INFERENCE_REQUEST_RECEIVED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="inference request received",
        )

    def emit_features_bound(
        self,
        *,
        request_id: str,
        model_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> InferenceLifecycleEvent:
        return self.emit(
            InferenceLifecycleEventType.FEATURES_BOUND,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="features bound",
        )

    def emit_model_execution_started(
        self,
        *,
        request_id: str,
        model_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> InferenceLifecycleEvent:
        return self.emit(
            InferenceLifecycleEventType.MODEL_EXECUTION_STARTED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="model execution started",
        )

    def emit_model_execution_completed(
        self,
        *,
        request_id: str,
        model_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> InferenceLifecycleEvent:
        return self.emit(
            InferenceLifecycleEventType.MODEL_EXECUTION_COMPLETED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="model execution completed",
        )

    def emit_output_normalized(
        self,
        *,
        request_id: str,
        model_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> InferenceLifecycleEvent:
        return self.emit(
            InferenceLifecycleEventType.OUTPUT_NORMALIZED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="output normalized",
        )

    def emit_inference_completed(
        self,
        *,
        request_id: str,
        model_id: str,
        correlation_id: str,
        trace_id: str,
    ) -> InferenceLifecycleEvent:
        return self.emit(
            InferenceLifecycleEventType.INFERENCE_COMPLETED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="inference completed",
        )

    def emit_inference_failed(
        self,
        *,
        request_id: str,
        model_id: str,
        message: str,
        correlation_id: str,
        trace_id: str,
    ) -> InferenceLifecycleEvent:
        return self.emit(
            InferenceLifecycleEventType.INFERENCE_FAILED,
            request_id=request_id,
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
        )

    def _publish_to_event_bus(self, event: InferenceLifecycleEvent) -> None:
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=EventType.VALIDATION_COMPLETED,
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=INFRASTRUCTURE_ENTITY_ID,
            payload={
                "inference_pipeline_event_type": event.event_type.value,
                "request_id": event.request_id,
                "model_id": event.model_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._event_bus.publish(domain_event)
