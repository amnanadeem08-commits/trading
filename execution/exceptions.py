"""Execution layer exceptions."""

from __future__ import annotations

from models.common import PlatformError


class ExecutionError(PlatformError):
    """Base exception for execution layer errors."""

    def __init__(self, message: str, *, code: str = "execution_error") -> None:
        super().__init__(message, code=code)


class ExecutionNotFoundError(ExecutionError):
    """Raised when a requested execution engine is not registered."""

    def __init__(self, execution_id: str) -> None:
        super().__init__(f"Execution engine not found: {execution_id}", code="execution_not_found")
        self.execution_id = execution_id


class ExecutionRegistrationError(ExecutionError):
    """Raised when execution engine registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="execution_registration_error")


class ExecutionStateError(ExecutionError):
    """Raised when an invalid execution state transition is attempted."""

    def __init__(self, execution_id: str, current_state: str, operation: str) -> None:
        super().__init__(
            f"Cannot {operation} execution '{execution_id}' in state '{current_state}'",
            code="execution_state_error",
        )
        self.execution_id = execution_id
        self.current_state = current_state
        self.operation = operation


class ValidationError(ExecutionError):
    """Raised when execution validation operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class DispatchError(ExecutionError):
    """Raised when dispatch operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="dispatch_error")


class OrchestrationError(ExecutionError):
    """Raised when execution orchestration operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="orchestration_error")


class QueueError(ExecutionError):
    """Raised when dispatch queue operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="queue_error")
