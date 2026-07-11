"""Unit tests for SignalValidator accept/reject paths."""

from __future__ import annotations

import pytest

from models.decision import DecisionSource, DecisionState
from models.risk import RiskAssessment
from models.signal import ExplainableSignal, InvalidationRule
from signal_engine import SignalAssembler, SignalValidationResult, SignalValidator
from tests.signal_helpers import make_assembly_request, make_reproducibility


def _valid_signal() -> ExplainableSignal:
    return SignalAssembler().assemble(make_assembly_request())


def _invalid_directional() -> ExplainableSignal:
    base = _valid_signal()
    return ExplainableSignal.model_construct(
        signal_id=base.signal_id,
        symbol_id=base.symbol_id,
        market_id=base.market_id,
        decision=DecisionState.BUY,
        decision_source=DecisionSource.STATISTICAL_ONLY,
        indicators_used=base.indicators_used,
        indicator_values=base.indicator_values,
        ml_prediction=None,
        llm_insight=None,
        confidence=0.0,
        risk_assessment=base.risk_assessment,
        invalidation=base.invalidation,
        alternative_scenario=base.alternative_scenario,
        provenance=base.provenance,
        reproducibility=make_reproducibility(),
    )


@pytest.mark.unit
def test_validator_accepts_valid_signal() -> None:
    result = SignalValidator().validate(_valid_signal())
    assert isinstance(result, SignalValidationResult)
    assert result.passed is True
    assert result.reasons == ()
    assert result.lifecycle_state == "accepted"


@pytest.mark.unit
def test_validator_rejects_directional_zero_confidence() -> None:
    result = SignalValidator().validate(_invalid_directional())
    assert result.passed is False
    assert result.lifecycle_state == "rejected"
    assert any("confidence > 0" in reason for reason in result.reasons)


@pytest.mark.unit
def test_validator_rejects_blank_risk_and_invalidation() -> None:
    base = _valid_signal()
    broken = ExplainableSignal.model_construct(
        signal_id=base.signal_id,
        symbol_id=base.symbol_id,
        market_id=base.market_id,
        decision=DecisionState.HOLD,
        decision_source=DecisionSource.STATISTICAL_ONLY,
        indicators_used=(),
        indicator_values={},
        ml_prediction=None,
        llm_insight=None,
        confidence=0.0,
        risk_assessment=RiskAssessment.model_construct(exposure_impact="  "),
        invalidation=InvalidationRule.model_construct(condition=""),
        alternative_scenario="  ",
        provenance=base.provenance,
        reproducibility=make_reproducibility(),
    )
    result = SignalValidator().validate(broken)
    assert result.passed is False
    joined = " | ".join(result.reasons)
    assert "indicators_used" in joined
    assert "exposure_impact" in joined
    assert "invalidation.condition" in joined
    assert "alternative_scenario" in joined


@pytest.mark.unit
def test_validator_rejects_ml_only_without_prediction() -> None:
    base = _valid_signal()
    broken = ExplainableSignal.model_construct(
        signal_id=base.signal_id,
        symbol_id=base.symbol_id,
        market_id=base.market_id,
        decision=DecisionState.HOLD,
        decision_source=DecisionSource.ML_ONLY,
        indicators_used=base.indicators_used,
        indicator_values=base.indicator_values,
        ml_prediction=None,
        llm_insight=None,
        confidence=0.4,
        risk_assessment=base.risk_assessment,
        invalidation=base.invalidation,
        alternative_scenario=base.alternative_scenario,
        provenance=base.provenance,
        reproducibility=make_reproducibility(),
    )
    result = SignalValidator().validate(broken)
    assert result.passed is False
    assert any("ml_prediction" in reason for reason in result.reasons)
