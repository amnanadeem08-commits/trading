"""Backtest reporting acceptance tests (BACKTEST-003)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from backtesting import (
    BacktestConfig,
    BacktestRequest,
    BacktestRunner,
    BacktestTradeLifecycle,
    BacktestTradeOutcome,
    build_backtest_report,
    deserialize_backtest_report,
    format_backtest_summary_text,
    serialize_backtest_report,
)
from backtesting.engine.metrics import compute_backtest_summary
from market_data.models.candle import Candle
from models.decision import DecisionState
from signal_engine import SignalAssembler
from tests.backtesting.fixtures import FIXTURE_CLOSES, FIXTURE_OVERSOLD_CLOSES, make_candles
from tests.signal_helpers import make_assembly_request


def _run_with_signal_at(
    *,
    candles: tuple[Candle, ...],
    bar_index: int,
    decision: DecisionState,
    config: BacktestConfig,
) -> tuple:
    injected = SignalAssembler().assemble(
        make_assembly_request(decision=decision, signal_id=f"sig-bt-{bar_index}")
    )

    def _signal_once(
        window: tuple[Candle, ...],
        *,
        market_id: str,
        bar_index: int,
        strategy_version: str,
        config_hash: str,
    ):
        if bar_index == target_index:
            return injected
        return None

    target_index = bar_index
    with patch("backtesting.engine.runner.evaluate_signal_at_bar", side_effect=_signal_once):
        request = BacktestRequest(
            symbol_id="BTC/USDT",
            market_id="crypto:binance",
            timeframe="1h",
            candles=candles,
            config=config,
        )
        result = BacktestRunner().run(request)
        report = build_backtest_report(result, request=request)
    return result, report


def _candles_for_take_profit() -> tuple[Candle, ...]:
    """Series where a BUY at bar 40 hits take-profit on the next bar."""
    base = datetime(2026, 1, 1, tzinfo=UTC)
    candles: list[Candle] = []
    for index in range(40):
        close = 100.0
        candles.append(
            Candle(
                record_id=f"bt-win-{index}",
                dataset_id="crypto:binance",
                symbol_id="BTC/USDT",
                timestamp=base + timedelta(hours=index),
                open=close,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=100.0,
                sequence=index,
            )
        )
    entry_close = 100.0
    candles.append(
        Candle(
            record_id="bt-win-40",
            dataset_id="crypto:binance",
            symbol_id="BTC/USDT",
            timestamp=base + timedelta(hours=40),
            open=entry_close,
            high=entry_close + 1.0,
            low=entry_close - 1.0,
            close=entry_close,
            volume=100.0,
            sequence=40,
        )
    )
    candles.append(
        Candle(
            record_id="bt-win-41",
            dataset_id="crypto:binance",
            symbol_id="BTC/USDT",
            timestamp=base + timedelta(hours=41),
            open=104.0,
            high=106.0,
            low=99.5,
            close=105.0,
            volume=100.0,
            sequence=41,
        )
    )
    for index in range(42, 55):
        candles.append(
            Candle(
                record_id=f"bt-win-{index}",
                dataset_id="crypto:binance",
                symbol_id="BTC/USDT",
                timestamp=base + timedelta(hours=index),
                open=105.0,
                high=106.0,
                low=104.0,
                close=105.0,
                volume=100.0,
                sequence=index,
            )
        )
    return tuple(candles)


def _candles_for_stop_loss() -> tuple[Candle, ...]:
    """Series where entry is followed by a sharp drop to stop."""
    base = datetime(2026, 1, 1, tzinfo=UTC)
    candles: list[Candle] = []
    for index in range(40):
        close = 100.0
        candles.append(
            Candle(
                record_id=f"bt-loss-{index}",
                dataset_id="crypto:binance",
                symbol_id="BTC/USDT",
                timestamp=base + timedelta(hours=index),
                open=close,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=100.0,
                sequence=index,
            )
        )
    entry_close = 100.0
    candles.append(
        Candle(
            record_id="bt-loss-40",
            dataset_id="crypto:binance",
            symbol_id="BTC/USDT",
            timestamp=base + timedelta(hours=40),
            open=entry_close,
            high=entry_close + 1.0,
            low=entry_close - 1.0,
            close=entry_close,
            volume=100.0,
            sequence=40,
        )
    )
    candles.append(
        Candle(
            record_id="bt-loss-41",
            dataset_id="crypto:binance",
            symbol_id="BTC/USDT",
            timestamp=base + timedelta(hours=41),
            open=95.0,
            high=96.0,
            low=94.0,
            close=95.0,
            volume=100.0,
            sequence=41,
        )
    )
    for index in range(42, 55):
        candles.append(
            Candle(
                record_id=f"bt-loss-{index}",
                dataset_id="crypto:binance",
                symbol_id="BTC/USDT",
                timestamp=base + timedelta(hours=index),
                open=95.0,
                high=96.0,
                low=94.0,
                close=95.0,
                volume=100.0,
                sequence=index,
            )
        )
    return tuple(candles)


@pytest.mark.unit
def test_report_profitable_fixture() -> None:
    candles = _candles_for_take_profit()
    config = BacktestConfig(
        min_bars_for_signal=35,
        seed="accept-profit",
        stop_loss_pct=0.02,
        take_profit_pct=0.04,
        slippage_bps=0.0,
        commission_bps=0.0,
        spread_bps=0.0,
    )
    _, report = _run_with_signal_at(
        candles=candles,
        bar_index=40,
        decision=DecisionState.BUY,
        config=config,
    )

    assert report.summary.total_trades >= 1
    assert report.summary.net_pnl > 0
    assert report.summary.wins >= 1
    assert len(report.trades) == report.summary.total_trades
    assert len(report.rejected_trades) == report.summary.rejected_trades
    assert report.run_id.startswith("btrun-")


@pytest.mark.unit
def test_report_losing_fixture() -> None:
    candles = _candles_for_stop_loss()
    config = BacktestConfig(
        min_bars_for_signal=35,
        seed="accept-loss",
        stop_loss_pct=0.02,
        take_profit_pct=0.50,
        slippage_bps=0.0,
        commission_bps=0.0,
        spread_bps=0.0,
    )
    _, report = _run_with_signal_at(
        candles=candles,
        bar_index=40,
        decision=DecisionState.BUY,
        config=config,
    )

    assert report.summary.total_trades >= 1
    assert report.summary.net_pnl < 0
    assert report.summary.losses >= 1
    closed = [
        trade for trade in report.trades if trade.lifecycle == BacktestTradeLifecycle.STOP_LOSS
    ]
    assert closed


@pytest.mark.unit
def test_report_no_trade_fixture() -> None:
    candles = make_candles(list(FIXTURE_CLOSES))

    def _no_signals(*args, **kwargs):
        return None

    with patch("backtesting.engine.runner.evaluate_signal_at_bar", side_effect=_no_signals):
        request = BacktestRequest(
            symbol_id="BTC/USDT",
            market_id="crypto:binance",
            timeframe="1h",
            candles=candles,
            config=BacktestConfig(min_bars_for_signal=35, seed="accept-no-trade"),
        )
        result = BacktestRunner().run(request)
        report = build_backtest_report(result, request=request)

    assert report.summary.total_trades == 0
    assert report.summary.rejected_trades == 0
    assert report.trades == ()
    assert report.rejected_trades == ()
    assert report.summary.final_equity == pytest.approx(request.config.initial_cash)


@pytest.mark.unit
def test_report_risk_rejected_fixture() -> None:
    candles = make_candles(list(FIXTURE_OVERSOLD_CLOSES))
    reject_index = 40
    injected = SignalAssembler().assemble(
        make_assembly_request(decision=DecisionState.BUY, signal_id=f"sig-bt-{reject_index}")
    )

    def _signal_at_reject(
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
        "backtesting.engine.runner.evaluate_signal_at_bar", side_effect=_signal_at_reject
    ):
        request = BacktestRequest(
            symbol_id="BTC/USDT",
            market_id="crypto:binance",
            timeframe="1h",
            candles=candles,
            config=BacktestConfig(
                min_bars_for_signal=35,
                seed="accept-reject",
                force_reject_bar_indices=frozenset({reject_index}),
            ),
        )
        result = BacktestRunner().run(request)
        report = build_backtest_report(result, request=request)

    assert report.summary.rejected_trades >= 1
    assert report.rejected_trades
    assert all(
        trade.lifecycle == BacktestTradeLifecycle.REJECTED for trade in report.rejected_trades
    )
    assert all(
        trade.outcome == BacktestTradeOutcome.REJECTED for trade in report.rejected_trades
    )
    assert report.warnings
    assert report.summary.total_trades == len(report.trades)


@pytest.mark.unit
def test_report_deterministic_repeated_run() -> None:
    candles = make_candles(list(FIXTURE_CLOSES))
    request = BacktestRequest(
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        candles=candles,
        config=BacktestConfig(min_bars_for_signal=35, seed="accept-determinism"),
    )
    first = build_backtest_report(BacktestRunner().run(request), request=request)
    second = build_backtest_report(BacktestRunner().run(request), request=request)

    assert first.model_dump() == second.model_dump()
    assert serialize_backtest_report(first) == serialize_backtest_report(second)


@pytest.mark.unit
def test_report_serialization_round_trip() -> None:
    candles = make_candles(list(FIXTURE_CLOSES))
    request = BacktestRequest(
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        candles=candles,
        config=BacktestConfig(min_bars_for_signal=35, seed="accept-serialize"),
    )
    original = build_backtest_report(BacktestRunner().run(request), request=request)
    payload = serialize_backtest_report(original)
    restored = deserialize_backtest_report(payload)

    assert restored == original
    assert '"schema_version":"backtest-report-v1"' in payload
    assert original.run_id in payload


@pytest.mark.unit
def test_report_metrics_consistency_with_engine() -> None:
    candles = make_candles(list(FIXTURE_OVERSOLD_CLOSES))
    request = BacktestRequest(
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        candles=candles,
        config=BacktestConfig(min_bars_for_signal=35, seed="accept-metrics"),
    )
    result = BacktestRunner().run(request)
    report = build_backtest_report(result, request=request)

    assert len(report.trades) + len(report.rejected_trades) == len(result.trades)

    equity_curve = [request.config.initial_cash]
    equity = request.config.initial_cash
    for trade in result.trades:
        if trade.lifecycle != BacktestTradeLifecycle.REJECTED:
            equity += trade.net_pnl
            equity_curve.append(equity)

    recomputed = compute_backtest_summary(
        result.trades,
        candles_processed=report.candles_processed,
        initial_cash=request.config.initial_cash,
        equity_curve=tuple(equity_curve),
    )
    assert report.summary == recomputed


@pytest.mark.unit
def test_report_config_references_and_human_summary() -> None:
    candles = make_candles(list(FIXTURE_CLOSES))
    config = BacktestConfig(min_bars_for_signal=35, seed="accept-text")
    request = BacktestRequest(
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        candles=candles,
        config=config,
    )
    report = build_backtest_report(BacktestRunner().run(request), request=request)
    text = format_backtest_summary_text(report)

    assert report.strategy_config.strategy_version == request.strategy_version
    assert report.strategy_config.seed == config.seed
    assert report.risk_config.stop_loss_pct == config.stop_loss_pct
    assert report.simulation_config.initial_cash == config.initial_cash
    assert report.run_id in text
    assert report.symbol_id in text
    assert "Disclaimer" in text
    assert report.technical_notes
