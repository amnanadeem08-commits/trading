"""Core layer exceptions."""

from __future__ import annotations

from models.common import PlatformError


class CoreError(PlatformError):
    """Base exception for core layer errors."""

    def __init__(self, message: str, *, code: str = "core_error") -> None:
        super().__init__(message, code=code)


class EntityNotFoundError(CoreError):
    """Raised when a requested entity is not registered."""

    def __init__(self, entity_id: str) -> None:
        super().__init__(f"Entity not found: {entity_id}", code="entity_not_found")
        self.entity_id = entity_id


class EntityRegistrationError(CoreError):
    """Raised when entity registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="entity_registration_error")


class CoreValidationError(CoreError):
    """Raised when core validation fails."""

    def __init__(self, message: str, *, errors: tuple[str, ...] = ()) -> None:
        super().__init__(message, code="core_validation_error")
        self.errors = errors


class CircularEntityDependencyError(CoreValidationError):
    """Raised when circular entity dependencies are detected."""

    def __init__(self, cycle: tuple[str, ...]) -> None:
        cycle_path = " -> ".join(cycle)
        super().__init__(
            f"Circular entity dependency detected: {cycle_path}",
            errors=(cycle_path,),
        )
        self.cycle = cycle


class CoreStateError(CoreError):
    """Raised when an invalid operation state transition is attempted."""

    def __init__(self, entity_id: str, current_state: str, operation: str) -> None:
        super().__init__(
            f"Cannot {operation} entity '{entity_id}' in state '{current_state}'",
            code="core_state_error",
        )
        self.entity_id = entity_id
        self.current_state = current_state
        self.operation = operation


class CoreContextError(CoreError):
    """Raised when core context construction or resolution fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="core_context_error")


class CoreRuntimeError(CoreError):
    """Raised when core runtime operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="core_runtime_error")


class IdentifierError(CoreError):
    """Raised when identifier generation or validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="identifier_error")
