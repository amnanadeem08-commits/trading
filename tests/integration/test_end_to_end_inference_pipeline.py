"""Integration tests for end-to-end inference execution pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

from framework_adapters import ORT_ADAPTER_ID, bootstrap_adapter_runtime
from framework_adapters.integration.inference_execution_bridge import build_execution_router
from inference_pipeline import InferenceLifecycleEventType, InferenceStatus
from inference_pipeline.runtime.inference_execution_pipeline import InferenceExecutionPipeline
from inference_pipeline.runtime.inference_request import InferenceExecutionRequest
from tests.framework_adapters.ort_helpers import make_ort_artifact_bundle, ort_engine_type
from tests.inference_pipeline.execution_helpers import make_identity_input_schema
from tests.integration.test_artifact_management_runtime import _build_inference_stack
from tests.storage_providers_helpers import make_local_storage_bridge

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.integration
def test_end_to_end_inference_execution_pipeline(tmp_path: Path) -> None:
    inference_runtime, _dataset_id = _build_inference_stack()
    reference, metadata, manifest, checksum = make_ort_artifact_bundle(tmp_path)
    _ml_runtime, _bridge, adapter_runtime = bootstrap_adapter_runtime()
    storage_bridge = make_local_storage_bridge(tmp_path)
    manager = adapter_runtime.model_runtime_manager

    resolved = storage_bridge.resolve_through_provider(
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    assert resolved.location is not None

    from framework_adapters import AdapterRuntimeContext

    adapter_context = AdapterRuntimeContext(
        engine_type=ort_engine_type(),
        artifact_format="ort",
        artifact_reference=resolved.uri,
        model_id="artifact-model",
        model_version=resolved.version,
        executor_id=ORT_ADAPTER_ID,
        attributes={
            "artifact_id": resolved.artifact_id,
            "checksum": checksum,
            "checksum_verified": True,
            "opset_version": 17,
            "location": resolved.location.model_dump(),
        },
    )
    manager.get_or_load_model(ORT_ADAPTER_ID, context=adapter_context)

    pipeline = InferenceExecutionPipeline(
        inference_runtime=inference_runtime,
        lifecycle=inference_runtime.lifecycle,
        metrics=inference_runtime.metrics_collector,
        router=build_execution_router(adapter_runtime),
    )
    response = pipeline.execute(
        InferenceExecutionRequest(
            request_id=str(uuid4()),
            model_id="artifact-model",
            input_schema=make_identity_input_schema(),
            features={"X": 6.0},
            adapter_id=ORT_ADAPTER_ID,
            artifact_id=resolved.artifact_id,
            correlation_id="exec-correlation",
            trace_id="exec-trace",
            execution_attributes={
                "location": resolved.location.model_dump(),
                "artifact_format": "ort",
                "artifact_reference": resolved.uri,
            },
        )
    )

    assert response.status == InferenceStatus.COMPLETED
    assert response.normalized_output["values"]
    assert response.execution_attributes.get("inference_outputs") is not None

    stats = inference_runtime.metrics_collector.statistics()
    assert stats.execution_latency_ms >= 0.0
    assert stats.total_inference_latency_ms >= 0.0

    event_types = {event.event_type for event in inference_runtime.lifecycle.events}
    assert InferenceLifecycleEventType.MODEL_EXECUTION_STARTED in event_types
    assert InferenceLifecycleEventType.MODEL_EXECUTION_COMPLETED in event_types
    assert InferenceLifecycleEventType.INFERENCE_COMPLETED in event_types

    manager.shutdown()
    storage_bridge.shutdown_provider("local-provider")
