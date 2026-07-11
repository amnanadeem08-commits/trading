"""Unit tests for signal → paper order mapping."""

from __future__ import annotations

import pytest

from models.decision import DecisionSource, DecisionState
from models.signal import ExplainableSignal
from paper_trading import (
    PaperMappingError,
    PaperOrderSide,
    PaperTradingOrchestrator,
    adapter_context_from_paper_order,
    map_signal_to_paper_order,
    paper_order_from_signal,
    reset_paper_registry,
)
from signal_engine import SignalAssembler
from tests.signal_helpers import make_assembly_request, make_ml_prediction, make_reproducibility


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_paper_registry()
    yield
    reset_paper_registry()


def _hold_signal(**overrides: object) -> ExplainableSignal:
    request = make_assembly_request(
        signal_id="sig-map-1",
        indicator_values={"rsi_14": 55.0, "close": 101.5},
        **overrides,
    )
    return SignalAssembler().assemble(request)


@pytest.mark.unit
def test_map_valid_hold_signal() -> None:
    signal = _hold_signal()
    result = map_signal_to_paper_order(signal, session_id="ps-1")
    assert result.passed is True
    assert result.order is not None
    assert result.order.side == PaperOrderSide.FLAT
    assert result.order.reference_price == 101.5
    assert result.order.adapter_payload["live_broker"] is False


@pytest.mark.unit
def test_map_directional_requires_reference_price() -> None:
    signal = SignalAssembler().assemble(
        make_assembly_request(
            signal_id="sig-buy",
            decision=DecisionState.BUY,
            confidence=0.7,
            indicator_values={"rsi_14": 40.0},
        )
    )
    rejected = map_signal_to_paper_order(signal, session_id="ps-2")
    assert rejected.passed is False
    assert any("reference price" in reason for reason in rejected.reasons)

    priced = ExplainableSignal.model_construct(
        signal_id=signal.signal_id,
        symbol_id=signal.symbol_id,
        market_id=signal.market_id,
        decision=DecisionState.BUY,
        decision_source=DecisionSource.STATISTICAL_ONLY,
        indicators_used=signal.indicators_used,
        indicator_values={"rsi_14": 40.0, "close": 99.0},
        ml_prediction=None,
        llm_insight=None,
        confidence=0.7,
        risk_assessment=signal.risk_assessment,
        invalidation=signal.invalidation,
        alternative_scenario=signal.alternative_scenario,
        provenance=signal.provenance,
        reproducibility=make_reproducibility(),
    )
    accepted = paper_order_from_signal(priced, session_id="ps-3", request_id="req-3")
    assert accepted.side == PaperOrderSide.BUY
    assert accepted.reference_price == 99.0
    context = adapter_context_from_paper_order(accepted)
    assert context.request_id == "req-3"
    assert context.payload["side"] == "BUY"
    assert context.metadata["path"] == "paper"


@pytest.mark.unit
def test_map_rejects_ml_only_without_prediction() -> None:
    base = _hold_signal()
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
    with pytest.raises(PaperMappingError, match="ml_prediction") as err:
        paper_order_from_signal(broken, session_id="ps-ml")
    assert err.value.reasons


@pytest.mark.unit
def test_map_edge_rejects_and_sell_side() -> None:
    base = _hold_signal()
    empty_ids = ExplainableSignal.model_construct(
        signal_id=" ",
        symbol_id=" ",
        market_id=" ",
        decision=DecisionState.SELL,
        decision_source=DecisionSource.STATISTICAL_ONLY,
        indicators_used=(),
        indicator_values={},
        ml_prediction=None,
        llm_insight=None,
        confidence=0.0,
        risk_assessment=base.risk_assessment.model_copy(update={"exposure_impact": "  "}),
        invalidation=base.invalidation.model_copy(update={"condition": ""}),
        alternative_scenario=base.alternative_scenario,
        provenance=base.provenance,
        reproducibility=make_reproducibility(),
    )
    rejected = map_signal_to_paper_order(
        empty_ids,
        session_id=" ",
        quantity=-1.0,
    )
    assert rejected.passed is False
    joined = " | ".join(rejected.reasons)
    assert "session_id" in joined
    assert "confidence" in joined

    sell = ExplainableSignal.model_construct(
        signal_id="sig-sell",
        symbol_id=base.symbol_id,
        market_id=base.market_id,
        decision=DecisionState.SELL,
        decision_source=DecisionSource.STATISTICAL_ONLY,
        indicators_used=base.indicators_used,
        indicator_values={"rsi_14": 70.0, "price": "100.25"},
        ml_prediction=None,
        llm_insight=None,
        confidence=0.55,
        risk_assessment=base.risk_assessment,
        invalidation=base.invalidation,
        alternative_scenario=base.alternative_scenario,
        provenance=base.provenance,
        reproducibility=make_reproducibility(),
    )
    order = paper_order_from_signal(sell, session_id="ps-sell")
    assert order.side == PaperOrderSide.SELL
    assert order.reference_price == 100.25

    signal = SignalAssembler().assemble(
        make_assembly_request(
            decision=DecisionState.BUY,
            confidence=0.66,
            decision_source=DecisionSource.ML_ONLY,
            ml_prediction=make_ml_prediction(),
            indicator_values={"rsi_14": 42.0, "close": 100.0},
        )
    )
    orchestrator = PaperTradingOrchestrator()
    order = orchestrator.map_signal(signal, session_id="ps-orch")
    assert order.side == PaperOrderSide.BUY
    prepared = orchestrator.prepare_from_signal(
        signal,
        session_id="ps-orch-2",
        map_order=True,
    )
    assert prepared.signal_id == signal.signal_id
