"""Helpers for training pipeline tests."""

from __future__ import annotations

from uuid import uuid4

from feature_store import FeatureStore, ingest_feature_set
from tests.feature_store_helpers import seed_feature_set_from_pipeline
from training_pipeline import (
    DatasetReference,
    TrainingJobSpec,
    TrainingPipelineRuntime,
    TrainingRequest,
    build_training_runtime,
)


def make_dataset_reference(
    *,
    dataset_id: str = "dataset-1",
    version: str = "1.0.0",
    record_count: int = 3,
    checksum: str = "abc123",
) -> DatasetReference:
    return DatasetReference(
        dataset_id=dataset_id,
        version=version,
        record_count=record_count,
        checksum=checksum,
    )


def make_training_request(
    *,
    experiment_id: str = "experiment-1",
    model_family: str = "baseline",
    dataset: DatasetReference | None = None,
) -> TrainingRequest:
    return TrainingRequest(
        request_id=f"request-{uuid4()}",
        experiment_id=experiment_id,
        model_family=model_family,
        dataset=dataset or make_dataset_reference(),
        hyperparameters={"epochs": 1},
        correlation_id=str(uuid4()),
        trace_id=str(uuid4()),
    )


def make_training_job_spec(
    *,
    job_id: str = "job-1",
    experiment_id: str = "experiment-1",
) -> TrainingJobSpec:
    return TrainingJobSpec(
        job_id=job_id,
        experiment_id=experiment_id,
        model_family="baseline",
        training_version="1.0.0",
        dataset=make_dataset_reference(),
        hyperparameters={"epochs": 1},
        correlation_id=str(uuid4()),
        trace_id=str(uuid4()),
    )


def seed_feature_store_with_dataset(*, record_count: int = 3) -> FeatureStore:
    feature_set, _ = seed_feature_set_from_pipeline(record_count=record_count)
    store = FeatureStore()
    ingest_feature_set(store, feature_set)
    return store


def make_training_runtime(*, record_count: int = 3) -> TrainingPipelineRuntime:
    store = seed_feature_store_with_dataset(record_count=record_count)
    return build_training_runtime(store)
