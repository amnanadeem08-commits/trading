"""Training pipeline validator."""

from __future__ import annotations

from training_pipeline.experiments.experiment_registry import ExperimentRegistry
from training_pipeline.jobs.training_job import TrainingJob
from training_pipeline.jobs.training_job_spec import TrainingJobSpec
from training_pipeline.jobs.training_request import TrainingRequest
from training_pipeline.validation.validation_result import TrainingValidationResult


class TrainingValidator:
    """Validates training submissions and job specifications."""

    def validate_request(self, request: TrainingRequest) -> TrainingValidationResult:
        errors: list[str] = []
        if not request.request_id.strip():
            errors.append("request_id must not be empty")
        if not request.experiment_id.strip():
            errors.append("experiment_id must not be empty")
        if not request.model_family.strip():
            errors.append("model_family must not be empty")
        if not request.dataset.dataset_id.strip():
            errors.append("dataset_id must not be empty")
        if errors:
            return TrainingValidationResult.failure(*errors, job_id=request.request_id)
        return TrainingValidationResult.success(job_id=request.request_id)

    def validate_spec(self, spec: TrainingJobSpec) -> TrainingValidationResult:
        errors: list[str] = []
        if not spec.job_id.strip():
            errors.append("job_id must not be empty")
        if not spec.experiment_id.strip():
            errors.append("experiment_id must not be empty")
        if not spec.model_family.strip():
            errors.append("model_family must not be empty")
        if not spec.dataset.dataset_id.strip():
            errors.append("dataset_id must not be empty")
        if errors:
            return TrainingValidationResult.failure(*errors, job_id=spec.job_id)
        return TrainingValidationResult.success(
            job_id=spec.job_id,
            experiment_id=spec.experiment_id,
        )

    def validate_job(self, job: TrainingJob) -> TrainingValidationResult:
        return self.validate_spec(job.spec)

    def validate_experiment_exists(
        self,
        experiment_id: str,
        registry: ExperimentRegistry,
    ) -> TrainingValidationResult:
        if not registry.exists(experiment_id):
            return TrainingValidationResult.failure(
                f"Experiment not registered: {experiment_id}",
                job_id=None,
            )
        return TrainingValidationResult.success(experiment_id=experiment_id)
