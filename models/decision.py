"""Decision engine contracts. Prediction is not a decision."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, ReproducibilityKey, UTCDateTime, utc_now


class DecisionState(StrEnum):
    """All valid decision engine output states."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WAIT = "WAIT"
    IGNORE = "IGNORE"
    PARTIAL_EXIT = "PARTIAL_EXIT"
    FULL_EXIT = "FULL_EXIT"


class DecisionSource(StrEnum):
    """Which layer produced the primary decision signal."""

    AI_ENHANCED_ML = "ai_enhanced_ml"
    ML_ONLY = "ml_only"
    STATISTICAL_ONLY = "statistical_only"
    FAIL_SAFE_HOLD = "fail_safe_hold"


class TradingDecision(PlatformModel):
    """Actionable decision produced by the Decision Engine."""

    decision_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    state: DecisionState
    source: DecisionSource
    confidence: float = Field(ge=0.0, le=1.0)
    strategy_id: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    reproducibility: ReproducibilityKey
    created_at: UTCDateTime = Field(default_factory=utc_now)
    rationale: str = Field(min_length=1, description="Human-readable decision rationale")
