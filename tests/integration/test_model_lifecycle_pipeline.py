"""Integration tests for model lifecycle pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from framework_adapters import (
    ORT_ADAPTER_ID,
    AdapterLifecycleEventType,
    AdapterRuntimeContext,
    bootstrap_adapter_runtime,
)
from inference_pipeline import InferenceStatus, run_inference_for_model
from ml_runtime import ExecutionStatus
from tests.framework_adapters.ort_helpers import make_ort_artifact_bundle, ort_engine_type
from tests.integration.test_artifact_management_runtime import _build_inference_stack
from tests.storage_providers_helpers import make_local_storage_bridge

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.integration
def test_model_lifecycle_pipeline_with_storage_and_runtime_manager(tmp_path: Path) -> None:
    inference_runtime, dataset_id = _build_inference_stack()
    reference, metadata, manifest, checksum = make_ort_artifact_bundle(tmp_path)
    ml_runtime, bridge, adapter_runtime = bootstrap_adapter_runtime()
    storage_bridge = make_local_storage_bridge(tmp_path)
    manager = adapter_runtime.model_runtime_manager

    resolved = storage_bridge.resolve_through_provider(
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    assert resolved.location is not None

    context = AdapterRuntimeContext(
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

    first = manager.get_or_load_model(ORT_ADAPTER_ID, context=context)
    second = manager.get_or_load_model(ORT_ADAPTER_ID, context=context)
    assert first.executor_id() == ORT_ADAPTER_ID
    assert second.executor_id() == ORT_ADAPTER_ID

    inference_response = run_inference_for_model(
        inference_runtime,
        model_id="artifact-model",
        input_metadata={"feature_set_id": dataset_id, "input": [[4.0]]},
    )
    assert inference_response.status == InferenceStatus.COMPLETED
    result = ml_runtime.execute(inference_response, executor_id=ORT_ADAPTER_ID)
    assert result.status == ExecutionStatus.COMPLETED
    assert result.metadata is not None
    assert result.metadata.attributes.get("inference_outputs") is not None

    stats = bridge.metrics_collector.statistics()
    assert stats.cache_hits >= 1
    event_types = {event.event_type for event in bridge.lifecycle.events}
    assert AdapterLifecycleEventType.MODEL_REUSED in event_types

    session_key = manager.build_session_key(ORT_ADAPTER_ID, context=context)
    reloaded = manager.reload_model(session_key, context=context, adapter_id=ORT_ADAPTER_ID)
    assert reloaded.executor_id() == ORT_ADAPTER_ID
    assert bridge.metrics_collector.statistics().model_reload_count >= 1

    manager.shutdown()
    storage_bridge.shutdown_provider("local-provider")
