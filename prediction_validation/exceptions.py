"""Prediction validation domain exceptions."""

from __future__ import annotations

from models.common import PlatformError


class PredictionValidationError(PlatformError):
    """Base error for prediction validation."""

    def __init__(self, message: str, *, code: str = "prediction_validation_error") -> None:
        super().__init__(message, code=code)


class PredictionNotFoundError(PredictionValidationError):
    """Raised when a prediction record is missing."""

    def __init__(self, prediction_id: str) -> None:
        super().__init__(f"Prediction not found: {prediction_id}", code="prediction_not_found")
        self.prediction_id = prediction_id


class LookAheadValidationError(PredictionValidationError):
    """Raised when evaluation would use market data after as_of."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="look_ahead_validation")


class PredictionImmutableError(PredictionValidationError):
    """Raised when a mutation of a stored prediction is attempted."""

    def __init__(self, prediction_id: str) -> None:
        super().__init__(
            f"Prediction records are immutable: {prediction_id}",
            code="prediction_immutable",
        )
        self.prediction_id = prediction_id
