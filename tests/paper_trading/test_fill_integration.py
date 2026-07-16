"""Integration: signal → risk gate → fill → ledger → portfolio (PAPER-004)."""

from __future__ import annotations

import pytest

from config.settings import get_settings, reset_settings
from models.common import utc_now
from models.decision import DecisionState
from models.risk import RiskVerdictStatus
from paper_trading import (
    FillConfig,
    PaperRiskRejectedError,
    PaperSessionStatus,
    PaperTradingOrchestrator,
    SimulatedFillExecutor,
    reset_paper_registry,
    reset_pnl_ledger,
    reset_position_ledger,
)
from paper_trading.contracts.ledger import PositionStatus
from paper_trading.risk import build_paper_risk_verdict
from signal_engine import SignalAssembler
from tests.signal_helpers import make_assembly_request


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_paper_registry()
    reset_position_ledger()
    reset_pnl_ledger()
    reset_settings()
    yield
    reset_paper_registry()
    reset_position_ledger()
    reset_pnl_ledger()
    reset_settings()


def _priced_buy():
    return SignalAssembler().assemble(
        make_assembly_request(
            signal_id="sig-p4-buy",
            decision=DecisionState.BUY,
            confidence=0.65,
            indicator_values={"rsi_14": 42.0, "close": 100.0},
        )
    )


@pytest.mark.integration
def test_signal_risk_fill_position_portfolio_pnl() -> None:
    signal = _priced_buy()
    ts = utc_now()
    cfg = FillConfig(
        slippage_bps=5.0,
        commission_bps=10.0,
        spread_bps=2.0,
        initial_cash=100_000.0,
    )
    orchestrator = PaperTradingOrchestrator(
        fill_executor=SimulatedFillExecutor(config=cfg),
    )
    verdict = build_paper_risk_verdict(signal, status=RiskVerdictStatus.APPROVED)
    result = orchestrator.execute_simulated_fill(
        signal,
        session_id="ps-p4-1",
        verdict=verdict,
        fill_timestamp=ts,
        quantity=2.0,
    )
    assert result.status == PaperSessionStatus.FILLED
    assert result.fill.quantity == pytest.approx(2.0)
    assert result.fill.fill_price > 100.0
    assert result.position_entry.status == PositionStatus.OPEN
    assert result.pnl_entry.commission > 0
    assert result.portfolio.cash < 100_000.0
    assert len(result.portfolio.open_positions) == 1
    assert orchestrator.get_session("ps-p4-1").status == PaperSessionStatus.FILLED


@pytest.mark.integration
def test_risk_reject_blocks_fill_execution() -> None:
    signal = _priced_buy()
    orchestrator = PaperTradingOrchestrator()
    verdict = build_paper_risk_verdict(
        signal,
        status=RiskVerdictStatus.REJECTED,
        rejection_reason="exposure_cap",
    )
    with pytest.raises(PaperRiskRejectedError):
        orchestrator.execute_simulated_fill(signal, session_id="ps-p4-rej", verdict=verdict)


@pytest.mark.integration
def test_fill_settings_loaded_from_yaml() -> None:
    settings = get_settings()
    assert settings.paper_trading.fill_slippage_bps == 5.0
    assert settings.paper_trading.fill_commission_bps == 10.0
    assert settings.paper_trading.initial_cash == 100_000.0
