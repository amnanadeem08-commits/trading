"""Unit tests for training scheduler."""

from __future__ import annotations

import pytest

from tests.training_pipeline_helpers import make_training_request, make_training_runtime
from training_pipeline import TrainingJobStatus


@pytest.mark.unit
def test_scheduler_submits_and_runs_job() -> None:
    runtime = make_training_runtime()
    request = make_training_request()
    request = request.model_copy(
        update={"dataset": runtime.dataset_selector.resolve_reference(dataset_id="dataset-1")}
    )
    job = runtime.scheduler.submit(request)
    assert job.status == TrainingJobStatus.QUEUED

    result = runtime.scheduler.run_next()
    assert result is not None
    assert result.status == TrainingJobStatus.COMPLETED
    assert result.artifact_id is not None


@pytest.mark.unit
def test_scheduler_run_all_drains_queue() -> None:
    runtime = make_training_runtime()
    dataset = runtime.dataset_selector.resolve_reference(dataset_id="dataset-1")
    for index in range(2):
        request = make_training_request(experiment_id=f"experiment-{index}").model_copy(
            update={"dataset": dataset}
        )
        runtime.scheduler.submit(request)
    results = runtime.scheduler.run_all()
    assert len(results) == 2
