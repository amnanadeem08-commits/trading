"""Service layer exceptions."""

from __future__ import annotations

from models.common import PlatformError


class ServiceError(PlatformError):
    """Base exception for service layer errors."""

    def __init__(self, message: str, *, code: str = "service_error") -> None:
        super().__init__(message, code=code)


class ServiceNotFoundError(ServiceError):
    """Raised when a requested service is not registered."""

    def __init__(self, service_name: str) -> None:
        super().__init__(
            f"Service not found: {service_name}",
            code="service_not_found",
        )
        self.service_name = service_name


class ServiceRegistrationError(ServiceError):
    """Raised when service registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="service_registration_error")


class ServiceLifecycleError(ServiceError):
    """Raised when lifecycle operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="service_lifecycle_error")


class ServiceValidationError(ServiceError):
    """Raised when service graph validation fails."""

    def __init__(self, message: str, *, errors: tuple[str, ...] = ()) -> None:
        super().__init__(message, code="service_validation_error")
        self.errors = errors


class CircularDependencyError(ServiceValidationError):
    """Raised when circular service dependencies are detected."""

    def __init__(self, cycle: tuple[str, ...]) -> None:
        cycle_path = " -> ".join(cycle)
        super().__init__(
            f"Circular dependency detected: {cycle_path}",
            errors=(cycle_path,),
        )
        self.cycle = cycle


class ServiceNotReadyError(ServiceError):
    """Raised when an operation requires a ready service."""

    def __init__(self, service_name: str) -> None:
        super().__init__(
            f"Service is not ready: {service_name}",
            code="service_not_ready",
        )
        self.service_name = service_name


class ServiceResolutionError(ServiceError):
    """Raised when dependency resolution fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="service_resolution_error")
