"""Unit tests for training jobs."""

from __future__ import annotations

import pytest

from tests.training_pipeline_helpers import make_training_job_spec
from training_pipeline import TrainingJob, TrainingJobStatus


@pytest.mark.unit
def test_training_job_from_spec() -> None:
    spec = make_training_job_spec()
    job = TrainingJob.from_spec(spec)
    assert job.job_id == "job-1"
    assert job.status == TrainingJobStatus.PENDING


@pytest.mark.unit
def test_training_job_with_status_terminal() -> None:
    spec = make_training_job_spec()
    job = TrainingJob.from_spec(spec)
    completed = job.with_status(TrainingJobStatus.COMPLETED)
    assert completed.status == TrainingJobStatus.COMPLETED
    assert completed.completed_at is not None
