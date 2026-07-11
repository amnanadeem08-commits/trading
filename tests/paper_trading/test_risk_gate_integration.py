"""Integration: paper orchestration + risk gate + mapping (PAPER-003)."""

from __future__ import annotations

import pytest

from config.settings import get_settings, reset_settings
from models.decision import DecisionState
from models.risk import RiskVerdictStatus
from paper_trading import (
    PaperLiveTradingDisabledError,
    PaperRiskRejectedError,
    PaperSessionStatus,
    PaperTradingOrchestrator,
    build_paper_risk_verdict,
    paper_order_from_signal,
    reset_paper_registry,
)
from risk.engine.risk_result import RiskResult
from risk.engine.risk_state import RiskState
from signal_engine import SignalAssembler
from tests.signal_helpers import make_assembly_request


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_paper_registry()
    reset_settings()
    yield
    reset_paper_registry()
    reset_settings()


def _priced_buy():
    return SignalAssembler().assemble(
        make_assembly_request(
            signal_id="sig-int-buy",
            decision=DecisionState.BUY,
            confidence=0.65,
            indicator_values={"rsi_14": 42.0, "close": 100.0},
        )
    )


@pytest.mark.integration
def test_map_then_risk_approve_then_authorize_fill() -> None:
    signal = _priced_buy()
    order = paper_order_from_signal(signal, session_id="ps-int-1")
    assert order.adapter_payload["live_broker"] is False

    orchestrator = PaperTradingOrchestrator()
    verdict = build_paper_risk_verdict(signal, status=RiskVerdictStatus.APPROVED)
    gate = orchestrator.authorize_fill(signal, verdict=verdict)
    assert gate.passed is True

    session = orchestrator.prepare_with_risk_gate(
        signal, session_id="ps-int-1", verdict=verdict, map_order=True
    )
    assert session.status == PaperSessionStatus.RISK_APPROVED


@pytest.mark.integration
def test_risk_reject_blocks_fill_end_to_end() -> None:
    signal = _priced_buy()
    orchestrator = PaperTradingOrchestrator()
    verdict = build_paper_risk_verdict(
        signal,
        status=RiskVerdictStatus.REJECTED,
        rejection_reason="position_limit",
    )
    with pytest.raises(PaperRiskRejectedError) as exc:
        orchestrator.authorize_fill(signal, verdict=verdict)
    assert "position_limit" in exc.value.reasons

    session = orchestrator.prepare_with_risk_gate(signal, session_id="ps-int-rej", verdict=verdict)
    assert session.status == PaperSessionStatus.RISK_REJECTED
    assert "position_limit" in session.risk_gate_reasons


@pytest.mark.integration
def test_foundation_risk_result_reject_blocks_fill() -> None:
    signal = _priced_buy()
    orchestrator = PaperTradingOrchestrator()
    risk_result = RiskResult(
        risk_id="rr-int",
        engine_id="paper-test-engine",
        policy_id="paper-test-policy",
        state=RiskState.REJECTED,
        metadata={"reason": "validation_failed"},
        validation={"passed": False, "failed_rules": ["min_confidence"]},
    )
    with pytest.raises(PaperRiskRejectedError) as exc:
        orchestrator.authorize_fill(signal, risk_result=risk_result)
    assert any("validation" in r or "min_confidence" in r for r in exc.value.reasons)


@pytest.mark.integration
def test_settings_require_risk_gate_before_fill() -> None:
    settings = get_settings()
    assert settings.paper_trading.risk_gate_required_before_fill is True


@pytest.mark.integration
def test_live_trading_still_blocks_risk_gate_path() -> None:
    settings = get_settings()
    live = settings.model_copy(
        update={
            "feature_flags": settings.feature_flags.model_copy(
                update={"live_trading_enabled": True}
            )
        }
    )
    orchestrator = PaperTradingOrchestrator(settings=live)
    signal = _priced_buy()
    with pytest.raises(PaperLiveTradingDisabledError):
        orchestrator.authorize_fill(
            signal,
            verdict=build_paper_risk_verdict(signal, status=RiskVerdictStatus.APPROVED),
        )
