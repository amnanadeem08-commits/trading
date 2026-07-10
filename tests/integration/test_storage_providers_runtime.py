"""Integration tests for storage provider pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from artifact_management import ArtifactState
from config.settings import AppSettings
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
from tests.artifact_management_helpers import STUB_ARTIFACT_ID
from tests.integration.test_artifact_management_runtime import _build_inference_stack
from tests.storage_providers_helpers import make_local_artifact_bundle


@pytest.mark.integration
def test_storage_provider_full_vertical_slice() -> None:
    inference_runtime, dataset_id = _build_inference_stack()
    artifact_root = Path(AppSettings.from_sources().storage_providers.artifact_root)
    reference, metadata, manifest, _checksum = make_local_artifact_bundle(
        artifact_root,
        artifact_id=STUB_ARTIFACT_ID,
    )
    ml_runtime, adapter_bridge, _, storage_bridge = bootstrap_storage_runtime()
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
    assert storage_bridge.artifact_registry.lookup(STUB_ARTIFACT_ID).state == ArtifactState.CACHED

    event_types = provider_lifecycle_event_types(storage_bridge)
    assert ProviderLifecycleEventType.PROVIDER_REGISTERED in event_types
    assert ProviderLifecycleEventType.PROVIDER_STARTUP in event_types
    assert ProviderLifecycleEventType.PROVIDER_VALIDATED in event_types
    assert ProviderLifecycleEventType.PROVIDER_RESOLVED in event_types
    assert ProviderLifecycleEventType.CHECKSUM_VERIFIED in event_types

    stats = storage_bridge.provider_metrics_collector.statistics()
    assert stats.provider_resolutions >= 1
    assert stats.provider_usage[LOCAL_PROVIDER_ID] >= 1

    storage_bridge.shutdown_default_providers()
    assert ProviderLifecycleEventType.PROVIDER_SHUTDOWN in provider_lifecycle_event_types(
        storage_bridge
    )


@pytest.mark.integration
def test_bootstrap_storage_runtime_wires_bridges() -> None:
    ml_runtime, adapter_bridge, artifact_bridge, storage_bridge = bootstrap_storage_runtime()
    assert ml_runtime is not None
    assert adapter_bridge is not None
    assert artifact_bridge is not None
    assert storage_bridge is not None
    assert storage_bridge.artifact_bridge is artifact_bridge
    assert storage_bridge.provider_registry.lookup(LOCAL_PROVIDER_ID) is not None


@pytest.mark.integration
def test_provider_lifecycle_event_types_helper() -> None:
    from tests.storage_providers_helpers import make_storage_bridge_with_artifact_bundle

    bridge, reference, metadata, manifest = make_storage_bridge_with_artifact_bundle()
    bridge.resolve_through_provider(
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    event_types = provider_lifecycle_event_types(bridge)
    assert ProviderLifecycleEventType.PROVIDER_VALIDATED in event_types
    assert ProviderLifecycleEventType.PROVIDER_RESOLVED in event_types
