"""Validation outcome contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime


class ValidationStatus(StrEnum):
    """Lifecycle status for a prediction validation outcome."""

    PENDING = "pending"
    VALIDATED = "validated"
    EXPIRED = "expired"
    INSUFFICIENT_DATA = "insufficient_data"
    INVALID = "invalid"


class ValidationOutcomeRecord(PlatformModel):
    """Outcome of evaluating a prediction against realized market data."""

    validation_id: str = Field(min_length=1)
    prediction_id: str = Field(min_length=1)
    status: ValidationStatus
    actual_price: float | None = Field(default=None, gt=0.0)
    actual_move_pct: float | None = None
    is_directionally_correct: bool | None = None
    move_error: float | None = Field(default=None, ge=0.0)
    prediction_error_pct: float | None = Field(default=None, ge=0.0)
    validated_at: UTCDateTime | None = None
    validation_notes: tuple[str, ...] = ()
