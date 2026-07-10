"""Workflow runtime exceptions."""

from __future__ import annotations

from models.common import PlatformError


class WorkflowError(PlatformError):
    """Base exception for workflow runtime errors."""

    def __init__(self, message: str, *, code: str = "workflow_error") -> None:
        super().__init__(message, code=code)


class WorkflowValidationError(WorkflowError):
    """Raised when workflow graph validation fails."""

    def __init__(self, message: str, *, errors: tuple[str, ...] = ()) -> None:
        super().__init__(message, code="workflow_validation_error")
        self.errors = errors


class CircularJobDependencyError(WorkflowValidationError):
    """Raised when circular job dependencies are detected."""

    def __init__(self, cycle: tuple[str, ...]) -> None:
        cycle_path = " -> ".join(cycle)
        super().__init__(
            f"Circular job dependency detected: {cycle_path}",
            errors=(cycle_path,),
        )
        self.cycle = cycle


class WorkflowNotFoundError(WorkflowError):
    """Raised when a workflow is not registered."""

    def __init__(self, workflow_id: str) -> None:
        super().__init__(f"Workflow not found: {workflow_id}", code="workflow_not_found")
        self.workflow_id = workflow_id


class JobNotFoundError(WorkflowError):
    """Raised when a job is not found in a workflow."""

    def __init__(self, job_id: str) -> None:
        super().__init__(f"Job not found: {job_id}", code="job_not_found")
        self.job_id = job_id


class WorkflowCancelledError(WorkflowError):
    """Raised when workflow execution is cancelled."""

    def __init__(self, workflow_id: str) -> None:
        super().__init__(
            f"Workflow execution cancelled: {workflow_id}",
            code="workflow_cancelled",
        )
        self.workflow_id = workflow_id


class JobTimeoutError(WorkflowError):
    """Raised when a job exceeds its timeout."""

    def __init__(self, job_id: str, timeout_seconds: int) -> None:
        super().__init__(
            f"Job timed out after {timeout_seconds}s: {job_id}",
            code="job_timeout",
        )
        self.job_id = job_id
        self.timeout_seconds = timeout_seconds


class JobExecutionError(WorkflowError):
    """Raised when a job fails during execution."""

    def __init__(self, job_id: str, message: str) -> None:
        super().__init__(message, code="job_execution_error")
        self.job_id = job_id


class WorkflowRegistrationError(WorkflowError):
    """Raised when workflow registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="workflow_registration_error")


class InvalidJobStateError(WorkflowError):
    """Raised when a job is in an invalid state for an operation."""

    def __init__(self, job_id: str, state: str, operation: str) -> None:
        super().__init__(
            f"Invalid job state '{state}' for {operation}: {job_id}",
            code="invalid_job_state",
        )
        self.job_id = job_id


class CheckpointError(WorkflowError):
    """Raised when checkpoint operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="checkpoint_error")
