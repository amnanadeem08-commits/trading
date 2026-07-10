"""Inference pipeline exceptions."""

from __future__ import annotations

from models.common import PlatformError


class InferencePipelineError(PlatformError):
    """Base exception for inference pipeline errors."""

    def __init__(self, message: str, *, code: str = "inference_pipeline_error") -> None:
        super().__init__(message, code=code)


class InferenceRequestNotFoundError(InferencePipelineError):
    """Raised when an inference request cannot be resolved."""

    def __init__(self, request_id: str) -> None:
        self.request_id = request_id
        super().__init__(f"Inference request not found: {request_id}", code="request_not_found")


class ModelResolutionError(InferencePipelineError):
    """Raised when model resolution fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="model_resolution_error")


class InferenceValidationError(InferencePipelineError):
    """Raised when inference validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="inference_validation_error")


class InferenceDispatchError(InferencePipelineError):
    """Raised when inference dispatch fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="inference_dispatch_error")
