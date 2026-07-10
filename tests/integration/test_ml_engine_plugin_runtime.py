"""Integration tests for ML engine plugin runtime."""

from __future__ import annotations

import pytest

from feature_engineering import run_extraction_from_stream
from feature_store import FeatureStore, ingest_feature_set
from inference_pipeline import (
    InferenceStatus,
    build_inference_runtime,
    prepare_production_model,
    run_inference_for_model,
)
from ml_engine_plugins import StubMLEnginePlugin, build_plugin_bridge
from ml_runtime import ExecutionStatus, build_ml_runtime
from model_registry import build_model_registry_runtime, register_model_from_training
from tests.feature_engineering_helpers import seed_historical_and_stream
from training_pipeline import build_training_runtime


@pytest.mark.integration
def test_full_pipeline_with_plugin_bridge() -> None:
    _, stream = seed_historical_and_stream(record_count=3)
    extraction = run_extraction_from_stream(stream, max_batches=1)
    assert extraction.feature_set is not None

    store = FeatureStore()
    dataset = ingest_feature_set(store, extraction.feature_set)
    training_runtime = build_training_runtime(store)
    registry_runtime = build_model_registry_runtime(training_runtime, approval_required=False)
    register_model_from_training(
        registry_runtime,
        model_id="plugin-model",
        model_name="Plugin Model",
        experiment_id="plugin-exp",
        dataset_id=dataset.dataset_id,
    )
    prepare_production_model(registry_runtime, model_id="plugin-model")

    inference_runtime = build_inference_runtime(registry_runtime)
    ml_runtime = build_ml_runtime()
    bridge = build_plugin_bridge(ml_runtime)
    bridge.register_provider(StubMLEnginePlugin(plugin_id="integration-engine"))
    bridge.discover_and_load()

    inference_response = run_inference_for_model(
        inference_runtime,
        model_id="plugin-model",
        input_metadata={"feature_set_id": dataset.dataset_id},
    )
    execution_result = ml_runtime.execute(
        inference_response,
        executor_id="integration-engine",
    )

    assert inference_response.status == InferenceStatus.COMPLETED
    assert execution_result.status == ExecutionStatus.COMPLETED
    assert len(bridge.registry.list()) == 1


@pytest.mark.integration
def test_plugin_bridge_registers_executor_without_ml_code() -> None:
    ml_runtime = build_ml_runtime()
    bridge = build_plugin_bridge(ml_runtime)
    bridge.register_provider(StubMLEnginePlugin(plugin_id="register-only"))
    registered = bridge.discover_and_load()
    assert registered == ("register-only",)
    bridge.health_check("register-only")
    assert ml_runtime.registry.metadata("register-only") is not None
