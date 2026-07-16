"""Backtest metrics aggregation tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backtesting.contracts.trade import (
    BacktestTradeLifecycle,
    BacktestTradeOutcome,
    BacktestTradeResult,
)
from backtesting.engine.metrics import compute_backtest_summary
from models.decision import DecisionState
from models.risk import RiskVerdictStatus


def _trade(
    *,
    net_pnl: float,
    outcome: BacktestTradeOutcome,
    return_pct: float | None = None,
) -> BacktestTradeResult:
    ts = datetime(2026, 1, 1, tzinfo=UTC)
    return BacktestTradeResult(
        trade_id=f"t-{outcome.value}-{net_pnl}",
        run_id="run-1",
        signal_id="sig-1",
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        direction=DecisionState.BUY,
        lifecycle=BacktestTradeLifecycle.TAKE_PROFIT,
        risk_verdict_status=RiskVerdictStatus.APPROVED,
        entry_price=100.0,
        exit_price=101.0,
        stop_price=98.0,
        target_price=104.0,
        quantity=1.0,
        commission=0.5,
        slippage=0.2,
        fees=0.7,
        gross_pnl=net_pnl + 0.7,
        net_pnl=net_pnl,
        return_pct=return_pct,
        outcome=outcome,
        entry_at=ts,
        exit_at=ts,
        entry_bar_index=0,
        exit_bar_index=1,
        exit_reason="take_profit",
    )


@pytest.mark.unit
def test_compute_backtest_summary_metrics() -> None:
    trades = (
        _trade(net_pnl=10.0, outcome=BacktestTradeOutcome.WIN, return_pct=10.0),
        _trade(net_pnl=-5.0, outcome=BacktestTradeOutcome.LOSS, return_pct=-5.0),
        _trade(net_pnl=0.0, outcome=BacktestTradeOutcome.BREAKEVEN, return_pct=0.0),
    )
    summary = compute_backtest_summary(
        trades,
        candles_processed=100,
        initial_cash=100_000.0,
        equity_curve=(100_000.0, 100_010.0, 100_005.0, 100_005.0),
    )

    assert summary.total_trades == 3
    assert summary.rejected_trades == 0
    assert summary.wins == 1
    assert summary.losses == 1
    assert summary.breakeven_trades == 1
    assert summary.win_rate == pytest.approx(1 / 3)
    assert summary.net_pnl == pytest.approx(5.0)
    assert summary.profit_factor == pytest.approx(10.0 / 5.0)
    assert summary.average_return_pct == pytest.approx(5.0 / 3)
    assert summary.max_drawdown == pytest.approx(5.0)
    assert summary.average_risk_reward == pytest.approx(2.0)
    assert summary.candles_processed == 100


@pytest.mark.unit
def test_compute_backtest_summary_excludes_rejected_from_pnl() -> None:
    ts = datetime(2026, 1, 1, tzinfo=UTC)
    rejected = BacktestTradeResult(
        trade_id="t-rejected",
        run_id="run-1",
        signal_id="sig-r",
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        direction=DecisionState.BUY,
        lifecycle=BacktestTradeLifecycle.REJECTED,
        risk_verdict_status=RiskVerdictStatus.REJECTED,
        risk_rejection_reason="exposure_limit",
        entry_price=100.0,
        stop_price=98.0,
        target_price=104.0,
        quantity=1.0,
        outcome=BacktestTradeOutcome.REJECTED,
        entry_at=ts,
        entry_bar_index=5,
        exit_reason="risk_rejected",
    )
    closed = _trade(net_pnl=10.0, outcome=BacktestTradeOutcome.WIN, return_pct=10.0)
    summary = compute_backtest_summary(
        (rejected, closed),
        candles_processed=50,
        initial_cash=100_000.0,
        equity_curve=(100_000.0, 100_010.0),
    )
    assert summary.total_trades == 1
    assert summary.rejected_trades == 1
    assert summary.net_pnl == pytest.approx(10.0)
    assert summary.wins == 1
