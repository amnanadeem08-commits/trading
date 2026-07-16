"""Prediction validation configuration."""

from __future__ import annotations

from datetime import timedelta

from pydantic import Field

from models.common import PlatformModel


class PredictionValidationConfig(PlatformModel):
    """Deterministic parameters for outcome evaluation."""

    calibration_bucket_size: float = Field(gt=0.0, le=1.0, default=0.1)
    max_wait_after_due: timedelta = Field(default=timedelta(hours=5))
    default_bar_interval: timedelta = Field(default=timedelta(hours=1))
