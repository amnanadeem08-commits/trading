"""Validation loop contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from models.decision import DecisionState


class ValidationOutcomeStatus(StrEnum):
    """Outcome of prediction validation."""

    ACCURATE = "accurate"
    PARTIALLY_ACCURATE = "partially_accurate"
    INACCURATE = "inaccurate"
    INCONCLUSIVE = "inconclusive"
    PENDING = "pending"


class ValidationOutcome(PlatformModel):
    """Result of comparing prediction to actual market outcome."""

    validation_id: str = Field(min_length=1)
    prediction_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    predicted_decision: DecisionState
    actual_outcome: str = Field(min_length=1)
    status: ValidationOutcomeStatus
    accuracy_score: float | None = Field(default=None, ge=0.0, le=1.0)
    mistake_category: str | None = None
    validated_at: UTCDateTime = Field(default_factory=utc_now)
