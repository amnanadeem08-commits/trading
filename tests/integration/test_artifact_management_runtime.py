"""Integration tests for artifact management runtime vertical slice."""

from __future__ import annotations

from pathlib import Path

import pytest

from artifact_management import (
    ArtifactLifecycleEventType,
    ArtifactState,
    lifecycle_event_types,
)
from config.settings import AppSettings
from feature_engineering import run_extraction_from_stream
from feature_store import FeatureStore, ingest_feature_set
from framework_adapters import create_stub_adapter, process_stub_plugin
from inference_pipeline import InferenceStatus, build_inference_runtime, prepare_production_model
from ml_engine_plugins import STUB_ENGINE_ID
from ml_runtime import ExecutionStatus
from model_registry import build_model_registry_runtime, register_model_from_training
from storage_providers import bootstrap_storage_runtime, provider_lifecycle_event_types
from storage_providers.lifecycle.provider_lifecycle import ProviderLifecycleEventType
from tests.artifact_management_helpers import STUB_ARTIFACT_ID
from tests.feature_engineering_helpers import seed_historical_and_stream
from tests.storage_providers_helpers import make_local_artifact_bundle
from training_pipeline import build_training_runtime


def _build_inference_stack() -> tuple[object, str]:
    _, stream = seed_historical_and_stream(record_count=3)
    extraction = run_extraction_from_stream(stream, max_batches=1)
    assert extraction.feature_set is not None

    store = FeatureStore()
    dataset = ingest_feature_set(store, extraction.feature_set)
    training_runtime = build_training_runtime(store)
    registry_runtime = build_model_registry_runtime(training_runtime, approval_required=False)
    register_model_from_training(
        registry_runtime,
        model_id="artifact-model",
        model_name="Artifact Model",
        experiment_id="artifact-exp",
        dataset_id=dataset.dataset_id,
    )
    prepare_production_model(registry_runtime, model_id="artifact-model")
    return build_inference_runtime(registry_runtime), dataset.dataset_id


@pytest.mark.integration
def test_artifact_management_full_vertical_slice() -> None:
    inference_runtime, dataset_id = _build_inference_stack()
    ml_runtime, adapter_bridge, artifact_bridge, storage_bridge = bootstrap_storage_runtime()
    process_stub_plugin(adapter_bridge, plugin_id=STUB_ENGINE_ID)

    adapter = create_stub_adapter()
    artifact_root = Path(AppSettings.from_sources().storage_providers.artifact_root)
    reference, metadata, manifest, _checksum = make_local_artifact_bundle(
        artifact_root,
        artifact_id=STUB_ARTIFACT_ID,
    )
    executor = storage_bridge.load_through_adapter(
        adapter,
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    ml_runtime.register_executor(
        executor, name="Stub", version="1.0.0", capabilities=("load_artifact",)
    )

    from inference_pipeline import run_inference_for_model

    inference_response = run_inference_for_model(
        inference_runtime,
        model_id="artifact-model",
        input_metadata={"feature_set_id": dataset_id},
    )
    result = ml_runtime.execute(inference_response, executor_id=STUB_ENGINE_ID)
    assert inference_response.status == InferenceStatus.COMPLETED
    assert result.status == ExecutionStatus.COMPLETED
    assert artifact_bridge.registry.lookup(STUB_ARTIFACT_ID).state == ArtifactState.CACHED

    events = lifecycle_event_types(artifact_bridge)
    assert ArtifactLifecycleEventType.ARTIFACT_REGISTERED in events
    assert ArtifactLifecycleEventType.ARTIFACT_RESOLVED in events
    assert ArtifactLifecycleEventType.ARTIFACT_VALIDATED in events
    assert ArtifactLifecycleEventType.ARTIFACT_CACHED in events

    provider_events = provider_lifecycle_event_types(storage_bridge)
    assert ProviderLifecycleEventType.PROVIDER_REGISTERED in provider_events
    assert ProviderLifecycleEventType.PROVIDER_RESOLVED in provider_events

    stats = artifact_bridge.metrics_collector.statistics()
    assert stats.artifact_registrations >= 1
    assert stats.artifact_resolutions >= 1
    assert stats.artifact_validations >= 1

    artifact_bridge.health_checker.check(STUB_ARTIFACT_ID)
    artifact_bridge.expire_cached(STUB_ARTIFACT_ID)
    assert ArtifactLifecycleEventType.ARTIFACT_EXPIRED in lifecycle_event_types(artifact_bridge)


@pytest.mark.integration
def test_storage_provider_resolution_to_adapter_load_path() -> None:
    inference_runtime, dataset_id = _build_inference_stack()
    ml_runtime, adapter_bridge, _artifact_bridge, storage_bridge = bootstrap_storage_runtime()
    adapter = create_stub_adapter()
    artifact_root = Path(AppSettings.from_sources().storage_providers.artifact_root)
    reference, metadata, manifest, _checksum = make_local_artifact_bundle(artifact_root)
    resolved = storage_bridge.resolve_through_provider(
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    assert resolved.location is not None
    executor = storage_bridge.load_through_adapter(
        adapter,
        reference=reference,
        metadata=metadata,
        manifest=manifest,
    )
    process_stub_plugin(adapter_bridge, plugin_id=STUB_ENGINE_ID)

    from inference_pipeline import run_inference_for_model

    inference_response = run_inference_for_model(
        inference_runtime,
        model_id="artifact-model",
        input_metadata={"feature_set_id": dataset_id},
    )
    execution = ml_runtime.execute(inference_response, executor_id=STUB_ENGINE_ID)
    _ = executor
    assert execution.status == ExecutionStatus.COMPLETED
