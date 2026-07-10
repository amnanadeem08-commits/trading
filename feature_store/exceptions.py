"""Feature store exceptions."""

from __future__ import annotations

from models.common import PlatformError


class FeatureStoreError(PlatformError):
    """Base exception for feature store errors."""

    def __init__(self, message: str, *, code: str = "feature_store_error") -> None:
        super().__init__(message, code=code)


class FeatureRecordNotFoundError(FeatureStoreError):
    """Raised when a feature record cannot be resolved."""

    def __init__(self, record_id: str) -> None:
        self.record_id = record_id
        super().__init__(f"Feature record not found: {record_id}", code="record_not_found")


class DatasetNotFoundError(FeatureStoreError):
    """Raised when a feature dataset cannot be resolved."""

    def __init__(self, dataset_id: str) -> None:
        self.dataset_id = dataset_id
        super().__init__(f"Feature dataset not found: {dataset_id}", code="dataset_not_found")


class DatasetRegistrationError(FeatureStoreError):
    """Raised when dataset registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="dataset_registration_error")


class SnapshotNotFoundError(FeatureStoreError):
    """Raised when a feature snapshot cannot be resolved."""

    def __init__(self, snapshot_id: str) -> None:
        self.snapshot_id = snapshot_id
        super().__init__(f"Feature snapshot not found: {snapshot_id}", code="snapshot_not_found")


class FeatureStoreValidationError(FeatureStoreError):
    """Raised when feature store validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="feature_store_validation_error")


class FeatureVersionError(FeatureStoreError):
    """Raised when dataset version operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="feature_version_error")
