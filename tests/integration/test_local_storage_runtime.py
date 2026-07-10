"""Integration tests for local storage provider pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from artifact_management import ArtifactState
from framework_adapters import create_stub_adapter, process_stub_plugin
from inference_pipeline import InferenceStatus, run_inference_for_model
from ml_engine_plugins import STUB_ENGINE_ID
from ml_runtime import ExecutionStatus
from storage_providers import (
    LOCAL_PROVIDER_ID,
    ProviderLifecycleEventType,
    bootstrap_storage_runtime,
    provider_lifecycle_event_types,
)
from tests.integration.test_artifact_management_runtime import _build_inference_stack
from tests.storage_providers_helpers import (
    make_local_artifact_bundle,
    make_local_storage_bridge,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.integration
def test_local_provider_full_vertical_slice(tmp_path: Path) -> None:
    inference_runtime, dataset_id = _build_inference_stack()
    reference, metadata, manifest, _checksum = make_local_artifact_bundle(tmp_path)
    ml_runtime, adapter_bridge, _, _ = bootstrap_storage_runtime()
    storage_bridge = make_local_storage_bridge(tmp_path)
    process_stub_plugin(adapter_bridge, plugin_id=STUB_ENGINE_ID)

    adapter = create_stub_adapter()
    executor = storage_bridge.load_through_adapter(
        adapter,
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    ml_runtime.register_executor(
        executor, name="Stub", version="1.0.0", capabilities=("load_artifact",)
    )

    inference_response = run_inference_for_model(
        inference_runtime,
        model_id="artifact-model",
        input_metadata={"feature_set_id": dataset_id},
    )
    result = ml_runtime.execute(inference_response, executor_id=STUB_ENGINE_ID)
    assert inference_response.status == InferenceStatus.COMPLETED
    assert result.status == ExecutionStatus.COMPLETED
    assert storage_bridge.artifact_registry.lookup(reference.artifact_id).state == (
        ArtifactState.CACHED
    )

    event_types = provider_lifecycle_event_types(storage_bridge)
    assert ProviderLifecycleEventType.PROVIDER_REGISTERED in event_types
    assert ProviderLifecycleEventType.PROVIDER_STARTUP in event_types
    assert ProviderLifecycleEventType.PROVIDER_VALIDATED in event_types
    assert ProviderLifecycleEventType.PROVIDER_RESOLVED in event_types
    assert ProviderLifecycleEventType.CHECKSUM_VERIFIED in event_types

    stats = storage_bridge.provider_metrics_collector.statistics()
    assert stats.provider_usage[LOCAL_PROVIDER_ID] >= 1
    assert stats.filesystem_lookups >= 1
    assert stats.checksum_operations >= 1

    storage_bridge.shutdown_provider(LOCAL_PROVIDER_ID)
    assert ProviderLifecycleEventType.PROVIDER_SHUTDOWN in provider_lifecycle_event_types(
        storage_bridge
    )
