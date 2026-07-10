"""Unit tests for checkpoint registry."""

from __future__ import annotations

import pytest

from training_pipeline import CheckpointNotFoundError, CheckpointRegistry, TrainingJobStatus


@pytest.mark.unit
def test_checkpoint_registry_create_and_list() -> None:
    registry = CheckpointRegistry()
    checkpoint = registry.create(
        job_id="job-1",
        experiment_id="exp-1",
        run_id="run-1",
        status=TrainingJobStatus.RUNNING,
    )
    checkpoints = registry.list_for_job("job-1")
    assert len(checkpoints) == 1
    assert checkpoints[0].checkpoint_id == checkpoint.checkpoint_id


@pytest.mark.unit
def test_checkpoint_registry_latest() -> None:
    registry = CheckpointRegistry()
    registry.create(
        job_id="job-1",
        experiment_id="exp-1",
        run_id="run-1",
        status=TrainingJobStatus.RUNNING,
        step=1,
    )
    latest = registry.create(
        job_id="job-1",
        experiment_id="exp-1",
        run_id="run-1",
        status=TrainingJobStatus.RUNNING,
        step=2,
    )
    assert registry.latest_for_job("job-1").checkpoint_id == latest.checkpoint_id


@pytest.mark.unit
def test_checkpoint_registry_missing_raises() -> None:
    registry = CheckpointRegistry()
    with pytest.raises(CheckpointNotFoundError):
        registry.get("missing")
