"""Unit tests for training pipeline runtime."""

from __future__ import annotations

import pytest

from tests.training_pipeline_helpers import make_training_runtime
from training_pipeline import TrainingJobStatus, schedule_training_from_dataset


@pytest.mark.unit
def test_training_runtime_schedule_and_execute() -> None:
    runtime = make_training_runtime()
    result = schedule_training_from_dataset(
        runtime,
        experiment_id="exp-runtime",
        model_family="baseline",
        dataset_id="dataset-1",
        hyperparameters={"epochs": 1},
    )
    assert result.status == TrainingJobStatus.COMPLETED
    assert runtime.artifact_store.exists(result.artifact_id or "")
    assert runtime.training_registry.get(result.job_id).status == TrainingJobStatus.COMPLETED


@pytest.mark.unit
def test_training_runtime_submit_training_request() -> None:
    runtime = make_training_runtime()
    request = runtime.submit_training(
        experiment_id="exp-1",
        model_family="baseline",
        dataset_id="dataset-1",
    )
    job = runtime.schedule(request)
    assert job.spec.dataset.dataset_id == "dataset-1"


@pytest.mark.unit
def test_training_runtime_lifecycle_events() -> None:
    runtime = make_training_runtime()
    schedule_training_from_dataset(
        runtime,
        experiment_id="exp-events",
        model_family="baseline",
        dataset_id="dataset-1",
    )
    event_types = {event.event_type for event in runtime.lifecycle.events}
    assert len(event_types) >= 3
