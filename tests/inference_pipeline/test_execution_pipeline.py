"""Unit tests for inference execution pipeline."""

from __future__ import annotations

from uuid import uuid4

import pytest

from inference_pipeline import InferenceLifecycleEventType, InferenceStatus
from inference_pipeline.runtime.execution_router import ExecutionOutcomeAdapter
from inference_pipeline.runtime.inference_execution_pipeline import InferenceExecutionPipeline
from inference_pipeline.runtime.inference_request import InferenceExecutionRequest
from tests.inference_pipeline.execution_helpers import make_identity_input_schema
from tests.inference_pipeline_helpers import make_inference_runtime


class _StubRouter:
    def route(
        self, inference_response, *, execution_context, bound_input
    ) -> ExecutionOutcomeAdapter:
        _ = inference_response, execution_context, bound_input
        return ExecutionOutcomeAdapter(
            status="completed",
            attributes={"inference_outputs": [[[5.0]]]},
        )


@pytest.mark.unit
def test_execution_pipeline_runs_full_path_with_stub_router() -> None:
    runtime = make_inference_runtime()
    pipeline = InferenceExecutionPipeline(
        inference_runtime=runtime,
        lifecycle=runtime.lifecycle,
        metrics=runtime.metrics_collector,
        router=_StubRouter(),
    )
    request = InferenceExecutionRequest(
        request_id=str(uuid4()),
        model_id="model-1",
        input_schema=make_identity_input_schema(),
        features={"X": 3.0},
        adapter_id="stub-framework-adapter",
    )
    response = pipeline.execute(request)
    assert response.status == InferenceStatus.COMPLETED
    assert response.normalized_output["values"] == [5.0]
    stats = runtime.metrics_collector.statistics()
    assert stats.feature_mapping_ms >= 0.0
    assert stats.total_inference_latency_ms >= 0.0
    event_types = {event.event_type for event in runtime.lifecycle.events}
    assert InferenceLifecycleEventType.INFERENCE_REQUEST_RECEIVED in event_types
    assert InferenceLifecycleEventType.FEATURES_BOUND in event_types
    assert InferenceLifecycleEventType.OUTPUT_NORMALIZED in event_types


@pytest.mark.unit
def test_execution_pipeline_rejects_missing_feature() -> None:
    runtime = make_inference_runtime()
    pipeline = InferenceExecutionPipeline(
        inference_runtime=runtime,
        lifecycle=runtime.lifecycle,
        metrics=runtime.metrics_collector,
        router=_StubRouter(),
    )
    request = InferenceExecutionRequest(
        request_id=str(uuid4()),
        model_id="model-1",
        input_schema=make_identity_input_schema(),
        features={},
    )
    response = pipeline.execute(request)
    assert response.status == InferenceStatus.FAILED
    assert runtime.metrics_collector.statistics().validation_failures >= 1
