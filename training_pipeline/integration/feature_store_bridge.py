"""Feature store bridge for training pipeline integration."""

from __future__ import annotations

from uuid import uuid4

from events.event_bus import EventBus
from feature_store.storage.feature_store import FeatureStore
from metrics.registry import MetricRegistry
from training_pipeline.artifacts.artifact_store import ArtifactStore
from training_pipeline.checkpoints.checkpoint_registry import CheckpointRegistry
from training_pipeline.datasets.dataset_selector import DatasetSelector
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
from training_pipeline.scheduler.training_scheduler import TrainingScheduler
from training_pipeline.validation.validator import TrainingValidator
from training_pipeline.versioning.training_version import TrainingVersionRegistry


class TrainingPipelineRuntime:
    """Wires training pipeline components for orchestration-only execution."""

    def __init__(
        self,
        *,
        feature_store: FeatureStore,
        event_bus: EventBus | None = None,
        metrics: MetricRegistry | None = None,
    ) -> None:
        self.feature_store = feature_store
        self.dataset_selector = DatasetSelector(feature_store)
        self.experiment_registry = ExperimentRegistry()
        self.artifact_store = ArtifactStore()
        self.checkpoint_registry = CheckpointRegistry()
        self.training_registry = TrainingRegistry()
        self.version_registry = TrainingVersionRegistry()
        self.metrics_collector = TrainingMetricsCollector()
        self.validator = TrainingValidator()
        self._event_bus = event_bus or EventBus()
        self._metric_registry = metrics or MetricRegistry()
        self.lifecycle = TrainingLifecycleManager(
            event_bus=self._event_bus,
            metrics=self._metric_registry,
        )
        self.queue = TrainingQueue()
        self.dispatcher = TrainingDispatcher(
            experiment_registry=self.experiment_registry,
            artifact_store=self.artifact_store,
            checkpoint_registry=self.checkpoint_registry,
            training_registry=self.training_registry,
            version_registry=self.version_registry,
            lifecycle=self.lifecycle,
            metrics=self.metrics_collector,
            validator=self.validator,
        )
        self.scheduler = TrainingScheduler(
            queue=self.queue,
            dispatcher=self.dispatcher,
            experiment_registry=self.experiment_registry,
            training_registry=self.training_registry,
            lifecycle=self.lifecycle,
            metrics=self.metrics_collector,
            validator=self.validator,
        )

    def register_experiment(self, experiment: Experiment) -> Experiment:
        return self.scheduler.register_experiment(experiment)

    def submit_training(
        self,
        *,
        experiment_id: str,
        model_family: str,
        dataset_id: str,
        hyperparameters: dict[str, object] | None = None,
        training_version: str = "1.0.0",
        snapshot_id: str | None = None,
    ) -> TrainingRequest:
        dataset = self.dataset_selector.resolve_reference(
            dataset_id=dataset_id,
            snapshot_id=snapshot_id,
        )
        return TrainingRequest(
            request_id=f"request-{uuid4()}",
            experiment_id=experiment_id,
            model_family=model_family,
            dataset=dataset,
            hyperparameters=hyperparameters or {},
            training_version=training_version,
            correlation_id=str(uuid4()),
            trace_id=str(uuid4()),
        )

    def schedule(self, request: TrainingRequest) -> TrainingJob:
        return self.scheduler.submit(request)

    def run_pending(self) -> tuple[TrainingResult, ...]:
        return self.scheduler.run_all()

    def build_job_spec(
        self,
        request: TrainingRequest,
        *,
        job_id: str | None = None,
    ) -> TrainingJobSpec:
        return TrainingJobSpec(
            job_id=job_id or request.request_id,
            experiment_id=request.experiment_id,
            model_family=request.model_family,
            training_version=request.training_version,
            dataset=request.dataset,
            hyperparameters=request.hyperparameters,
            tags=request.tags,
            correlation_id=request.correlation_id,
            trace_id=request.trace_id,
        )


def build_training_runtime(feature_store: FeatureStore) -> TrainingPipelineRuntime:
    """Create a training pipeline runtime bound to a feature store."""
    return TrainingPipelineRuntime(feature_store=feature_store)


def schedule_training_from_dataset(
    runtime: TrainingPipelineRuntime,
    *,
    experiment_id: str,
    model_family: str,
    dataset_id: str,
    hyperparameters: dict[str, object] | None = None,
) -> TrainingResult:
    """Schedule and execute a training job for a feature store dataset."""
    request = runtime.submit_training(
        experiment_id=experiment_id,
        model_family=model_family,
        dataset_id=dataset_id,
        hyperparameters=hyperparameters,
    )
    runtime.schedule(request)
    results = runtime.run_pending()
    if not results:
        msg = "Training job was not executed"
        from training_pipeline.exceptions import TrainingJobError

        raise TrainingJobError(msg)
    return results[-1]
