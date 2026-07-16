"""PAPER-007 deterministic performance metrics (paper_trading)."""

from __future__ import annotations

import pytest

from models.common import utc_now
from models.decision import DecisionState
from paper_trading.contracts.journal import (
    PaperJournalEntry,
    PaperJournalTradeState,
)
from paper_trading.contracts.ledger import PnLLedgerEntry
from paper_trading.contracts.paper_order import PaperOrderSide
from paper_trading.contracts.paper_request import PaperSessionStatus
from paper_trading.journal.metrics import compute_performance_metrics


def _entry(
    *,
    trade_state: PaperJournalTradeState,
    realized_pnl: float = 0.0,
    fees: float = 1.0,
    entry_price: float | None = 100.0,
    exit_price: float | None = None,
    stop_price: float | None = None,
    target_price: float | None = None,
    direction: DecisionState = DecisionState.BUY,
    position_id: str | None = "pos-1",
) -> PaperJournalEntry:
    ts = utc_now()
    return PaperJournalEntry(
        journal_id=f"j-{trade_state.value}-{realized_pnl}",
        session_id="ps-1",
        signal_id=f"sig-{trade_state.value}",
        position_id=position_id,
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        direction=direction,
        side=PaperOrderSide.BUY if direction == DecisionState.BUY else PaperOrderSide.SELL,
        trade_state=trade_state,
        lifecycle_status=trade_state.value,
        session_status=PaperSessionStatus.FILLED,
        risk_decision=direction,
        recorded_at=ts,
        entry_price=entry_price,
        exit_price=exit_price,
        fill_price=entry_price,
        stop_price=stop_price,
        target_price=target_price,
        fees=fees,
        realized_pnl=realized_pnl,
    )


@pytest.mark.unit
def test_performance_metrics_counts_and_pnl() -> None:
    entries = (
        _entry(trade_state=PaperJournalTradeState.OPEN, fees=2.0),
        _entry(
            trade_state=PaperJournalTradeState.CLOSED,
            realized_pnl=50.0,
            fees=3.0,
            entry_price=100.0,
            exit_price=110.0,
            position_id="pos-closed-win",
        ),
        _entry(
            trade_state=PaperJournalTradeState.CLOSED,
            realized_pnl=-20.0,
            fees=2.0,
            entry_price=100.0,
            exit_price=95.0,
            position_id="pos-closed-loss",
        ),
        _entry(trade_state=PaperJournalTradeState.REJECTED, entry_price=None),
        _entry(trade_state=PaperJournalTradeState.CANCELLED, entry_price=None),
    )
    pnl_rows = (
        PnLLedgerEntry(
            trade_id="t1",
            position_id="p1",
            symbol="BTC/USDT",
            market="crypto:binance",
            commission=1.0,
            slippage=0.5,
            running_equity=100_000.0,
            drawdown=100.0,
            timestamp=utc_now(),
            fill_id="f1",
        ),
        PnLLedgerEntry(
            trade_id="t2",
            position_id="p2",
            symbol="BTC/USDT",
            market="crypto:binance",
            commission=1.0,
            slippage=0.5,
            running_equity=99_900.0,
            drawdown=250.0,
            timestamp=utc_now(),
            fill_id="f2",
        ),
    )

    metrics = compute_performance_metrics(entries, pnl_entries=pnl_rows)

    assert metrics.total_simulated_trades == 3
    assert metrics.open_trades == 1
    assert metrics.closed_trades == 2
    assert metrics.rejected_trades == 1
    assert metrics.cancelled_trades == 1
    assert metrics.wins == 1
    assert metrics.losses == 1
    assert metrics.win_rate == pytest.approx(0.5)
    assert metrics.net_pnl == pytest.approx(30.0)
    assert metrics.gross_pnl == pytest.approx(35.0)
    assert metrics.total_fees == pytest.approx(7.0)
    assert metrics.max_drawdown == pytest.approx(250.0)
    assert metrics.signal_accuracy == pytest.approx(0.5)
    assert metrics.average_return_pct == pytest.approx(2.5)


@pytest.mark.unit
def test_performance_metrics_risk_reward_when_data_exists() -> None:
    entries = (
        _entry(
            trade_state=PaperJournalTradeState.OPEN,
            entry_price=100.0,
            stop_price=95.0,
            target_price=115.0,
        ),
    )
    metrics = compute_performance_metrics(entries)
    assert metrics.average_risk_reward == pytest.approx(3.0)


@pytest.mark.unit
def test_performance_metrics_empty_slice() -> None:
    metrics = compute_performance_metrics(())
    assert metrics.total_simulated_trades == 0
    assert metrics.win_rate is None
    assert metrics.max_drawdown is None
    assert metrics.signal_accuracy is None
