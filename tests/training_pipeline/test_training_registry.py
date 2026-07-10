"""Unit tests for training registry."""

from __future__ import annotations

import pytest

from tests.training_pipeline_helpers import make_training_job_spec
from training_pipeline import (
    TrainingJob,
    TrainingJobNotFoundError,
    TrainingJobStatus,
    TrainingRegistry,
)


@pytest.mark.unit
def test_training_registry_register_and_update() -> None:
    registry = TrainingRegistry()
    job = TrainingJob.from_spec(make_training_job_spec())
    entry = registry.register_job(job)
    assert entry.status == TrainingJobStatus.PENDING

    updated_job = job.with_status(TrainingJobStatus.COMPLETED)
    updated_entry = registry.update_job(updated_job)
    assert updated_entry.status == TrainingJobStatus.COMPLETED


@pytest.mark.unit
def test_training_registry_list_by_status() -> None:
    registry = TrainingRegistry()
    job = TrainingJob.from_spec(make_training_job_spec(job_id="job-1"))
    registry.register_job(job)
    pending = registry.list_by_status(TrainingJobStatus.PENDING)
    assert len(pending) == 1


@pytest.mark.unit
def test_training_registry_missing_raises() -> None:
    registry = TrainingRegistry()
    with pytest.raises(TrainingJobNotFoundError):
        registry.get("missing")
