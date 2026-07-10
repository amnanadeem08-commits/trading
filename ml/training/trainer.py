"""Trainer interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import uuid4

from ml.exceptions import TrainingStateError
from ml.models.model import MLModel
from ml.training.training_job import TERMINAL_TRAINING_STATES, TrainingJob, TrainingJobState
from ml.training.training_result import TrainingResult
from models.common import utc_now


class Trainer(ABC):
    """Coordinates model training operations."""

    @abstractmethod
    def create_job(
        self,
        *,
        model_id: str,
        dataset_id: str,
        parameters: dict[str, object] | None = None,
    ) -> TrainingJob:
        """Create a new training job."""

    @abstractmethod
    def run(self, job: TrainingJob, model: MLModel) -> TrainingResult:
        """Execute a training job against a model implementation."""

    def start(self, job: TrainingJob) -> TrainingJob:
        """Transition a job to running state."""
        if job.state != TrainingJobState.CREATED:
            raise TrainingStateError(job.job_id, job.state.value, "start")
        return job.model_copy(
            update={"state": TrainingJobState.RUNNING, "started_at": utc_now()},
        )

    def complete(self, job: TrainingJob, *, result: TrainingResult) -> TrainingJob:
        """Transition a job to completed state."""
        if job.state != TrainingJobState.RUNNING:
            raise TrainingStateError(job.job_id, job.state.value, "complete")
        return job.model_copy(
            update={
                "state": TrainingJobState.COMPLETED,
                "completed_at": utc_now(),
            },
        )

    def fail(self, job: TrainingJob, *, message: str) -> TrainingJob:
        """Transition a job to failed state."""
        if job.state in TERMINAL_TRAINING_STATES:
            raise TrainingStateError(job.job_id, job.state.value, "fail")
        return job.model_copy(
            update={
                "state": TrainingJobState.FAILED,
                "completed_at": utc_now(),
                "error_message": message,
            },
        )


class InMemoryTrainer(Trainer):
    """In-memory trainer for platform scaffolding."""

    def __init__(self) -> None:
        self._jobs: dict[str, TrainingJob] = {}

    def create_job(
        self,
        *,
        model_id: str,
        dataset_id: str,
        parameters: dict[str, object] | None = None,
    ) -> TrainingJob:
        job = TrainingJob(
            job_id=str(uuid4()),
            model_id=model_id,
            dataset_id=dataset_id,
            parameters=parameters or {},
        )
        self._jobs[job.job_id] = job
        return job

    def run(self, job: TrainingJob, model: MLModel) -> TrainingResult:
        started = self.start(job)
        self._jobs[started.job_id] = started
        try:
            result = model.train(
                dataset_id=started.dataset_id,
                parameters=dict(started.parameters),
            )
            completed = self.complete(started, result=result)
            self._jobs[completed.job_id] = completed
            return result
        except Exception as error:
            failed = self.fail(started, message=str(error))
            self._jobs[failed.job_id] = failed
            return TrainingResult(
                job_id=failed.job_id,
                model_id=failed.model_id,
                dataset_id=failed.dataset_id,
                state=TrainingJobState.FAILED,
                errors=(str(error),),
            )

    def get_job(self, job_id: str) -> TrainingJob | None:
        return self._jobs.get(job_id)
