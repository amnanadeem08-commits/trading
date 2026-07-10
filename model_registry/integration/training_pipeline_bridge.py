"""Training pipeline bridge for model registry integration."""

from __future__ import annotations

from uuid import uuid4

from config.hash import compute_configuration_hash
from events.event_bus import EventBus
from metrics.registry import MetricRegistry
from model_registry.experiments.experiment_metrics import ExperimentMetrics
from model_registry.experiments.experiment_run import ExperimentRun
from model_registry.experiments.experiment_snapshot import ExperimentSnapshot
from model_registry.lifecycle.registry_lifecycle import RegistryLifecycleManager
from model_registry.lineage.lineage_graph import LineageGraph
from model_registry.models.model_stage import ModelStage
from model_registry.models.model_version import ModelVersion
from model_registry.models.registered_model import RegisteredModel
from model_registry.registry.model_registry import ModelRegistryStore
from model_registry.versioning.registry_version import RegistryVersionRegistry
from training_pipeline import (
    TrainingJobStatus,
    TrainingPipelineRuntime,
    schedule_training_from_dataset,
)
from training_pipeline.artifacts.model_artifact import ModelArtifact
from training_pipeline.jobs.training_result import TrainingResult


class ModelRegistryRuntime:
    """Wires model registry components with training pipeline integration."""

    def __init__(
        self,
        *,
        training_runtime: TrainingPipelineRuntime,
        registry: ModelRegistryStore | None = None,
        event_bus: EventBus | None = None,
        metrics: MetricRegistry | None = None,
        approval_required: bool = True,
    ) -> None:
        self.training_runtime = training_runtime
        self.registry = registry or ModelRegistryStore(approval_required=approval_required)
        self.lineage = LineageGraph()
        self.version_registry = RegistryVersionRegistry()
        self._event_bus = event_bus or EventBus()
        self._metric_registry = metrics or MetricRegistry()
        self.lifecycle = RegistryLifecycleManager(
            event_bus=self._event_bus,
            metrics=self._metric_registry,
        )
        self.version_registry.register(
            version_id="registry-v1",
            registry_schema="1.0.0",
            configuration_hash=compute_configuration_hash(),
        )

    def register_model(self, *, model_id: str, name: str, description: str = "") -> RegisteredModel:
        model = RegisteredModel.create(
            model_id=model_id,
            name=name,
            description=description,
        )
        registered = self.registry.register_model(model)
        correlation_id = str(uuid4())
        self.lifecycle.emit_model_registered(
            model_id=model_id,
            correlation_id=correlation_id,
            trace_id=str(uuid4()),
        )
        return registered

    def ingest_training_result(
        self,
        *,
        model_id: str,
        training_result: TrainingResult,
        experiment_id: str,
        semantic_version: str = "1.0.0",
    ) -> ModelVersion:

        if training_result.status != TrainingJobStatus.COMPLETED:
            msg = "only completed training results can be ingested"
            from model_registry.exceptions import ModelRegistryError

            raise ModelRegistryError(msg)

        artifact = self.training_runtime.artifact_store.get(training_result.artifact_id or "")
        run = self.training_runtime.experiment_registry.get_run(training_result.run_id)
        version = self.registry.build_version(
            model_id=model_id,
            semantic_version=semantic_version,
            artifact_id=artifact.artifact_id,
            dataset_id=run.dataset.dataset_id,
            dataset_snapshot_id=run.dataset.snapshot_id,
            experiment_id=experiment_id,
            run_id=training_result.run_id,
            job_id=training_result.job_id,
            config_hash=artifact.manifest.reproducibility_key,
            checksum=artifact.metadata.checksum,
        )
        registered_version = self.registry.register_version(version)
        correlation_id = str(uuid4())
        self.lifecycle.emit_version_registered(
            model_id=model_id,
            version_id=registered_version.version_id,
            correlation_id=correlation_id,
            trace_id=str(uuid4()),
        )
        self.lineage.record_training_lineage(
            dataset_id=run.dataset.dataset_id,
            job_id=training_result.job_id,
            experiment_id=experiment_id,
            artifact_id=artifact.artifact_id,
            model_id=model_id,
            version_id=registered_version.version_id,
        )
        self.lifecycle.emit_lineage_updated(
            model_id=model_id,
            version_id=registered_version.version_id,
            correlation_id=correlation_id,
            trace_id=str(uuid4()),
        )
        return registered_version

    def capture_experiment_snapshot(self, run: ExperimentRun) -> ExperimentSnapshot:
        return ExperimentSnapshot(
            snapshot_id=f"snapshot-{uuid4()}",
            run_id=run.run_id,
            experiment_id=run.experiment_id,
            artifact_id=run.artifact_id,
            dataset_id=run.dataset_id,
            parameters=run.parameters,
            metrics=run.metrics,
            config_hash=run.config_hash,
            checksum=run.checksum,
            captured_at=run.completed_at,
        )

    def experiment_run_from_artifact(self, artifact: ModelArtifact) -> ExperimentRun:
        from models.common import utc_now

        return ExperimentRun(
            run_id=artifact.metadata.run_id,
            experiment_id=artifact.metadata.experiment_id,
            job_id=artifact.metadata.job_id,
            artifact_id=artifact.artifact_id,
            dataset_id=artifact.metadata.dataset.dataset_id,
            dataset_snapshot_id=artifact.metadata.dataset.snapshot_id,
            parameters=artifact.manifest.hyperparameters,
            metrics=ExperimentMetrics(
                run_id=artifact.metadata.run_id,
                experiment_id=artifact.metadata.experiment_id,
                values={},
            ),
            config_hash=artifact.manifest.reproducibility_key,
            checksum=artifact.metadata.checksum,
            started_at=artifact.metadata.created_at,
            completed_at=utc_now(),
        )

    def promote_version(
        self,
        *,
        version_id: str,
        to_stage: ModelStage,
        approved: bool = True,
    ) -> ModelVersion:

        version = self.registry.get_version(version_id)
        if self.registry.validator.policy.approval_required and to_stage in {
            ModelStage.APPROVED,
            ModelStage.PRODUCTION,
        }:
            request = self.registry.promotion_registry.create_approval_request(
                model_id=version.model_id,
                version_id=version_id,
                from_stage=version.stage,
                to_stage=to_stage,
            )
            self.lifecycle.emit_promotion_requested(
                model_id=version.model_id,
                version_id=version_id,
                to_stage=to_stage.value,
                correlation_id=str(uuid4()),
                trace_id=str(uuid4()),
            )
            result = self.registry.promotion_registry.resolve_approval(
                request,
                approved=approved,
                message="registry promotion",
            )
            if not result.approved:
                self.lifecycle.emit_promotion_rejected(
                    model_id=version.model_id,
                    version_id=version_id,
                    message=result.message,
                    correlation_id=str(uuid4()),
                    trace_id=str(uuid4()),
                )
                from model_registry.exceptions import PromotionError

                raise PromotionError("promotion rejected")
            self.lifecycle.emit_promotion_approved(
                model_id=version.model_id,
                version_id=version_id,
                to_stage=to_stage.value,
                correlation_id=str(uuid4()),
                trace_id=str(uuid4()),
            )
        return self.registry.promote(version_id=version_id, to_stage=to_stage, approved=approved)


def build_model_registry_runtime(
    training_runtime: TrainingPipelineRuntime,
    *,
    approval_required: bool = True,
) -> ModelRegistryRuntime:
    """Create a model registry runtime bound to a training pipeline."""
    return ModelRegistryRuntime(
        training_runtime=training_runtime,
        approval_required=approval_required,
    )


def register_model_from_training(
    runtime: ModelRegistryRuntime,
    *,
    model_id: str,
    model_name: str,
    experiment_id: str,
    dataset_id: str,
    model_family: str = "baseline",
) -> ModelRegistryStore:
    """Execute training and register the resulting model version."""
    runtime.register_model(model_id=model_id, name=model_name)
    result = schedule_training_from_dataset(
        runtime.training_runtime,
        experiment_id=experiment_id,
        model_family=model_family,
        dataset_id=dataset_id,
    )
    runtime.ingest_training_result(
        model_id=model_id,
        training_result=result,
        experiment_id=experiment_id,
    )
    return runtime.registry
