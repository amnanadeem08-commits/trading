"""Typed input contract for assembling an ExplainableSignal."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, ReproducibilityKey
from models.decision import DecisionSource, DecisionState
from models.prediction import LLMInsight, MLPrediction
from models.risk import RiskAssessment
from models.signal import InvalidationRule, Provenance


class SignalAssemblyRequest(PlatformModel):
    """Structured inputs required to assemble an explainable signal."""

    signal_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    decision: DecisionState
    decision_source: DecisionSource
    indicators_used: tuple[str, ...] = Field(min_length=1)
    indicator_values: dict[str, float | str | int | bool] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    risk_assessment: RiskAssessment
    invalidation: InvalidationRule
    alternative_scenario: str = Field(min_length=1)
    provenance: Provenance
    reproducibility: ReproducibilityKey
    ml_prediction: MLPrediction | None = None
    llm_insight: LLMInsight | None = None
