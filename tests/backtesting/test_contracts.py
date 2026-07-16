"""Backtest contract and adapter unit tests."""

from __future__ import annotations

import pytest

from backtesting.contracts.config import BacktestConfig
from backtesting.contracts.request import BacktestRequest
from backtesting.engine.position import OpenBacktestPosition
from backtesting.engine.pricing import compute_commission, compute_fill_price
from backtesting.engine.risk_evaluator import (
    build_backtest_risk_verdict,
    evaluate_backtest_risk,
)
from backtesting.engine.runner import _check_exit, _stop_target_prices
from backtesting.exceptions import BacktestConfigurationError
from models.decision import DecisionState
from models.risk import RiskVerdictStatus
from signal_engine import SignalAssembler
from tests.backtesting.fixtures import make_candles
from tests.signal_helpers import make_assembly_request


@pytest.mark.unit
def test_backtest_request_rejects_symbol_mismatch() -> None:
    candles = make_candles([100.0, 101.0], symbol_id="ETH/USDT")
    with pytest.raises(ValueError, match="symbol_id"):
        BacktestRequest(
            symbol_id="BTC/USDT",
            market_id="crypto:binance",
            timeframe="1h",
            candles=candles,
        )


@pytest.mark.unit
def test_pricing_and_commission_for_buy_and_sell() -> None:
    buy_price, spread, slip = compute_fill_price(
        100.0,
        DecisionState.BUY,
        spread_bps=2.0,
        slippage_bps=5.0,
    )
    sell_price, _, _ = compute_fill_price(
        100.0,
        DecisionState.SELL,
        spread_bps=2.0,
        slippage_bps=5.0,
    )
    assert buy_price > 100.0
    assert sell_price < 100.0
    assert spread > 0
    assert slip > 0
    assert compute_commission(buy_price * 2, 10.0) > 0


@pytest.mark.unit
def test_risk_evaluator_fail_closed_and_approved() -> None:
    signal = SignalAssembler().assemble(make_assembly_request(decision=DecisionState.BUY))
    rejected = build_backtest_risk_verdict(
        signal,
        status=RiskVerdictStatus.REJECTED,
        rejection_reason="exposure_limit",
    )
    not_approved, reasons = evaluate_backtest_risk(signal, verdict=rejected)
    assert not_approved is False
    assert reasons == ("exposure_limit",)

    approved = build_backtest_risk_verdict(signal)
    ok, _ = evaluate_backtest_risk(signal, verdict=approved)
    assert ok is True

    missing, reasons = evaluate_backtest_risk(signal, verdict=None, require_approval=True)
    assert missing is False
    assert reasons == ("missing_risk_verdict",)

    with pytest.raises(ValueError, match="rejection_reason"):
        build_backtest_risk_verdict(signal, status=RiskVerdictStatus.REJECTED)


@pytest.mark.unit
def test_stop_target_and_exit_detection() -> None:
    stop, target = _stop_target_prices(
        direction=DecisionState.BUY,
        entry_price=100.0,
        stop_loss_pct=0.02,
        take_profit_pct=0.04,
    )
    assert stop == pytest.approx(98.0)
    assert target == pytest.approx(104.0)

    position = OpenBacktestPosition(
        trade_id="t-1",
        signal_id="sig-1",
        direction=DecisionState.BUY,
        entry_price=100.0,
        stop_price=98.0,
        target_price=104.0,
        quantity=1.0,
        commission=0.1,
        slippage=0.1,
        fees=0.2,
        invalidation_price=99.0,
        risk_verdict_status=RiskVerdictStatus.APPROVED,
        entry_at=make_candles([100.0])[0].timestamp,
        entry_bar_index=0,
    )
    stop_candle = make_candles([100.0, 97.0])[1]
    stop_candle = stop_candle.model_copy(update={"low": 97.0, "high": 101.0})
    exit_decision = _check_exit(position, stop_candle)
    assert exit_decision is not None
    assert exit_decision.reason == "stop_loss"

    with pytest.raises(BacktestConfigurationError):
        _stop_target_prices(
            direction=DecisionState.HOLD,
            entry_price=100.0,
            stop_loss_pct=0.02,
            take_profit_pct=0.04,
        )


@pytest.mark.unit
def test_config_custom_run_id() -> None:
    candles = make_candles([100.0] * 40)
    request = BacktestRequest(
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        candles=candles,
        run_id="custom-run-001",
    )
    assert request.run_id == "custom-run-001"
    assert request.config.min_bars_for_signal == BacktestConfig().min_bars_for_signal
