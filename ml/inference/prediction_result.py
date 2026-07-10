"""Prediction result contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class PredictionResult(PlatformModel):
    """Outcome of an inference operation."""

    inference_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    outputs: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    metadata: dict[str, str] = Field(default_factory=dict)
    execution_info: dict[str, str] = Field(default_factory=dict)
    completed_at: UTCDateTime = Field(default_factory=utc_now)
