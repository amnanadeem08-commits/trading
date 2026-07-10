"""Integration tests for real model pipeline execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from artifact_management import ArtifactState
from framework_adapters import (
    ORT_ADAPTER_ID,
    AdapterLifecycleEventType,
    bootstrap_adapter_runtime,
    create_ort_adapter,
)
from inference_pipeline import InferenceStatus, run_inference_for_model
from ml_runtime import ExecutionStatus
from storage_providers import (
    LOCAL_PROVIDER_ID,
    ProviderLifecycleEventType,
    provider_lifecycle_event_types,
)
from tests.framework_adapters.ort_helpers import make_ort_artifact_bundle
from tests.integration.test_artifact_management_runtime import _build_inference_stack
from tests.storage_providers_helpers import make_local_storage_bridge

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.integration
def test_real_model_pipeline_through_storage_and_runtime(tmp_path: Path) -> None:
    inference_runtime, dataset_id = _build_inference_stack()
    reference, metadata, manifest, _checksum = make_ort_artifact_bundle(tmp_path)
    ml_runtime, bridge, _adapter_runtime = bootstrap_adapter_runtime()
    storage_bridge = make_local_storage_bridge(tmp_path)
    adapter = create_ort_adapter()

    executor = storage_bridge.load_through_adapter(
        adapter,
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    record = bridge.registry.lookup(ORT_ADAPTER_ID)
    bridge.register_executor(
        executor,
        name=record.metadata.name,
        version=record.metadata.version,
        capabilities=tuple(cap.value for cap in adapter.capabilities()),
    )

    inference_response = run_inference_for_model(
        inference_runtime,
        model_id="artifact-model",
        input_metadata={"feature_set_id": dataset_id, "input": [[3.0]]},
    )
    assert inference_response.status == InferenceStatus.COMPLETED

    result = ml_runtime.execute(inference_response, executor_id=ORT_ADAPTER_ID)
    assert result.status == ExecutionStatus.COMPLETED
    assert result.metadata is not None
    assert result.metadata.executor_id == ORT_ADAPTER_ID
    assert result.metadata.attributes.get("inference_outputs") is not None

    assert (
        storage_bridge.artifact_registry.lookup(reference.artifact_id).state == ArtifactState.CACHED
    )
    event_types = {event.event_type for event in bridge.lifecycle.events}
    assert AdapterLifecycleEventType.ADAPTER_INITIALIZED in event_types

    provider_events = provider_lifecycle_event_types(storage_bridge)
    assert ProviderLifecycleEventType.PROVIDER_RESOLVED in provider_events
    assert ProviderLifecycleEventType.CHECKSUM_VERIFIED in provider_events
    stats = storage_bridge.provider_metrics_collector.statistics()
    assert stats.provider_usage[LOCAL_PROVIDER_ID] >= 1
    assert bridge.metrics_collector.statistics().adapter_loads >= 0

    storage_bridge.shutdown_provider(LOCAL_PROVIDER_ID)
