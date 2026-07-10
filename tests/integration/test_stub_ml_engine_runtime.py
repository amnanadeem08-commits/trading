"""Integration tests for the concrete stub ML engine vertical slice."""

from __future__ import annotations

import pytest

from feature_engineering import run_extraction_from_stream
from feature_store import FeatureStore, ingest_feature_set
from inference_pipeline import InferenceStatus, build_inference_runtime, prepare_production_model
from ml_engine_plugins import (
    STUB_ENGINE_ID,
    PluginLifecycleEventType,
    PluginState,
    bootstrap_plugin_runtime,
    lifecycle_event_types,
    run_full_stub_engine_pipeline,
)
from ml_runtime import ExecutionStatus
from model_registry import build_model_registry_runtime, register_model_from_training
from tests.feature_engineering_helpers import seed_historical_and_stream
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
        model_id="stub-model",
        model_name="Stub Model",
        experiment_id="stub-exp",
        dataset_id=dataset.dataset_id,
    )
    prepare_production_model(registry_runtime, model_id="stub-model")
    return build_inference_runtime(registry_runtime), dataset.dataset_id


@pytest.mark.integration
def test_stub_engine_full_vertical_slice() -> None:
    inference_runtime, dataset_id = _build_inference_stack()
    inference_response, execution_result, ml_runtime, bridge = run_full_stub_engine_pipeline(
        inference_runtime,
        model_id="stub-model",
        input_metadata={"feature_set_id": dataset_id},
    )

    assert inference_response.status == InferenceStatus.COMPLETED
    assert execution_result.status == ExecutionStatus.COMPLETED
    assert execution_result.metadata is not None
    assert execution_result.metadata.executor_id == STUB_ENGINE_ID
    assert "stub" in execution_result.message

    assert ml_runtime.registry.metadata(STUB_ENGINE_ID) is not None
    assert bridge.registry.lookup(STUB_ENGINE_ID).state in {
        PluginState.LOADED,
        PluginState.REGISTERED,
        PluginState.HEALTHY,
    }
    assert bridge.version_registry.latest() is not None

    events = lifecycle_event_types(bridge)
    assert PluginLifecycleEventType.PLUGIN_DISCOVERED in events
    assert PluginLifecycleEventType.PLUGIN_REGISTERED in events
    assert PluginLifecycleEventType.PLUGIN_LOADED in events
    assert PluginLifecycleEventType.PLUGIN_VALIDATED in events

    bridge.health_check(STUB_ENGINE_ID)
    assert PluginLifecycleEventType.PLUGIN_HEALTH_CHECKED in lifecycle_event_types(bridge)
    assert bridge.metrics_collector.statistics().loaded_plugins >= 1

    bridge.unload(STUB_ENGINE_ID)
    assert PluginLifecycleEventType.PLUGIN_UNLOADED in lifecycle_event_types(bridge)
    assert bridge.registry.lookup(STUB_ENGINE_ID).state == PluginState.UNLOADED


@pytest.mark.integration
def test_stub_engine_executor_load_unload_during_runtime_execute() -> None:
    inference_runtime, dataset_id = _build_inference_stack()
    ml_runtime, bridge = bootstrap_plugin_runtime()
    plugin = bridge.registry.get_plugin(STUB_ENGINE_ID)
    executor = plugin.create_executor()
    assert isinstance(executor, object)

    from inference_pipeline import run_inference_for_model

    inference_response = run_inference_for_model(
        inference_runtime,
        model_id="stub-model",
        input_metadata={"feature_set_id": dataset_id},
    )
    result = ml_runtime.execute(inference_response, executor_id=STUB_ENGINE_ID)
    assert result.status == ExecutionStatus.COMPLETED

    runtime_executor = ml_runtime.registry.lookup(STUB_ENGINE_ID)
    assert runtime_executor.executor_id() == STUB_ENGINE_ID
