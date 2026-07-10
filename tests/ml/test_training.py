"""Unit tests for ML training framework."""

from __future__ import annotations

import pytest

from ml import (
    TERMINAL_TRAINING_STATES,
    InMemoryTrainer,
    TrainingJobState,
    TrainingStateError,
)
from tests.ml_helpers import FailingMLModel, SampleMLModel


@pytest.mark.unit
def test_trainer_create_and_run_job() -> None:
    trainer = InMemoryTrainer()
    job = trainer.create_job(
        model_id="sample-model", dataset_id="records", parameters={"epochs": 3}
    )
    assert job.state == TrainingJobState.CREATED
    result = trainer.run(job, SampleMLModel())
    assert result.state == TrainingJobState.COMPLETED
    assert result.metrics["loss"] == 0.1
    stored = trainer.get_job(job.job_id)
    assert stored is not None
    assert stored.state == TrainingJobState.COMPLETED


@pytest.mark.unit
def test_trainer_start_invalid_state_raises() -> None:
    trainer = InMemoryTrainer()
    job = trainer.create_job(model_id="sample-model", dataset_id="records")
    running = trainer.start(job)
    with pytest.raises(TrainingStateError):
        trainer.start(running)


@pytest.mark.unit
def test_trainer_failed_job() -> None:
    trainer = InMemoryTrainer()
    job = trainer.create_job(model_id="failing-model", dataset_id="records")
    result = trainer.run(job, FailingMLModel())
    assert result.state == TrainingJobState.FAILED
    assert result.errors


@pytest.mark.unit
def test_terminal_training_states() -> None:
    assert TrainingJobState.COMPLETED in TERMINAL_TRAINING_STATES
    assert TrainingJobState.CREATED not in TERMINAL_TRAINING_STATES
