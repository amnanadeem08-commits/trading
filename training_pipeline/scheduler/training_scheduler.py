"""Training job scheduler."""

from __future__ import annotations

from uuid import uuid4

from training_pipeline.experiments.experiment import Experiment
from training_pipeline.experiments.experiment_registry import ExperimentRegistry
from training_pipeline.jobs.training_job import TrainingJob
from training_pipeline.jobs.training_job_spec import TrainingJobSpec
from training_pipeline.jobs.training_request import TrainingRequest
from training_pipeline.jobs.training_result import TrainingResult
from training_pipeline.lifecycle.training_lifecycle import TrainingLifecycleManager
from training_pipeline.metrics.training_metrics import TrainingMetricsCollector
from training_pipeline.registry.training_registry import TrainingRegistry
from training_pipeline.scheduler.training_dispatcher import TrainingDispatcher
from training_pipeline.scheduler.training_queue import TrainingQueue
from training_pipeline.validation.validator import TrainingValidator


class TrainingScheduler:
    """Schedules and executes training jobs through the queue and dispatcher."""

    def __init__(
        self,
        *,
        queue: TrainingQueue,
        dispatcher: TrainingDispatcher,
        experiment_registry: ExperimentRegistry,
        training_registry: TrainingRegistry,
        lifecycle: TrainingLifecycleManager,
        metrics: TrainingMetricsCollector,
        validator: TrainingValidator | None = None,
    ) -> None:
        self._queue = queue
        self._dispatcher = dispatcher
        self._experiments = experiment_registry
        self._registry = training_registry
        self._lifecycle = lifecycle
        self._metrics = metrics
        self._validator = validator or TrainingValidator()

    def register_experiment(self, experiment: Experiment) -> Experiment:
        self._experiments.register(experiment)
        return experiment

    def submit(self, request: TrainingRequest) -> TrainingJob:
        validation = self._validator.validate_request(request)
        if not validation.valid:
            msg = validation.errors[0] if validation.errors else "invalid request"
            from training_pipeline.exceptions import TrainingValidationError

            raise TrainingValidationError(msg)

        if not self._experiments.exists(request.experiment_id):
            experiment = Experiment.create(
                experiment_id=request.experiment_id,
                name=request.experiment_id,
                model_family=request.model_family,
                default_hyperparameters=request.hyperparameters,
                tags=request.tags,
            )
            self._experiments.register(experiment)

        job_id = request.request_id or f"job-{uuid4()}"
        spec = TrainingJobSpec(
            job_id=job_id,
            experiment_id=request.experiment_id,
            model_family=request.model_family,
            training_version=request.training_version,
            dataset=request.dataset,
            hyperparameters=request.hyperparameters,
            tags=request.tags,
            correlation_id=request.correlation_id or str(uuid4()),
            trace_id=request.trace_id or str(uuid4()),
        )
        job = TrainingJob.from_spec(spec)
        self._registry.register_job(job)
        queued = self._queue.enqueue(job)
        self._lifecycle.emit_queued(
            job_id=queued.job_id,
            experiment_id=queued.spec.experiment_id,
            correlation_id=queued.spec.correlation_id,
            trace_id=queued.spec.trace_id,
        )
        self._metrics.record_status(queued.status)
        return queued

    def run_next(self) -> TrainingResult | None:
        job = self._queue.dequeue()
        if job is None:
            return None
        result = self._dispatcher.dispatch(job)
        self._queue.update(
            job.model_copy(
                update={
                    "status": result.status,
                    "run_id": result.run_id or None,
                    "artifact_id": result.artifact_id,
                    "checkpoint_id": result.checkpoint_id,
                    "completed_at": result.completed_at,
                }
            )
        )
        return result

    def run_all(self) -> tuple[TrainingResult, ...]:
        results: list[TrainingResult] = []
        while True:
            result = self.run_next()
            if result is None:
                break
            results.append(result)
        return tuple(results)

    def pending_count(self) -> int:
        return self._queue.size()
