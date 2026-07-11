"""Unit tests for confidence / risk / invalidation binding."""

from __future__ import annotations

import pytest

from models.decision import DecisionState
from risk.scoring.confidence_score import ConfidenceScore
from signal_engine import (
    SignalAssembler,
    SignalRiskAttachmentError,
    StubRiskBindingProvider,
    assert_directional_confidence,
    attach_confidence,
    attach_risk_bindings,
    attach_risk_bindings_from_provider,
    build_invalidation_rule,
    build_risk_assessment,
    compute_atr,
    confidence_value_from_score,
    ensure_risk_bindings_present,
    invalidation_from_atr,
    invalidation_from_structure,
)
from tests.signal_helpers import make_assembly_request


@pytest.mark.unit
def test_confidence_from_score_and_directional_rules() -> None:
    score = ConfidenceScore(value=0.55, source="unit")
    assert confidence_value_from_score(score) == 0.55
    assert_directional_confidence(DecisionState.HOLD, 0.0)
    with pytest.raises(SignalRiskAttachmentError, match="confidence > 0"):
        assert_directional_confidence(DecisionState.BUY, 0.0)
    with pytest.raises(SignalRiskAttachmentError, match="confidence > 0"):
        attach_confidence(
            make_assembly_request(decision=DecisionState.SELL),
            0.0,
        )


@pytest.mark.unit
def test_build_risk_and_invalidation_failures() -> None:
    with pytest.raises(SignalRiskAttachmentError, match="exposure_impact"):
        build_risk_assessment(exposure_impact="  ")
    with pytest.raises(SignalRiskAttachmentError, match="condition"):
        build_invalidation_rule(condition="")
    assessment = build_risk_assessment(
        exposure_impact="Within limits.",
        notes="Confidence is not a probability of profit.",
    )
    assert assessment.exposure_impact == "Within limits."


@pytest.mark.unit
def test_invalidation_from_structure_and_atr() -> None:
    buy_rule = invalidation_from_structure(
        DecisionState.BUY,
        support=100.0,
    )
    assert buy_rule.price_level == 100.0
    sell_rule = invalidation_from_structure(
        DecisionState.SELL,
        resistance=110.0,
    )
    assert sell_rule.price_level == 110.0
    with pytest.raises(SignalRiskAttachmentError, match="support"):
        invalidation_from_structure(DecisionState.BUY, support=None)

    atr_rule = invalidation_from_atr(
        DecisionState.BUY,
        current_price=100.0,
        atr=2.0,
        multiplier=1.5,
    )
    assert atr_rule.price_level == pytest.approx(97.0)


@pytest.mark.unit
def test_compute_atr_basic() -> None:
    closes = [10.0 + i * 0.1 for i in range(20)]
    highs = [c + 0.5 for c in closes]
    lows = [c - 0.5 for c in closes]
    atr = compute_atr(highs, lows, closes, period=14)
    assert atr > 0


@pytest.mark.unit
def test_attach_risk_bindings_wires_assembler() -> None:
    request = attach_risk_bindings(
        make_assembly_request(decision=DecisionState.BUY, confidence=0.0),
        confidence=0.7,
        assessment=build_risk_assessment(exposure_impact="OK"),
        invalidation=build_invalidation_rule(condition="Break below 95"),
        decision=DecisionState.BUY,
    )
    assert request.confidence == 0.7
    assert request.risk_assessment.exposure_impact == "OK"
    assert request.invalidation.condition.startswith("Break")
    signal = SignalAssembler().assemble(request)
    assert signal.confidence == 0.7
    assert signal.risk_assessment.exposure_impact == "OK"
    assert signal.invalidation.condition.startswith("Break")


@pytest.mark.unit
def test_attach_from_provider_and_failure_modes() -> None:
    provider = StubRiskBindingProvider(confidence=0.66)
    request = attach_risk_bindings_from_provider(
        make_assembly_request(
            decision=DecisionState.BUY,
            indicator_values={
                "rsi_14": 55.0,
                "support": 98.0,
                "close": 100.0,
                "atr_14": 1.5,
            },
        ),
        provider,
    )
    assert request.confidence == 0.66
    assert request.invalidation.price_level == 98.0
    ensure_risk_bindings_present(request)

    with pytest.raises(SignalRiskAttachmentError, match="forced failure"):
        attach_risk_bindings_from_provider(
            make_assembly_request(decision=DecisionState.BUY),
            StubRiskBindingProvider(fail=True),
        )

    with pytest.raises(SignalRiskAttachmentError, match="confidence > 0"):
        attach_risk_bindings_from_provider(
            make_assembly_request(decision=DecisionState.BUY),
            StubRiskBindingProvider(zero_directional_confidence=True),
        )


@pytest.mark.unit
def test_provider_unexpected_exception_is_wrapped() -> None:
    class BrokenProvider:
        def get_confidence(self, **kwargs: object) -> object:
            raise RuntimeError("boom")

        def get_assessment(self, **kwargs: object) -> object:
            raise RuntimeError("unused")

        def get_invalidation(self, **kwargs: object) -> object:
            raise RuntimeError("unused")

    with pytest.raises(SignalRiskAttachmentError, match="provider failed"):
        attach_risk_bindings_from_provider(
            make_assembly_request(decision=DecisionState.BUY),
            BrokenProvider(),  # type: ignore[arg-type]
        )
