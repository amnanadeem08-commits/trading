"""Integration tests for inference pipeline runtime."""

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
from model_registry import build_model_registry_runtime, register_model_from_training
from tests.feature_engineering_helpers import seed_historical_and_stream
from training_pipeline import build_training_runtime


@pytest.mark.integration
def test_full_pipeline_to_inference_flow() -> None:
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

    inference_runtime = build_inference_runtime(registry_runtime)
    response = run_inference_for_model(
        inference_runtime,
        model_id="integration-model",
        input_metadata={"feature_set_id": dataset.dataset_id},
    )

    assert response.status == InferenceStatus.COMPLETED
    assert response.metadata.version_id
    assert response.metadata.stage == "production"
    assert len(inference_runtime.inference_registry.history("integration-model")) == 1


@pytest.mark.integration
def test_inference_batch_through_scheduler() -> None:
    _, stream = seed_historical_and_stream(record_count=2)
    extraction = run_extraction_from_stream(stream, max_batches=1)
    assert extraction.feature_set is not None

    store = FeatureStore()
    ingest_feature_set(store, extraction.feature_set)
    training_runtime = build_training_runtime(store)
    registry_runtime = build_model_registry_runtime(training_runtime, approval_required=False)
    register_model_from_training(
        registry_runtime,
        model_id="batch-model",
        model_name="Batch Model",
        experiment_id="batch-exp",
        dataset_id="dataset-1",
    )
    prepare_production_model(registry_runtime, model_id="batch-model")
    inference_runtime = build_inference_runtime(registry_runtime)

    from inference_pipeline import InferenceBatchRequest

    batch = InferenceBatchRequest(
        batch_id="batch-1",
        model_id="batch-model",
        input_metadata_batch=({"id": "1"}, {"id": "2"}),
    )
    inference_runtime.scheduler.submit_batch(batch)
    responses = inference_runtime.scheduler.run_all()
    assert len(responses) == 2
    assert all(response.status == InferenceStatus.COMPLETED for response in responses)
