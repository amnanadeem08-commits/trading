"""Immutable prediction record contracts."""

from __future__ import annotations

from pydantic import Field, model_validator

from models.common import PlatformModel, UTCDateTime, utc_now
from models.prediction import SignalDirection


class PredictionRecord(PlatformModel):
    """Append-only prediction to validate against future market outcomes."""

    prediction_id: str = Field(min_length=1)
    signal_id: str | None = None
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    predicted_at: UTCDateTime
    prediction_horizon_bars: int = Field(ge=1)
    validation_due_at: UTCDateTime
    predicted_direction: SignalDirection
    predicted_target: float | None = Field(default=None, gt=0.0)
    expected_move_pct: float | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    model_reference: str = Field(min_length=1)
    reference_price: float = Field(gt=0.0)
    recorded_at: UTCDateTime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_directional_prediction(self) -> PredictionRecord:
        if self.predicted_direction == SignalDirection.HOLD:
            msg = "HOLD predictions are not valid for directional outcome validation"
            raise ValueError(msg)
        if self.validation_due_at < self.predicted_at:
            msg = "validation_due_at must be >= predicted_at"
            raise ValueError(msg)
        return self
