"""Historical data repository exceptions."""

from __future__ import annotations

from models.common import PlatformError


class HistoricalError(PlatformError):
    """Base exception for historical data repository errors."""

    def __init__(self, message: str, *, code: str = "historical_error") -> None:
        super().__init__(message, code=code)


class DatasetNotFoundError(HistoricalError):
    """Raised when a historical dataset cannot be resolved."""

    def __init__(self, dataset_id: str) -> None:
        self.dataset_id = dataset_id
        super().__init__(f"Historical dataset not found: {dataset_id}", code="dataset_not_found")


class DatasetRegistrationError(HistoricalError):
    """Raised when dataset registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="dataset_registration_error")


class StorageError(HistoricalError):
    """Raised when storage operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="storage_error")


class ReplayError(HistoricalError):
    """Raised when replay operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="replay_error")


class QueryError(HistoricalError):
    """Raised when query operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="query_error")


class HistoricalValidationError(HistoricalError):
    """Raised when historical validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="historical_validation_error")


class VersionError(HistoricalError):
    """Raised when version operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="version_error")
