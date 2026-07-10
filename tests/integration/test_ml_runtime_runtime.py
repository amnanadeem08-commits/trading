"""Integration tests for ML runtime."""

from __future__ import annotations

import pytest

from feature_engineering import run_extraction_from_stream
from feature_store import FeatureStore, ingest_feature_set
from inference_pipeline import InferenceStatus, prepare_production_model
from ml_runtime import ExecutionStatus, build_ml_runtime, run_inference_and_execute
from model_registry import build_model_registry_runtime, register_model_from_training
from tests.feature_engineering_helpers import seed_historical_and_stream
from tests.ml_runtime_helpers import StubModelExecutor
from training_pipeline import build_training_runtime


@pytest.mark.integration
def test_full_pipeline_to_ml_runtime_flow() -> None:
    _, stream = seed_historical_and_stream(record_count=3)
    extraction = run_extraction_from_stream(stream, max_batches=1)
    assert extraction.feature_set is not None

    store = FeatureStore()
    dataset = ingest_feature_set(store, extraction.feature_set)
    training_runtime = build_training_runtime(store)
    registry_runtime = build_model_registry_runtime(training_runtime, approval_required=False)
    register_model_from_training(
        registry_runtime,
        model_id="integration-model",
        model_name="Integration Model",
        experiment_id="integration-exp",
        dataset_id=dataset.dataset_id,
    )
    prepare_production_model(registry_runtime, model_id="integration-model")

    from inference_pipeline import build_inference_runtime

    inference_runtime = build_inference_runtime(registry_runtime)
    ml_runtime = build_ml_runtime()
    ml_runtime.register_executor(
        StubModelExecutor(executor_id="integration-executor"),
        name="Integration Stub",
        version="1.0.0",
    )

    inference_response, execution_result = run_inference_and_execute(
        inference_runtime,
        ml_runtime,
        model_id="integration-model",
        input_metadata={"feature_set_id": dataset.dataset_id},
        executor_id="integration-executor",
    )

    assert inference_response.status == InferenceStatus.COMPLETED
    assert execution_result.status == ExecutionStatus.COMPLETED
    assert execution_result.metadata is not None
    assert execution_result.metadata.artifact_reference


@pytest.mark.integration
def test_ml_runtime_executor_load_unload_lifecycle() -> None:
    executor = StubModelExecutor(executor_id="lifecycle-executor")
    runtime = build_ml_runtime()
    runtime.register_executor(executor, name="Lifecycle Stub", version="1.0.0")

    from inference_pipeline import run_inference_for_model
    from tests.inference_pipeline_helpers import make_inference_runtime

    inference_runtime = make_inference_runtime()
    response = run_inference_for_model(
        inference_runtime,
        model_id="model-1",
        input_metadata={"id": "1"},
    )
    result = runtime.execute(response, executor_id="lifecycle-executor")
    assert result.status == ExecutionStatus.COMPLETED
    assert executor.loaded is True
    assert executor.unloaded is True
