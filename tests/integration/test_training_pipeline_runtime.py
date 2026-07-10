"""Integration tests for training pipeline runtime."""

from __future__ import annotations

import pytest

from feature_engineering import run_extraction_from_stream
from feature_store import FeatureStore, ingest_feature_set
from tests.feature_engineering_helpers import seed_historical_and_stream
from training_pipeline import (
    TrainingJobStatus,
    build_training_runtime,
    schedule_training_from_dataset,
)


@pytest.mark.integration
def test_feature_store_to_training_pipeline_flow() -> None:
    _, stream = seed_historical_and_stream(record_count=3)
    extraction = run_extraction_from_stream(stream, max_batches=1)
    assert extraction.feature_set is not None

    store = FeatureStore()
    dataset = ingest_feature_set(store, extraction.feature_set)
    runtime = build_training_runtime(store)

    result = schedule_training_from_dataset(
        runtime,
        experiment_id="integration-exp",
        model_family="baseline",
        dataset_id=dataset.dataset_id,
        hyperparameters={"epochs": 1},
    )

    assert result.status == TrainingJobStatus.COMPLETED
    artifact = runtime.artifact_store.get(result.artifact_id or "")
    assert artifact.metadata.dataset.dataset_id == dataset.dataset_id
    assert artifact.metadata.dataset.record_count == 3


@pytest.mark.integration
def test_training_pipeline_experiment_and_version_lineage() -> None:
    _, stream = seed_historical_and_stream(record_count=2)
    extraction = run_extraction_from_stream(stream, max_batches=1)
    assert extraction.feature_set is not None

    store = FeatureStore()
    ingest_feature_set(store, extraction.feature_set)
    runtime = build_training_runtime(store)
    schedule_training_from_dataset(
        runtime,
        experiment_id="lineage-exp",
        model_family="baseline",
        dataset_id="dataset-1",
    )

    runs = runtime.experiment_registry.list_runs("lineage-exp")
    assert len(runs) == 1
    version = runtime.version_registry.latest_for_job(runs[0].job_id)
    assert version is not None
    assert version.semantic_version == "1.0.0"
