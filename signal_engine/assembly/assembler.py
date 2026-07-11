"""Assemble ExplainableSignal instances from typed requests."""

from __future__ import annotations

from pydantic import ValidationError

from models.decision import DecisionSource, DecisionState
from models.signal import ExplainableSignal
from signal_engine.contracts.assembly_request import SignalAssemblyRequest
from signal_engine.exceptions import SignalAssemblyError


class SignalAssembler:
    """Constructs ExplainableSignal values without bypassing model validators."""

    def assemble(self, request: SignalAssemblyRequest) -> ExplainableSignal:
        """Validate request invariants, then build an ExplainableSignal."""
        self._validate_request(request)
        try:
            return ExplainableSignal(
                signal_id=request.signal_id,
                symbol_id=request.symbol_id,
                market_id=request.market_id,
                decision=request.decision,
                decision_source=request.decision_source,
                indicators_used=request.indicators_used,
                indicator_values=request.indicator_values,
                ml_prediction=request.ml_prediction,
                llm_insight=request.llm_insight,
                confidence=request.confidence,
                risk_assessment=request.risk_assessment,
                invalidation=request.invalidation,
                alternative_scenario=request.alternative_scenario,
                provenance=request.provenance,
                reproducibility=request.reproducibility,
            )
        except ValidationError as error:
            msg = f"ExplainableSignal validation failed: {error}"
            raise SignalAssemblyError(msg) from error

    def _validate_request(self, request: SignalAssemblyRequest) -> None:
        if not request.indicators_used:
            raise SignalAssemblyError("indicators_used must not be empty")
        if not request.indicator_values:
            raise SignalAssemblyError("indicator_values must not be empty")
        if request.decision_source == DecisionSource.AI_ENHANCED_ML and request.llm_insight is None:
            raise SignalAssemblyError(
                "llm_insight is required when decision_source is ai_enhanced_ml"
            )
        if (
            request.decision_source in {DecisionSource.AI_ENHANCED_ML, DecisionSource.ML_ONLY}
            and request.ml_prediction is None
        ):
            raise SignalAssemblyError(
                "ml_prediction is required for ai_enhanced_ml and ml_only sources"
            )
        if request.decision in {DecisionState.BUY, DecisionState.SELL} and request.confidence <= 0:
            raise SignalAssemblyError("directional decisions require confidence > 0")
