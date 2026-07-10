"""Training job dispatcher."""

from __future__ import annotations

from uuid import uuid4

from models.common import utc_now
from training_pipeline.artifacts.artifact_store import ArtifactStore
from training_pipeline.checkpoints.checkpoint_registry import CheckpointRegistry
from training_pipeline.experiments.experiment import ExperimentRun
from training_pipeline.experiments.experiment_registry import ExperimentRegistry
from training_pipeline.jobs.training_job import TrainingJob
from training_pipeline.jobs.training_job_status import TrainingJobStatus
from training_pipeline.jobs.training_result import TrainingResult
from training_pipeline.lifecycle.training_lifecycle import TrainingLifecycleManager
from training_pipeline.metrics.training_metrics import TrainingMetricsCollector, TrainingSummary
from training_pipeline.registry.training_registry import TrainingRegistry
from training_pipeline.validation.validator import TrainingValidator
from training_pipeline.versioning.training_version import TrainingVersionRegistry


class TrainingDispatcher:
    """Dispatches training jobs through orchestration-only lifecycle."""

    def __init__(
        self,
        *,
        experiment_registry: ExperimentRegistry,
        artifact_store: ArtifactStore,
        checkpoint_registry: CheckpointRegistry,
        training_registry: TrainingRegistry,
        version_registry: TrainingVersionRegistry,
        lifecycle: TrainingLifecycleManager,
        metrics: TrainingMetricsCollector,
        validator: TrainingValidator | None = None,
    ) -> None:
        self._experiments = experiment_registry
        self._artifacts = artifact_store
        self._checkpoints = checkpoint_registry
        self._registry = training_registry
        self._versions = version_registry
        self._lifecycle = lifecycle
        self._metrics = metrics
        self._validator = validator or TrainingValidator()

    def dispatch(self, job: TrainingJob) -> TrainingResult:
        validation = self._validator.validate_job(job)
        if not validation.valid:
            failed = job.with_status(
                TrainingJobStatus.FAILED,
                message=validation.errors[0] if validation.errors else "validation failed",
            )
            self._registry.update_job(failed)
            self._lifecycle.emit_failed(
                job_id=job.job_id,
                experiment_id=job.spec.experiment_id,
                message=failed.error_message or "validation failed",
                correlation_id=job.spec.correlation_id,
                trace_id=job.spec.trace_id,
            )
            self._metrics.record_status(TrainingJobStatus.FAILED)
            return TrainingResult(
                job_id=job.job_id,
                experiment_id=job.spec.experiment_id,
                run_id="",
                status=TrainingJobStatus.FAILED,
                message=failed.error_message or "validation failed",
                completed_at=utc_now(),
            )

        run_id = str(uuid4())
        running = job.model_copy(
            update={
                "status": TrainingJobStatus.RUNNING,
                "run_id": run_id,
                "started_at": utc_now(),
                "updated_at": utc_now(),
            }
        )
        self._registry.update_job(running)
        self._lifecycle.emit_started(
            job_id=job.job_id,
            experiment_id=job.spec.experiment_id,
            run_id=run_id,
            correlation_id=job.spec.correlation_id,
            trace_id=job.spec.trace_id,
        )
        self._metrics.record_status(TrainingJobStatus.RUNNING)

        checkpoint = self._checkpoints.create(
            job_id=job.job_id,
            experiment_id=job.spec.experiment_id,
            run_id=run_id,
            status=TrainingJobStatus.RUNNING,
            checksum=job.spec.dataset.checksum,
        )
        self._lifecycle.emit_checkpoint_created(
            checkpoint_id=checkpoint.checkpoint_id,
            job_id=job.job_id,
            experiment_id=job.spec.experiment_id,
            correlation_id=job.spec.correlation_id,
            trace_id=job.spec.trace_id,
        )
        self._metrics.record_checkpoint()

        artifact = self._artifacts.store(
            experiment_id=job.spec.experiment_id,
            run_id=run_id,
            job_id=job.job_id,
            model_family=job.spec.model_family,
            training_version=job.spec.training_version,
            dataset=job.spec.dataset,
            hyperparameters=job.spec.hyperparameters,
            lineage=(
                job.spec.experiment_id,
                run_id,
                job.spec.dataset.dataset_id,
                job.spec.dataset.version,
            ),
        )
        self._lifecycle.emit_artifact_stored(
            artifact_id=artifact.artifact_id,
            job_id=job.job_id,
            experiment_id=job.spec.experiment_id,
            correlation_id=job.spec.correlation_id,
            trace_id=job.spec.trace_id,
        )
        self._metrics.record_artifact()

        self._versions.register(
            version_id=f"version-{run_id}",
            job_id=job.job_id,
            experiment_id=job.spec.experiment_id,
            semantic_version=job.spec.training_version,
            configuration_hash=artifact.manifest.reproducibility_key,
        )

        run = ExperimentRun(
            run_id=run_id,
            experiment_id=job.spec.experiment_id,
            job_id=job.job_id,
            status=TrainingJobStatus.COMPLETED,
            dataset=job.spec.dataset,
            hyperparameters=job.spec.hyperparameters,
            artifact_id=artifact.artifact_id,
            checkpoint_id=checkpoint.checkpoint_id,
            started_at=running.started_at or utc_now(),
            completed_at=utc_now(),
        )
        self._experiments.record_run(run)

        completed = running.model_copy(
            update={
                "status": TrainingJobStatus.COMPLETED,
                "artifact_id": artifact.artifact_id,
                "checkpoint_id": checkpoint.checkpoint_id,
                "completed_at": utc_now(),
                "updated_at": utc_now(),
            }
        )
        self._registry.update_job(completed)
        self._lifecycle.emit_completed(
            job_id=job.job_id,
            experiment_id=job.spec.experiment_id,
            run_id=run_id,
            artifact_id=artifact.artifact_id,
            correlation_id=job.spec.correlation_id,
            trace_id=job.spec.trace_id,
        )
        self._metrics.record_status(TrainingJobStatus.COMPLETED)
        self._metrics.record_summary(
            TrainingSummary(
                job_id=job.job_id,
                experiment_id=job.spec.experiment_id,
                status=TrainingJobStatus.COMPLETED,
                artifact_stored=True,
                checkpoint_count=1,
            )
        )

        return TrainingResult(
            job_id=job.job_id,
            experiment_id=job.spec.experiment_id,
            run_id=run_id,
            status=TrainingJobStatus.COMPLETED,
            artifact_id=artifact.artifact_id,
            checkpoint_id=checkpoint.checkpoint_id,
            dataset_snapshot_id=job.spec.dataset.snapshot_id,
            training_version=job.spec.training_version,
            message="orchestration completed",
            completed_at=completed.completed_at,
        )

    def cancel(self, job: TrainingJob) -> TrainingJob:
        cancelled = job.with_status(TrainingJobStatus.CANCELLED)
        self._registry.update_job(cancelled)
        self._lifecycle.emit_cancelled(
            job_id=job.job_id,
            experiment_id=job.spec.experiment_id,
            correlation_id=job.spec.correlation_id,
            trace_id=job.spec.trace_id,
        )
        self._metrics.record_status(TrainingJobStatus.CANCELLED)
        return cancelled
