"""Explainability contracts. Every recommendation must be fully explainable."""

from __future__ import annotations

from pydantic import Field, model_validator

from models.common import PlatformModel, ReproducibilityKey, UTCDateTime, utc_now
from models.decision import DecisionSource, DecisionState
from models.prediction import LLMInsight, MLPrediction, SignalDirection
from models.risk import RiskAssessment


class InvalidationRule(PlatformModel):
    """Condition that would invalidate the recommendation."""

    condition: str = Field(min_length=1)
    price_level: float | None = Field(default=None, gt=0)


class Provenance(PlatformModel):
    """Full lineage of a recommendation."""

    market_id: str = Field(min_length=1)
    connector_version: str = Field(min_length=1)
    model_versions: dict[str, str] = Field(default_factory=dict)
    prompt_version: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    provider: str | None = None
    feature_snapshot_version: str = Field(min_length=1)


class ExplainableSignal(PlatformModel):
    """Mandatory explainability bundle for every recommendation. No black boxes."""

    signal_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    decision: DecisionState
    decision_source: DecisionSource
    indicators_used: tuple[str, ...]
    indicator_values: dict[str, float | str | int | bool]
    ml_prediction: MLPrediction | None = None
    llm_insight: LLMInsight | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    risk_assessment: RiskAssessment
    invalidation: InvalidationRule
    alternative_scenario: str = Field(min_length=1)
    provenance: Provenance
    reproducibility: ReproducibilityKey
    created_at: UTCDateTime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_explainability_requirements(self) -> ExplainableSignal:
        if not self.indicators_used:
            msg = "indicators_used must not be empty"
            raise ValueError(msg)
        if not self.indicator_values:
            msg = "indicator_values must not be empty"
            raise ValueError(msg)
        if self.decision_source == DecisionSource.AI_ENHANCED_ML and self.llm_insight is None:
            msg = "llm_insight required when decision_source is ai_enhanced_ml"
            raise ValueError(msg)
        if (
            self.decision_source in {DecisionSource.AI_ENHANCED_ML, DecisionSource.ML_ONLY}
            and self.ml_prediction is None
        ):
            msg = "ml_prediction required for ai_enhanced_ml and ml_only sources"
            raise ValueError(msg)
        if self.decision in {DecisionState.BUY, DecisionState.SELL} and self.confidence <= 0:
            msg = "directional decisions require confidence > 0"
            raise ValueError(msg)
        return self


class DirectionalRecommendation(PlatformModel):
    """Lightweight directional output before full decision pipeline."""

    direction: SignalDirection
    confidence: float = Field(ge=0.0, le=1.0)
