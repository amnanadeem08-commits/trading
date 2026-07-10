"""Integration tests for adapter runtime routing."""

from __future__ import annotations

import pytest

from feature_engineering import run_extraction_from_stream
from feature_store import FeatureStore, ingest_feature_set
from framework_adapters import (
    STUB_ADAPTER_ID,
    AdapterLifecycleEventType,
    AdapterRuntimeContext,
    AdapterState,
    EngineType,
    bootstrap_adapter_runtime,
)
from inference_pipeline import (
    InferenceStatus,
    build_inference_runtime,
    prepare_production_model,
    run_inference_for_model,
)
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
        model_id="runtime-routing-model",
        model_name="Runtime Routing Model",
        experiment_id="runtime-routing-exp",
        dataset_id=dataset.dataset_id,
    )
    prepare_production_model(registry_runtime, model_id="runtime-routing-model")
    return build_inference_runtime(registry_runtime), dataset.dataset_id


@pytest.mark.integration
def test_adapter_runtime_routes_execution_through_ml_runtime() -> None:
    inference_runtime, dataset_id = _build_inference_stack()
    _ml_runtime, bridge, adapter_runtime = bootstrap_adapter_runtime()

    inference_response = run_inference_for_model(
        inference_runtime,
        model_id="runtime-routing-model",
        input_metadata={"feature_set_id": dataset_id},
    )
    assert inference_response.status == InferenceStatus.COMPLETED

    context = AdapterRuntimeContext(
        engine_type=EngineType.STUB,
        artifact_format="stub",
        artifact_reference="artifacts/runtime-routing-model.stub",
        model_id="runtime-routing-model",
        executor_id=STUB_ENGINE_ID,
    )
    result = adapter_runtime.route_execution(inference_response, context=context)
    assert result.status == ExecutionStatus.COMPLETED

    event_types = {event.event_type for event in bridge.lifecycle.events}
    assert AdapterLifecycleEventType.ADAPTER_INITIALIZED in event_types
    assert AdapterLifecycleEventType.ADAPTER_SELECTED in event_types
    assert AdapterLifecycleEventType.ADAPTER_LOADED in event_types

    stats = bridge.metrics_collector.statistics()
    assert stats.adapter_executions >= 1
    assert stats.adapter_usage >= 1
    assert bridge.registry.lookup(STUB_ADAPTER_ID).state == AdapterState.LOADED
