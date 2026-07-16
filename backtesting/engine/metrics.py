"""Aggregate backtest performance metrics."""

from __future__ import annotations

from backtesting.contracts.summary import BacktestSummary
from backtesting.contracts.trade import (
    BacktestTradeLifecycle,
    BacktestTradeOutcome,
    BacktestTradeResult,
)
from models.decision import DecisionState


def _planned_risk_reward(trade: BacktestTradeResult) -> float | None:
    entry = trade.entry_price
    stop = trade.stop_price
    target = trade.target_price
    if trade.direction == DecisionState.BUY:
        risk = entry - stop
        reward = target - entry
    elif trade.direction == DecisionState.SELL:
        risk = stop - entry
        reward = entry - target
    else:
        return None
    if risk <= 0 or reward <= 0:
        return None
    return reward / risk


def compute_backtest_summary(
    trades: tuple[BacktestTradeResult, ...],
    *,
    candles_processed: int,
    initial_cash: float,
    equity_curve: tuple[float, ...],
) -> BacktestSummary:
    """Aggregate deterministic metrics from closed and rejected lifecycle records."""
    rejected = [trade for trade in trades if trade.lifecycle == BacktestTradeLifecycle.REJECTED]
    closed = [
        trade
        for trade in trades
        if trade.outcome
        in {BacktestTradeOutcome.WIN, BacktestTradeOutcome.LOSS, BacktestTradeOutcome.BREAKEVEN}
    ]
    wins = sum(1 for trade in closed if trade.outcome == BacktestTradeOutcome.WIN)
    losses = sum(1 for trade in closed if trade.outcome == BacktestTradeOutcome.LOSS)
    breakeven = sum(1 for trade in closed if trade.outcome == BacktestTradeOutcome.BREAKEVEN)

    net_pnl = sum(trade.net_pnl for trade in closed)
    total_fees = sum(trade.fees for trade in closed)
    gross_pnl = net_pnl + sum(trade.commission for trade in closed)

    win_rate: float | None = None
    if closed:
        win_rate = wins / len(closed)

    returns = [trade.return_pct for trade in closed if trade.return_pct is not None]
    average_return_pct: float | None = None
    if returns:
        average_return_pct = sum(returns) / len(returns)

    gross_wins = sum(trade.net_pnl for trade in closed if trade.net_pnl > 0)
    gross_losses = abs(sum(trade.net_pnl for trade in closed if trade.net_pnl < 0))
    profit_factor: float | None = None
    if gross_losses > 0:
        profit_factor = gross_wins / gross_losses

    rr_values = [value for trade in closed if (value := _planned_risk_reward(trade)) is not None]
    average_risk_reward: float | None = None
    if rr_values:
        average_risk_reward = sum(rr_values) / len(rr_values)

    max_drawdown: float | None = None
    if equity_curve:
        peak = equity_curve[0]
        max_dd = 0.0
        for equity in equity_curve:
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
        max_drawdown = max_dd

    final_equity = equity_curve[-1] if equity_curve else initial_cash

    return BacktestSummary(
        total_trades=len(closed),
        rejected_trades=len(rejected),
        wins=wins,
        losses=losses,
        breakeven_trades=breakeven,
        win_rate=win_rate,
        gross_pnl=gross_pnl,
        net_pnl=net_pnl,
        total_fees=total_fees,
        average_return_pct=average_return_pct,
        profit_factor=profit_factor,
        max_drawdown=max_drawdown,
        average_risk_reward=average_risk_reward,
        candles_processed=candles_processed,
        final_equity=final_equity,
    )
