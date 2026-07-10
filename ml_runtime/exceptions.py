"""ML runtime exceptions."""


class MLRuntimeError(Exception):
    """Base exception for ML runtime errors."""


class RuntimeValidationError(MLRuntimeError):
    """Raised when runtime validation fails."""


class ExecutorNotFoundError(MLRuntimeError):
    """Raised when a requested executor is not registered."""


class RuntimeSessionError(MLRuntimeError):
    """Raised when a runtime session operation fails."""


class RuntimeNotInitializedError(MLRuntimeError):
    """Raised when the runtime has not been initialized."""
