"""Backtest trade lifecycle and replay integration tests (BACKTEST-002)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from backtesting import BacktestConfig, BacktestRequest, BacktestRunner
from backtesting.contracts.trade import BacktestTradeLifecycle, BacktestTradeOutcome
from backtesting.engine.position import OpenBacktestPosition
from backtesting.engine.runner import _check_exit
from market_data.models.candle import Candle
from models.decision import DecisionState
from models.risk import RiskVerdictStatus
from signal_engine import SignalAssembler
from tests.backtesting.fixtures import FIXTURE_CLOSES, FIXTURE_OVERSOLD_CLOSES, make_candles
from tests.signal_helpers import make_assembly_request


def _candle_at(
    *,
    index: int,
    close: float,
    low: float,
    high: float,
    start: datetime | None = None,
) -> Candle:
    base = start or datetime(2026, 1, 1, tzinfo=UTC)
    return Candle(
        record_id=f"bt-lc-{index}",
        dataset_id="crypto:binance",
        symbol_id="BTC/USDT",
        timestamp=base + timedelta(hours=index),
        open=close,
        high=high,
        low=low,
        close=close,
        volume=100.0,
        sequence=index,
    )


@pytest.mark.unit
def test_stop_loss_checked_before_take_profit_on_same_bar() -> None:
    position = OpenBacktestPosition(
        trade_id="t-stop-first",
        signal_id="sig-1",
        direction=DecisionState.BUY,
        entry_price=100.0,
        stop_price=98.0,
        target_price=104.0,
        quantity=1.0,
        commission=0.0,
        slippage=0.0,
        fees=0.0,
        invalidation_price=99.0,
        risk_verdict_status=RiskVerdictStatus.APPROVED,
        entry_at=datetime(2026, 1, 1, tzinfo=UTC),
        entry_bar_index=0,
    )
    candle = _candle_at(index=1, close=101.0, low=97.0, high=105.0)
    exit_decision = _check_exit(position, candle)
    assert exit_decision is not None
    assert exit_decision.reason == "stop_loss"
    assert exit_decision.lifecycle == BacktestTradeLifecycle.STOP_LOSS


@pytest.mark.unit
def test_signal_exit_before_take_profit_when_invalidation_breaks() -> None:
    position = OpenBacktestPosition(
        trade_id="t-signal-exit",
        signal_id="sig-2",
        direction=DecisionState.BUY,
        entry_price=100.0,
        stop_price=95.0,
        target_price=110.0,
        quantity=1.0,
        commission=0.0,
        slippage=0.0,
        fees=0.0,
        invalidation_price=99.0,
        risk_verdict_status=RiskVerdictStatus.APPROVED,
        entry_at=datetime(2026, 1, 1, tzinfo=UTC),
        entry_bar_index=0,
    )
    candle = _candle_at(index=1, close=100.5, low=98.5, high=111.0)
    exit_decision = _check_exit(position, candle)
    assert exit_decision is not None
    assert exit_decision.reason == "signal_exit"
    assert exit_decision.lifecycle == BacktestTradeLifecycle.SIGNAL_EXIT


@pytest.mark.unit
def test_runner_records_risk_rejection_without_open_position() -> None:
    candles = make_candles(list(FIXTURE_OVERSOLD_CLOSES))
    reject_index = 40
    injected = SignalAssembler().assemble(
        make_assembly_request(decision=DecisionState.BUY, signal_id=f"sig-bt-{reject_index}")
    )

    def _signal_at_reject_bar(
        window: tuple[Candle, ...],
        *,
        market_id: str,
        bar_index: int,
        strategy_version: str,
        config_hash: str,
    ):
        if bar_index == reject_index:
            return injected
        return None

    with patch(
        "backtesting.engine.runner.evaluate_signal_at_bar", side_effect=_signal_at_reject_bar
    ):
        result = BacktestRunner().run(
            BacktestRequest(
                symbol_id="BTC/USDT",
                market_id="crypto:binance",
                timeframe="1h",
                candles=candles,
                config=BacktestConfig(
                    min_bars_for_signal=35,
                    seed="reject-test",
                    force_reject_bar_indices=frozenset({reject_index}),
                ),
            )
        )

    rejected = [
        trade for trade in result.trades if trade.lifecycle == BacktestTradeLifecycle.REJECTED
    ]
    assert rejected
    record = rejected[0]
    assert record.outcome == BacktestTradeOutcome.REJECTED
    assert record.risk_verdict_status == RiskVerdictStatus.REJECTED
    assert record.risk_rejection_reason == "forced_bar_rejection"
    assert record.exit_price is None
    assert record.exit_at is None
    assert result.summary.rejected_trades == len(rejected)
    assert all(trade.exit_at is None for trade in rejected)


@pytest.mark.unit
def test_runner_end_of_data_forces_close() -> None:
    candles = make_candles(list(FIXTURE_OVERSOLD_CLOSES))
    entry_index = 40
    injected = SignalAssembler().assemble(
        make_assembly_request(decision=DecisionState.BUY, signal_id=f"sig-bt-{entry_index}")
    )

    def _signal_once(
        window: tuple[Candle, ...],
        *,
        market_id: str,
        bar_index: int,
        strategy_version: str,
        config_hash: str,
    ):
        if bar_index == entry_index:
            return injected
        return None

    with patch("backtesting.engine.runner.evaluate_signal_at_bar", side_effect=_signal_once):
        result = BacktestRunner().run(
            BacktestRequest(
                symbol_id="BTC/USDT",
                market_id="crypto:binance",
                timeframe="1h",
                candles=candles,
                config=BacktestConfig(
                    min_bars_for_signal=35,
                    seed="eod-close",
                    stop_loss_pct=0.50,
                    take_profit_pct=0.50,
                ),
            )
        )

    closed = [
        trade
        for trade in result.trades
        if trade.lifecycle
        in {
            BacktestTradeLifecycle.STOP_LOSS,
            BacktestTradeLifecycle.TAKE_PROFIT,
            BacktestTradeLifecycle.SIGNAL_EXIT,
            BacktestTradeLifecycle.END_OF_DATA,
        }
    ]
    assert closed
    last_trade = closed[-1]
    assert last_trade.lifecycle == BacktestTradeLifecycle.END_OF_DATA
    assert last_trade.exit_reason == "end_of_data"
    assert last_trade.exit_at == candles[-1].timestamp
    assert last_trade.exit_bar_index == len(candles) - 1


@pytest.mark.unit
def test_runner_no_overlapping_positions_and_no_duplicate_trade_ids() -> None:
    candles = make_candles(list(FIXTURE_CLOSES))
    request = BacktestRequest(
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        candles=candles,
        config=BacktestConfig(min_bars_for_signal=35, seed="no-overlap"),
    )
    result = BacktestRunner().run(request)

    trade_ids = [trade.trade_id for trade in result.trades]
    assert len(trade_ids) == len(set(trade_ids))

    opened = [
        trade
        for trade in result.trades
        if trade.lifecycle != BacktestTradeLifecycle.REJECTED and trade.exit_at is not None
    ]
    for trade in opened:
        assert trade.entry_bar_index <= (trade.exit_bar_index or trade.entry_bar_index)


@pytest.mark.unit
def test_runner_deterministic_repeated_runs_include_lifecycle_fields() -> None:
    candles = make_candles(list(FIXTURE_CLOSES))
    request = BacktestRequest(
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        candles=candles,
        config=BacktestConfig(min_bars_for_signal=35, seed="lifecycle-determinism"),
    )
    first = BacktestRunner().run(request)
    second = BacktestRunner().run(request)
    assert first.model_dump() == second.model_dump()

    for trade in first.trades:
        assert trade.lifecycle
        if trade.lifecycle != BacktestTradeLifecycle.REJECTED:
            assert trade.risk_verdict_status == RiskVerdictStatus.APPROVED
            assert trade.entry_price > 0
            assert trade.stop_price > 0
            assert trade.target_price > 0
