"""Integration tests for framework adapter bridge vertical slice."""

from __future__ import annotations

import pytest

from feature_engineering import run_extraction_from_stream
from feature_store import FeatureStore, ingest_feature_set
from framework_adapters import AdapterLifecycleEventType, AdapterState
from inference_pipeline import InferenceStatus, build_inference_runtime, prepare_production_model
from ml_engine_plugins import STUB_ENGINE_ID, create_stub_engine
from ml_runtime import ExecutionStatus
from model_registry import build_model_registry_runtime, register_model_from_training
from tests.feature_engineering_helpers import seed_historical_and_stream
from tests.framework_adapters_helpers import make_adapter_bridge
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
        model_id="adapter-model",
        model_name="Adapter Model",
        experiment_id="adapter-exp",
        dataset_id=dataset.dataset_id,
    )
    prepare_production_model(registry_runtime, model_id="adapter-model")
    return build_inference_runtime(registry_runtime), dataset.dataset_id


@pytest.mark.integration
def test_framework_adapter_bridge_vertical_slice() -> None:
    inference_runtime, dataset_id = _build_inference_stack()
    ml_runtime, bridge = make_adapter_bridge()
    plugin = create_stub_engine()
    executor = bridge.process_plugin(plugin)
    assert executor.executor_id() == STUB_ENGINE_ID

    from inference_pipeline import run_inference_for_model

    inference_response = run_inference_for_model(
        inference_runtime,
        model_id="adapter-model",
        input_metadata={"feature_set_id": dataset_id},
    )
    result = ml_runtime.execute(inference_response, executor_id=STUB_ENGINE_ID)
    assert result.status == ExecutionStatus.COMPLETED
    assert bridge.registry.lookup(STUB_ENGINE_ID).state == AdapterState.LOADED

    event_types = {event.event_type for event in bridge.lifecycle.events}
    assert AdapterLifecycleEventType.ADAPTER_DISCOVERED in event_types
    assert AdapterLifecycleEventType.ADAPTER_LOADED in event_types

    bridge.health_checker.check(STUB_ENGINE_ID)
    assert bridge.metrics_collector.statistics().loaded_adapters >= 1

    bridge.shutdown_adapter(STUB_ENGINE_ID)
    assert bridge.registry.lookup(STUB_ENGINE_ID).state == AdapterState.SHUTDOWN


@pytest.mark.integration
def test_inference_completes_through_adapter_bridge() -> None:
    inference_runtime, dataset_id = _build_inference_stack()
    ml_runtime, bridge = make_adapter_bridge()
    bridge.process_plugin(create_stub_engine())

    from inference_pipeline import run_inference_for_model

    inference_response = run_inference_for_model(
        inference_runtime,
        model_id="adapter-model",
        input_metadata={"feature_set_id": dataset_id},
    )
    assert inference_response.status == InferenceStatus.COMPLETED
    execution = ml_runtime.execute(inference_response, executor_id=STUB_ENGINE_ID)
    assert execution.status == ExecutionStatus.COMPLETED
