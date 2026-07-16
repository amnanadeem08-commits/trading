"""Aggregated prediction validation metrics."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class ConfidenceCalibrationBucket(PlatformModel):
    """Directional accuracy within a confidence range."""

    bucket_label: str = Field(min_length=1)
    total: int = Field(ge=0)
    correct: int = Field(ge=0)
    accuracy: float | None = Field(default=None, ge=0.0, le=1.0)


class PredictionValidationSummary(PlatformModel):
    """Deterministic metrics over recorded predictions and outcomes."""

    total_predictions: int = Field(ge=0)
    pending: int = Field(ge=0)
    validated: int = Field(ge=0)
    expired: int = Field(ge=0)
    insufficient_data: int = Field(ge=0)
    invalid: int = Field(ge=0)
    correct: int = Field(ge=0)
    incorrect: int = Field(ge=0)
    directional_accuracy: float | None = Field(default=None, ge=0.0, le=1.0)
    average_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    average_confidence_correct: float | None = Field(default=None, ge=0.0, le=1.0)
    average_confidence_incorrect: float | None = Field(default=None, ge=0.0, le=1.0)
    calibration_buckets: tuple[ConfidenceCalibrationBucket, ...] = ()
    average_realized_move_pct: float | None = None
    average_prediction_error_pct: float | None = Field(default=None, ge=0.0)
