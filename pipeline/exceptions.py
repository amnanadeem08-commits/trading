"""Pipeline engine exceptions."""

from __future__ import annotations

from models.common import PlatformError


class PipelineError(PlatformError):
    """Base exception for pipeline engine errors."""

    def __init__(self, message: str, *, code: str = "pipeline_error") -> None:
        super().__init__(message, code=code)


class PipelineValidationError(PipelineError):
    """Raised when pipeline graph validation fails."""

    def __init__(self, message: str, *, errors: tuple[str, ...] = ()) -> None:
        super().__init__(message, code="pipeline_validation_error")
        self.errors = errors


class CircularStageDependencyError(PipelineValidationError):
    """Raised when circular stage dependencies are detected."""

    def __init__(self, cycle: tuple[str, ...]) -> None:
        cycle_path = " -> ".join(cycle)
        super().__init__(
            f"Circular stage dependency detected: {cycle_path}",
            errors=(cycle_path,),
        )
        self.cycle = cycle


class StageNotFoundError(PipelineError):
    """Raised when a requested stage is not registered."""

    def __init__(self, stage_name: str) -> None:
        super().__init__(f"Stage not found: {stage_name}", code="stage_not_found")
        self.stage_name = stage_name


class PipelineNotFoundError(PipelineError):
    """Raised when a requested pipeline is not registered."""

    def __init__(self, pipeline_name: str) -> None:
        super().__init__(f"Pipeline not found: {pipeline_name}", code="pipeline_not_found")
        self.pipeline_name = pipeline_name


class PipelineCancelledError(PipelineError):
    """Raised when a pipeline execution is cancelled."""

    def __init__(self, pipeline_name: str) -> None:
        super().__init__(
            f"Pipeline execution cancelled: {pipeline_name}",
            code="pipeline_cancelled",
        )
        self.pipeline_name = pipeline_name


class PipelineTimeoutError(PipelineError):
    """Raised when a pipeline or stage exceeds its timeout."""

    def __init__(self, target: str, timeout_seconds: int) -> None:
        super().__init__(
            f"Timeout after {timeout_seconds}s: {target}",
            code="pipeline_timeout",
        )
        self.target = target
        self.timeout_seconds = timeout_seconds


class StageExecutionError(PipelineError):
    """Raised when a stage fails during execution."""

    def __init__(self, stage_name: str, message: str) -> None:
        super().__init__(message, code="stage_execution_error")
        self.stage_name = stage_name


class PipelineRegistrationError(PipelineError):
    """Raised when pipeline registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="pipeline_registration_error")
