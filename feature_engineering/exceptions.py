"""Feature engineering framework exceptions."""

from __future__ import annotations

from models.common import PlatformError


class FeatureEngineeringError(PlatformError):
    """Base exception for feature engineering errors."""

    def __init__(self, message: str, *, code: str = "feature_engineering_error") -> None:
        super().__init__(message, code=code)


class FeatureNotFoundError(FeatureEngineeringError):
    """Raised when a feature definition cannot be resolved."""

    def __init__(self, feature_id: str) -> None:
        self.feature_id = feature_id
        super().__init__(f"Feature not found: {feature_id}", code="feature_not_found")


class FeatureRegistrationError(FeatureEngineeringError):
    """Raised when feature registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="feature_registration_error")


class FeatureExtractionError(FeatureEngineeringError):
    """Raised when feature extraction fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="feature_extraction_error")


class FeatureValidationError(FeatureEngineeringError):
    """Raised when feature validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="feature_validation_error")


class FeatureSchemaError(FeatureEngineeringError):
    """Raised when feature schema operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="feature_schema_error")


class FeatureVersionError(FeatureEngineeringError):
    """Raised when feature version operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="feature_version_error")
