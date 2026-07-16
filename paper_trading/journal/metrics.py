"""Deterministic performance metrics derived from journal + PnL ledger (PAPER-007)."""

from __future__ import annotations

from models.decision import DecisionState
from paper_trading.contracts.journal import (
    PaperJournalEntry,
    PaperJournalTradeState,
    PaperPerformanceMetrics,
)
from paper_trading.contracts.ledger import PnLLedgerEntry


def _price_return_pct(entry: PaperJournalEntry) -> float | None:
    if entry.entry_price is None or entry.exit_price is None:
        return None
    if entry.entry_price <= 0:
        return None
    if entry.direction == DecisionState.BUY:
        return (entry.exit_price - entry.entry_price) / entry.entry_price * 100.0
    if entry.direction == DecisionState.SELL:
        return (entry.entry_price - entry.exit_price) / entry.entry_price * 100.0
    return None


def _planned_risk_reward(entry: PaperJournalEntry) -> float | None:
    if entry.entry_price is None or entry.stop_price is None or entry.target_price is None:
        return None
    entry_px = entry.entry_price
    stop = entry.stop_price
    target = entry.target_price
    if entry.direction == DecisionState.BUY:
        risk = entry_px - stop
        reward = target - entry_px
    elif entry.direction == DecisionState.SELL:
        risk = stop - entry_px
        reward = entry_px - target
    else:
        return None
    if risk <= 0 or reward <= 0:
        return None
    return reward / risk


def _signal_direction_correct(entry: PaperJournalEntry) -> bool | None:
    if entry.trade_state != PaperJournalTradeState.CLOSED:
        return None
    if entry.realized_pnl > 0:
        return True
    if entry.realized_pnl < 0:
        return False
    return None


def compute_performance_metrics(
    entries: tuple[PaperJournalEntry, ...],
    *,
    pnl_entries: tuple[PnLLedgerEntry, ...] = (),
) -> PaperPerformanceMetrics:
    """Aggregate deterministic paper-trading performance metrics from journal rows."""
    filled = [
        e
        for e in entries
        if e.trade_state in {PaperJournalTradeState.OPEN, PaperJournalTradeState.CLOSED}
    ]
    closed_rows = [e for e in entries if e.trade_state == PaperJournalTradeState.CLOSED]
    closed_position_ids = {e.position_id for e in closed_rows if e.position_id is not None}
    open_trades = sum(
        1
        for e in entries
        if e.trade_state == PaperJournalTradeState.OPEN
        and e.position_id is not None
        and e.position_id not in closed_position_ids
    )
    closed_trades = len(closed_rows)
    rejected = sum(1 for e in entries if e.trade_state == PaperJournalTradeState.REJECTED)
    cancelled = sum(1 for e in entries if e.trade_state == PaperJournalTradeState.CANCELLED)

    wins = sum(1 for e in closed_rows if e.realized_pnl > 0)
    losses = sum(1 for e in closed_rows if e.realized_pnl < 0)
    breakeven = sum(1 for e in closed_rows if e.realized_pnl == 0)

    net_pnl = sum(e.realized_pnl for e in closed_rows)
    closed_fees = sum(e.fees for e in closed_rows)
    gross_pnl = net_pnl + closed_fees
    total_fees = sum(e.fees for e in filled)

    win_rate: float | None = None
    if closed_trades > 0:
        win_rate = wins / closed_trades

    returns = [r for e in closed_rows if (r := _price_return_pct(e)) is not None]
    average_return_pct: float | None = None
    if returns:
        average_return_pct = sum(returns) / len(returns)

    rr_values = [r for e in filled if (r := _planned_risk_reward(e)) is not None]
    average_risk_reward: float | None = None
    if rr_values:
        average_risk_reward = sum(rr_values) / len(rr_values)

    max_drawdown: float | None = None
    if pnl_entries:
        max_drawdown = max(e.drawdown for e in pnl_entries)

    accuracy_samples = [_signal_direction_correct(e) for e in closed_rows]
    resolved = [a for a in accuracy_samples if a is not None]
    signal_accuracy: float | None = None
    if resolved:
        signal_accuracy = sum(1 for a in resolved if a) / len(resolved)

    return PaperPerformanceMetrics(
        total_simulated_trades=len(filled),
        open_trades=open_trades,
        closed_trades=closed_trades,
        rejected_trades=rejected,
        cancelled_trades=cancelled,
        wins=wins,
        losses=losses,
        breakeven_trades=breakeven,
        win_rate=win_rate,
        gross_pnl=gross_pnl,
        net_pnl=net_pnl,
        total_fees=total_fees,
        average_return_pct=average_return_pct,
        average_risk_reward=average_risk_reward,
        max_drawdown=max_drawdown,
        signal_accuracy=signal_accuracy,
    )
