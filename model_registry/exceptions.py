"""Model registry exceptions."""

from __future__ import annotations

from models.common import PlatformError


class ModelRegistryError(PlatformError):
    """Base exception for model registry errors."""

    def __init__(self, message: str, *, code: str = "model_registry_error") -> None:
        super().__init__(message, code=code)


class ModelNotFoundError(ModelRegistryError):
    """Raised when a registered model cannot be resolved."""

    def __init__(self, model_id: str) -> None:
        self.model_id = model_id
        super().__init__(f"Registered model not found: {model_id}", code="model_not_found")


class ModelVersionNotFoundError(ModelRegistryError):
    """Raised when a model version cannot be resolved."""

    def __init__(self, version_id: str) -> None:
        self.version_id = version_id
        super().__init__(f"Model version not found: {version_id}", code="version_not_found")


class ModelRegistrationError(ModelRegistryError):
    """Raised when model registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="model_registration_error")


class PromotionError(ModelRegistryError):
    """Raised when model promotion fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="promotion_error")


class ApprovalError(ModelRegistryError):
    """Raised when approval operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="approval_error")


class LineageError(ModelRegistryError):
    """Raised when lineage graph operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="lineage_error")


class RegistryValidationError(ModelRegistryError):
    """Raised when registry validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="registry_validation_error")
