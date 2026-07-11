"""Unit tests for SignalAssembler."""

from __future__ import annotations

import pytest

from models.decision import DecisionSource, DecisionState
from signal_engine import SignalAssembler, SignalAssemblyError, SignalAssemblyRequest
from tests.signal_helpers import make_assembly_request, make_llm_insight, make_ml_prediction


@pytest.mark.unit
def test_assemble_statistical_hold_signal() -> None:
    assembler = SignalAssembler()
    signal = assembler.assemble(make_assembly_request())
    assert signal.signal_id == "sig-1"
    assert signal.decision == DecisionState.HOLD
    assert signal.ml_prediction is None
    assert signal.llm_insight is None


@pytest.mark.unit
def test_assemble_ai_enhanced_buy_signal() -> None:
    assembler = SignalAssembler()
    signal = assembler.assemble(
        make_assembly_request(
            decision=DecisionState.BUY,
            decision_source=DecisionSource.AI_ENHANCED_ML,
            confidence=0.72,
            indicators_used=("rsi_14", "macd"),
            indicator_values={"rsi_14": 58.0, "macd": 0.12},
            ml_prediction=make_ml_prediction(),
            llm_insight=make_llm_insight(),
        )
    )
    assert signal.decision == DecisionState.BUY
    assert signal.ml_prediction is not None
    assert signal.llm_insight is not None


@pytest.mark.unit
def test_assemble_rejects_ml_only_without_prediction() -> None:
    assembler = SignalAssembler()
    with pytest.raises(SignalAssemblyError, match="ml_prediction"):
        assembler.assemble(
            make_assembly_request(decision_source=DecisionSource.ML_ONLY, ml_prediction=None)
        )


@pytest.mark.unit
def test_assemble_rejects_ai_enhanced_without_llm() -> None:
    assembler = SignalAssembler()
    with pytest.raises(SignalAssemblyError, match="llm_insight"):
        assembler.assemble(
            make_assembly_request(
                decision_source=DecisionSource.AI_ENHANCED_ML,
                ml_prediction=make_ml_prediction(),
                llm_insight=None,
            )
        )


@pytest.mark.unit
def test_assemble_rejects_buy_with_zero_confidence() -> None:
    assembler = SignalAssembler()
    with pytest.raises(SignalAssemblyError, match="confidence"):
        assembler.assemble(
            make_assembly_request(
                decision=DecisionState.BUY,
                confidence=0.0,
                decision_source=DecisionSource.STATISTICAL_ONLY,
            )
        )


@pytest.mark.unit
def test_assemble_rejects_empty_indicator_collections_via_construct() -> None:
    assembler = SignalAssembler()
    base = make_assembly_request().model_dump()
    # Bypass request-level Field(min_length=1) to exercise assembler guards.
    empty_indicators = SignalAssemblyRequest.model_construct(**{**base, "indicators_used": ()})
    with pytest.raises(SignalAssemblyError, match="indicators_used"):
        assembler.assemble(empty_indicators)

    empty_values = SignalAssemblyRequest.model_construct(**{**base, "indicator_values": {}})
    with pytest.raises(SignalAssemblyError, match="indicator_values"):
        assembler.assemble(empty_values)


@pytest.mark.unit
def test_assemble_wraps_explainable_signal_validation_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pydantic import ValidationError

    assembler = SignalAssembler()

    def _raise(*_args: object, **_kwargs: object) -> None:
        raise ValidationError.from_exception_data("ExplainableSignal", [])

    monkeypatch.setattr("signal_engine.assembly.assembler.ExplainableSignal", _raise)
    with pytest.raises(SignalAssemblyError, match="ExplainableSignal validation failed"):
        assembler.assemble(make_assembly_request())
