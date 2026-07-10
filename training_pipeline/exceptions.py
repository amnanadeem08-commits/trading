"""Training pipeline exceptions."""

from __future__ import annotations

from models.common import PlatformError


class TrainingPipelineError(PlatformError):
    """Base exception for training pipeline errors."""

    def __init__(self, message: str, *, code: str = "training_pipeline_error") -> None:
        super().__init__(message, code=code)


class TrainingJobNotFoundError(TrainingPipelineError):
    """Raised when a training job cannot be resolved."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Training job not found: {job_id}", code="training_job_not_found")


class TrainingJobError(TrainingPipelineError):
    """Raised when training job operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="training_job_error")


class ExperimentNotFoundError(TrainingPipelineError):
    """Raised when an experiment cannot be resolved."""

    def __init__(self, experiment_id: str) -> None:
        self.experiment_id = experiment_id
        super().__init__(f"Experiment not found: {experiment_id}", code="experiment_not_found")


class ArtifactNotFoundError(TrainingPipelineError):
    """Raised when a model artifact cannot be resolved."""

    def __init__(self, artifact_id: str) -> None:
        self.artifact_id = artifact_id
        super().__init__(f"Model artifact not found: {artifact_id}", code="artifact_not_found")


class CheckpointNotFoundError(TrainingPipelineError):
    """Raised when a training checkpoint cannot be resolved."""

    def __init__(self, checkpoint_id: str) -> None:
        self.checkpoint_id = checkpoint_id
        super().__init__(
            f"Training checkpoint not found: {checkpoint_id}", code="checkpoint_not_found"
        )


class DatasetReferenceError(TrainingPipelineError):
    """Raised when dataset selection or reference resolution fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="dataset_reference_error")


class TrainingValidationError(TrainingPipelineError):
    """Raised when training validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="training_validation_error")
