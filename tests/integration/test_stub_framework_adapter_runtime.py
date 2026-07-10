"""Integration tests for stub framework adapter runtime vertical slice."""

from __future__ import annotations

import pytest

from feature_engineering import run_extraction_from_stream
from feature_store import FeatureStore, ingest_feature_set
from framework_adapters import (
    STUB_ADAPTER_ID,
    AdapterLifecycleEventType,
    AdapterState,
    bootstrap_adapter_runtime,
    lifecycle_event_types,
    process_stub_plugin,
    run_full_stub_adapter_pipeline,
)
from inference_pipeline import InferenceStatus, build_inference_runtime, prepare_production_model
from ml_engine_plugins import STUB_ENGINE_ID
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
        model_id="stub-adapter-model",
        model_name="Stub Adapter Model",
        experiment_id="stub-adapter-exp",
        dataset_id=dataset.dataset_id,
    )
    prepare_production_model(registry_runtime, model_id="stub-adapter-model")
    return build_inference_runtime(registry_runtime), dataset.dataset_id


@pytest.mark.integration
def test_stub_framework_adapter_full_vertical_slice() -> None:
    inference_runtime, dataset_id = _build_inference_stack()
    inference_response, execution_result, _ml_runtime, bridge, _adapter_runtime = (
        run_full_stub_adapter_pipeline(
            inference_runtime,
            model_id="stub-adapter-model",
            input_metadata={"feature_set_id": dataset_id},
        )
    )

    assert inference_response.status == InferenceStatus.COMPLETED
    assert execution_result.status == ExecutionStatus.COMPLETED
    assert execution_result.metadata is not None
    assert execution_result.metadata.executor_id == STUB_ENGINE_ID

    assert bridge.registry.lookup(STUB_ADAPTER_ID).metadata.engine_type.value == "stub"
    assert bridge.registry.lookup(STUB_ENGINE_ID).state == AdapterState.LOADED
    assert bridge.version_registry.get(STUB_ADAPTER_ID).adapter_id == STUB_ADAPTER_ID

    events = lifecycle_event_types(bridge)
    assert AdapterLifecycleEventType.ADAPTER_DISCOVERED in events
    assert AdapterLifecycleEventType.ADAPTER_REGISTERED in events
    assert AdapterLifecycleEventType.ADAPTER_VALIDATED in events
    assert AdapterLifecycleEventType.ADAPTER_LOADED in events

    stats = bridge.metrics_collector.statistics()
    assert stats.adapter_validations >= 1
    assert stats.adapter_loads >= 1
    assert stats.loaded_adapters >= 1

    bridge.health_checker.check(STUB_ENGINE_ID)
    bridge.shutdown_adapter(STUB_ENGINE_ID)
    assert AdapterLifecycleEventType.ADAPTER_SHUTDOWN in lifecycle_event_types(bridge)
    assert bridge.registry.lookup(STUB_ENGINE_ID).state == AdapterState.SHUTDOWN
    assert bridge.metrics_collector.statistics().adapter_shutdowns >= 1


@pytest.mark.integration
def test_stub_adapter_plugin_to_executor_runtime_path() -> None:
    inference_runtime, dataset_id = _build_inference_stack()
    ml_runtime, bridge, _adapter_runtime = bootstrap_adapter_runtime()
    process_stub_plugin(bridge)

    from inference_pipeline import run_inference_for_model

    inference_response = run_inference_for_model(
        inference_runtime,
        model_id="stub-adapter-model",
        input_metadata={"feature_set_id": dataset_id},
    )
    result = ml_runtime.execute(inference_response, executor_id=STUB_ENGINE_ID)
    assert result.status == ExecutionStatus.COMPLETED
    assert "stub" in result.message

    runtime_executor = ml_runtime.registry.lookup(STUB_ENGINE_ID)
    assert runtime_executor.executor_id() == STUB_ENGINE_ID
