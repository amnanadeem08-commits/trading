"""Backtest runner unit tests."""

from __future__ import annotations

import pytest

from backtesting import BacktestConfig, BacktestRequest, BacktestRunner
from backtesting.engine.ids import resolve_run_id
from backtesting.exceptions import BacktestConfigurationError
from tests.backtesting.fixtures import FIXTURE_CLOSES, make_candles


@pytest.mark.unit
def test_deterministic_run_id_from_request() -> None:
    candles = make_candles(list(FIXTURE_CLOSES[:30]))
    request = BacktestRequest(
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        candles=candles,
        config=BacktestConfig(seed="test-seed"),
    )
    first = resolve_run_id(request)
    second = resolve_run_id(request)
    assert first == second
    assert first.startswith("btrun-")


@pytest.mark.unit
def test_runner_rejects_insufficient_candles() -> None:
    candles = make_candles([100.0, 101.0, 102.0])
    request = BacktestRequest(
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        candles=candles,
        config=BacktestConfig(min_bars_for_signal=35),
    )
    with pytest.raises(BacktestConfigurationError, match="Need at least"):
        BacktestRunner().run(request)


@pytest.mark.unit
def test_runner_produces_reproducible_results() -> None:
    candles = make_candles(list(FIXTURE_CLOSES))
    config = BacktestConfig(seed="repro-1", min_bars_for_signal=35)
    request = BacktestRequest(
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        candles=candles,
        config=config,
    )
    first = BacktestRunner().run(request)
    second = BacktestRunner().run(request)

    assert first.run_id == second.run_id
    assert first.summary == second.summary
    assert len(first.trades) == len(second.trades)
    if first.trades:
        assert first.trades[0].trade_id == second.trades[0].trade_id


@pytest.mark.unit
def test_runner_records_trade_fields() -> None:
    candles = make_candles(list(FIXTURE_CLOSES))
    result = BacktestRunner().run(
        BacktestRequest(
            symbol_id="BTC/USDT",
            market_id="crypto:binance",
            timeframe="1h",
            candles=candles,
            config=BacktestConfig(min_bars_for_signal=26, seed="fields"),
        )
    )

    assert result.summary.candles_processed == len(candles)
    assert result.deterministic is True
    for trade in result.trades:
        assert trade.entry_price > 0
        assert trade.stop_price > 0
        assert trade.target_price > 0
        assert trade.lifecycle
        assert trade.entry_at is not None
        if trade.exit_at is not None:
            assert trade.exit_at >= trade.entry_at
        assert trade.trade_id.startswith("bttrade-")
        assert trade.run_id == result.run_id
