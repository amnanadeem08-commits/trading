"""Unit tests for experiment registry."""

from __future__ import annotations

import pytest

from models.common import utc_now
from tests.training_pipeline_helpers import make_dataset_reference
from training_pipeline import (
    Experiment,
    ExperimentNotFoundError,
    ExperimentRegistry,
    ExperimentRun,
    TrainingJobStatus,
)


@pytest.mark.unit
def test_experiment_registry_register_and_lookup() -> None:
    registry = ExperimentRegistry()
    experiment = Experiment.create(
        experiment_id="exp-1",
        name="Baseline",
        model_family="baseline",
    )
    registry.register(experiment)
    assert registry.lookup("exp-1").experiment_id == "exp-1"


@pytest.mark.unit
def test_experiment_registry_record_run() -> None:
    registry = ExperimentRegistry()
    experiment = Experiment.create(
        experiment_id="exp-1",
        name="Baseline",
        model_family="baseline",
    )
    registry.register(experiment)
    run = ExperimentRun(
        run_id="run-1",
        experiment_id="exp-1",
        job_id="job-1",
        status=TrainingJobStatus.COMPLETED,
        dataset=make_dataset_reference(),
        hyperparameters={"epochs": 1},
        started_at=utc_now(),
    )
    registry.record_run(run)
    assert registry.get_run("run-1").job_id == "job-1"


@pytest.mark.unit
def test_experiment_registry_missing_raises() -> None:
    registry = ExperimentRegistry()
    with pytest.raises(ExperimentNotFoundError):
        registry.lookup("missing")
