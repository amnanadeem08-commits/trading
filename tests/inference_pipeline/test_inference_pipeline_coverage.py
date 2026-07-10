"""Extended unit tests for inference pipeline coverage."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from inference_pipeline import (
    InferenceDispatchError,
    InferenceLifecycleEventType,
    InferenceLifecycleManager,
    InferenceQueue,
    InferenceRequest,
    InferenceRequestNotFoundError,
    InferenceStatus,
    InferenceValidationError,
    ModelLoader,
    ModelResolutionError,
)
from inference_pipeline.responses.inference_metadata import InferenceMetadata
from metrics.registry import MetricRegistry
from tests.inference_pipeline_helpers import make_inference_runtime


@pytest.mark.unit
def test_model_loader_resolution_errors() -> None:
    runtime = make_inference_runtime()
    loader = ModelLoader(runtime.model_registry)
    with pytest.raises(ModelResolutionError):
        loader.resolve_production_version("missing")


@pytest.mark.unit
def test_inference_queue_operations() -> None:
    queue = InferenceQueue(max_size=2)
    request = InferenceRequest(
        request_id="req-q1",
        model_id="model-1",
        input_metadata={"id": "1"},
    )
    queue.enqueue(request)
    assert queue.size() == 1
    assert queue.peek() is not None
    dequeued = queue.dequeue()
    assert dequeued is not None
    with pytest.raises(InferenceRequestNotFoundError):
        queue.get("missing")


@pytest.mark.unit
def test_inference_queue_capacity() -> None:
    queue = InferenceQueue(max_size=1)
    request = InferenceRequest(
        request_id="req-1",
        model_id="model-1",
        input_metadata={"id": "1"},
    )
    queue.enqueue(request)
    with pytest.raises(InferenceDispatchError):
        queue.enqueue(
            InferenceRequest(
                request_id="req-2",
                model_id="model-1",
                input_metadata={"id": "2"},
            )
        )


@pytest.mark.unit
def test_dispatcher_cancel() -> None:
    runtime = make_inference_runtime()
    request = InferenceRequest(
        request_id="req-cancel",
        model_id="model-1",
        input_metadata={"id": "1"},
        correlation_id="c",
        trace_id="t",
    )
    result = runtime.dispatcher.cancel(request)
    assert result.status == InferenceStatus.CANCELLED


@pytest.mark.unit
def test_dispatcher_fails_without_production_model() -> None:
    training_runtime = __import__(
        "tests.training_pipeline_helpers", fromlist=["make_training_runtime"]
    ).make_training_runtime()
    from inference_pipeline import build_inference_runtime
    from model_registry import build_model_registry_runtime, register_model_from_training

    registry_runtime = build_model_registry_runtime(
        training_runtime,
        approval_required=False,
    )
    register_model_from_training(
        registry_runtime,
        model_id="draft-model",
        model_name="Draft",
        experiment_id="exp-draft",
        dataset_id="dataset-1",
    )
    runtime = build_inference_runtime(registry_runtime)
    request = InferenceRequest(
        request_id="req-fail",
        model_id="draft-model",
        input_metadata={"id": "1"},
        correlation_id="c",
        trace_id="t",
    )
    runtime.scheduler.submit(request)
    from inference_pipeline.scheduler.inference_queue import QueuedInferenceRequest

    queued = runtime.queue.dequeue()
    assert isinstance(queued, QueuedInferenceRequest)
    response = runtime.dispatcher.dispatch(queued)
    assert response.status == InferenceStatus.FAILED


@pytest.mark.unit
def test_validator_metadata_and_ensure_valid() -> None:
    from inference_pipeline import InferenceValidator

    validator = InferenceValidator()
    metadata = InferenceMetadata(
        request_id="",
        model_id="model-1",
        version_id="",
        artifact_id="",
        config_hash="",
        checksum="",
        stage="production",
        correlation_id="c",
        trace_id="t",
        started_at=__import__("models.common", fromlist=["utc_now"]).utc_now(),
    )
    result = validator.validate_metadata(metadata)
    assert result.valid is False
    with pytest.raises(InferenceValidationError):
        validator.ensure_valid(result)


@pytest.mark.unit
def test_lifecycle_model_resolved_and_runtime_initialized() -> None:
    lifecycle = InferenceLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_model_resolved(
        model_id="model-1",
        version_id="v-1",
        artifact_id="artifact-1",
        correlation_id="c",
        trace_id="t",
    )
    lifecycle.emit_runtime_initialized(
        pipeline_version="1.0.0",
        correlation_id="c",
        trace_id="t",
    )
    subscription = lifecycle.on_event(lambda _event: None)
    lifecycle.off_event(subscription)
    types = {event.event_type for event in lifecycle.events}
    assert InferenceLifecycleEventType.MODEL_RESOLVED in types
    assert InferenceLifecycleEventType.RUNTIME_INITIALIZED in types
