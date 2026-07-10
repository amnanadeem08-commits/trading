"""Experiment registry."""

from __future__ import annotations

from threading import RLock

from training_pipeline.exceptions import ExperimentNotFoundError, TrainingJobError
from training_pipeline.experiments.experiment import Experiment, ExperimentRun


class ExperimentRegistry:
    """Thread-safe registry for experiments and runs."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._experiments: dict[str, Experiment] = {}
        self._runs: dict[str, ExperimentRun] = {}
        self._runs_by_experiment: dict[str, tuple[str, ...]] = {}

    def register(self, experiment: Experiment) -> None:
        experiment_id = experiment.experiment_id
        if not experiment_id.strip():
            msg = "Experiment id must not be empty"
            raise TrainingJobError(msg)
        with self._lock:
            self._experiments[experiment_id] = experiment
            self._runs_by_experiment.setdefault(experiment_id, ())

    def lookup(self, experiment_id: str) -> Experiment:
        with self._lock:
            experiment = self._experiments.get(experiment_id)
        if experiment is None:
            raise ExperimentNotFoundError(experiment_id)
        return experiment

    def exists(self, experiment_id: str) -> bool:
        with self._lock:
            return experiment_id in self._experiments

    def list_experiments(self) -> tuple[Experiment, ...]:
        with self._lock:
            return tuple(
                self._experiments[experiment_id] for experiment_id in sorted(self._experiments)
            )

    def record_run(self, run: ExperimentRun) -> None:
        with self._lock:
            if run.experiment_id not in self._experiments:
                raise ExperimentNotFoundError(run.experiment_id)
            self._runs[run.run_id] = run
            runs = self._runs_by_experiment.get(run.experiment_id, ())
            if run.run_id not in runs:
                self._runs_by_experiment[run.experiment_id] = (*runs, run.run_id)

    def get_run(self, run_id: str) -> ExperimentRun:
        with self._lock:
            run = self._runs.get(run_id)
        if run is None:
            msg = f"Experiment run not found: {run_id}"
            raise TrainingJobError(msg)
        return run

    def list_runs(self, experiment_id: str) -> tuple[ExperimentRun, ...]:
        with self._lock:
            run_ids = self._runs_by_experiment.get(experiment_id, ())
            if not run_ids and experiment_id not in self._experiments:
                raise ExperimentNotFoundError(experiment_id)
            return tuple(self._runs[run_id] for run_id in run_ids if run_id in self._runs)
