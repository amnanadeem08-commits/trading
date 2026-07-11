"""Validate assembled explainable signals before registry acceptance."""

from __future__ import annotations

from models.decision import DecisionSource, DecisionState
from models.signal import ExplainableSignal
from signal_engine.validation.validation_result import SignalValidationResult


class SignalValidator:
    """Structural validator — reject paths always include explicit reasons."""

    def validate(self, signal: ExplainableSignal) -> SignalValidationResult:
        """Return accept/reject result without mutating the signal."""
        reasons: list[str] = []

        if not signal.signal_id.strip():
            reasons.append("signal_id must not be empty")
        if not signal.indicators_used:
            reasons.append("indicators_used must not be empty")
        if not signal.indicator_values:
            reasons.append("indicator_values must not be empty")
        if signal.decision in {DecisionState.BUY, DecisionState.SELL} and signal.confidence <= 0:
            reasons.append("directional decisions require confidence > 0")
        if not signal.risk_assessment.exposure_impact.strip():
            reasons.append("risk_assessment.exposure_impact is required")
        if not signal.invalidation.condition.strip():
            reasons.append("invalidation.condition is required")
        if not signal.alternative_scenario.strip():
            reasons.append("alternative_scenario is required")
        if signal.decision_source == DecisionSource.AI_ENHANCED_ML and signal.llm_insight is None:
            reasons.append("llm_insight required when decision_source is ai_enhanced_ml")
        if (
            signal.decision_source in {DecisionSource.AI_ENHANCED_ML, DecisionSource.ML_ONLY}
            and signal.ml_prediction is None
        ):
            reasons.append("ml_prediction required for ai_enhanced_ml and ml_only sources")

        passed = not reasons
        return SignalValidationResult(
            signal_id=signal.signal_id or "unknown",
            passed=passed,
            reasons=tuple(reasons),
            lifecycle_state="accepted" if passed else "rejected",
        )
