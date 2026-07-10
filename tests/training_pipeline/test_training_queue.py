"""Unit tests for training queue."""

from __future__ import annotations

import pytest

from tests.training_pipeline_helpers import make_training_job_spec
from training_pipeline import (
    TrainingJob,
    TrainingJobNotFoundError,
    TrainingJobStatus,
    TrainingQueue,
)


@pytest.mark.unit
def test_queue_enqueue_dequeue() -> None:
    queue = TrainingQueue()
    job = TrainingJob.from_spec(make_training_job_spec(job_id="job-a"))
    queued = queue.enqueue(job)
    assert queued.status == TrainingJobStatus.QUEUED
    assert queue.size() == 1

    running = queue.dequeue()
    assert running is not None
    assert running.status == TrainingJobStatus.RUNNING
    assert queue.size() == 0


@pytest.mark.unit
def test_queue_get_missing_raises() -> None:
    queue = TrainingQueue()
    with pytest.raises(TrainingJobNotFoundError):
        queue.get("missing")
