"""ML layer exceptions."""

from __future__ import annotations

from models.common import PlatformError


class MLError(PlatformError):
    """Base exception for ML layer errors."""

    def __init__(self, message: str, *, code: str = "ml_error") -> None:
        super().__init__(message, code=code)


class ModelNotFoundError(MLError):
    """Raised when a requested model is not registered."""

    def __init__(self, model_id: str) -> None:
        super().__init__(f"Model not found: {model_id}", code="model_not_found")
        self.model_id = model_id


class ModelRegistrationError(MLError):
    """Raised when model registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="model_registration_error")


class ModelValidationError(MLError):
    """Raised when model validation fails."""

    def __init__(self, message: str, *, errors: tuple[str, ...] = ()) -> None:
        super().__init__(message, code="model_validation_error")
        self.errors = errors


class TrainingError(MLError):
    """Raised when training operations fail."""

    def __init__(self, message: str, *, job_id: str | None = None) -> None:
        super().__init__(message, code="training_error")
        self.job_id = job_id


class TrainingStateError(MLError):
    """Raised when an invalid training state transition is attempted."""

    def __init__(self, job_id: str, current_state: str, operation: str) -> None:
        super().__init__(
            f"Cannot {operation} training job '{job_id}' in state '{current_state}'",
            code="training_state_error",
        )
        self.job_id = job_id
        self.current_state = current_state
        self.operation = operation


class InferenceError(MLError):
    """Raised when inference operations fail."""

    def __init__(self, message: str, *, model_id: str | None = None) -> None:
        super().__init__(message, code="inference_error")
        self.model_id = model_id


class EvaluationError(MLError):
    """Raised when evaluation operations fail."""

    def __init__(self, message: str, *, evaluation_id: str | None = None) -> None:
        super().__init__(message, code="evaluation_error")
        self.evaluation_id = evaluation_id


class FeaturePipelineError(MLError):
    """Raised when feature pipeline operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="feature_pipeline_error")


class MLRegistryError(MLError):
    """Raised when ML registry operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="ml_registry_error")
