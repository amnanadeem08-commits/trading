"""Data layer exceptions."""

from __future__ import annotations

from models.common import PlatformError


class DataError(PlatformError):
    """Base exception for data layer errors."""

    def __init__(self, message: str, *, code: str = "data_error") -> None:
        super().__init__(message, code=code)


class DatasetNotFoundError(DataError):
    """Raised when a requested dataset is not registered."""

    def __init__(self, dataset_id: str) -> None:
        super().__init__(f"Dataset not found: {dataset_id}", code="dataset_not_found")
        self.dataset_id = dataset_id


class DatasetRegistrationError(DataError):
    """Raised when dataset registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="dataset_registration_error")


class DatasetValidationError(DataError):
    """Raised when dataset validation fails."""

    def __init__(self, message: str, *, errors: tuple[str, ...] = ()) -> None:
        super().__init__(message, code="dataset_validation_error")
        self.errors = errors


class CircularDatasetDependencyError(DatasetValidationError):
    """Raised when circular dataset dependencies are detected."""

    def __init__(self, cycle: tuple[str, ...]) -> None:
        cycle_path = " -> ".join(cycle)
        super().__init__(
            f"Circular dataset dependency detected: {cycle_path}",
            errors=(cycle_path,),
        )
        self.cycle = cycle


class SchemaValidationError(DataError):
    """Raised when schema validation fails."""

    def __init__(self, message: str, *, field_name: str | None = None) -> None:
        super().__init__(message, code="schema_validation_error")
        self.field_name = field_name


class DatasetLoadError(DataError):
    """Raised when dataset loading fails."""

    def __init__(self, message: str, *, dataset_id: str | None = None) -> None:
        super().__init__(message, code="dataset_load_error")
        self.dataset_id = dataset_id


class DatasetStateError(DataError):
    """Raised when an invalid dataset state transition is attempted."""

    def __init__(self, dataset_id: str, current_state: str, operation: str) -> None:
        super().__init__(
            f"Cannot {operation} dataset '{dataset_id}' in state '{current_state}'",
            code="dataset_state_error",
        )
        self.dataset_id = dataset_id
        self.current_state = current_state
        self.operation = operation


class DatasetPersistenceError(DataError):
    """Raised when dataset persistence operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="dataset_persistence_error")


class DatasetCacheError(DataError):
    """Raised when dataset cache operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="dataset_cache_error")
