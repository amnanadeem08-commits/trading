"""Framework adapter exceptions."""


class FrameworkAdapterError(Exception):
    """Base exception for framework adapter errors."""


class AdapterNotFoundError(FrameworkAdapterError):
    """Raised when an adapter is not registered."""


class AdapterValidationError(FrameworkAdapterError):
    """Raised when adapter validation fails."""


class AdapterResolutionError(FrameworkAdapterError):
    """Raised when adapter resolution fails."""


class AdapterLoadError(FrameworkAdapterError):
    """Raised when adapter loading fails."""


class AdapterHealthError(FrameworkAdapterError):
    """Raised when adapter health checks fail."""


class AdapterFactoryError(FrameworkAdapterError):
    """Raised when adapter factory operations fail."""
