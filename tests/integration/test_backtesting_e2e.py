"""E2E integration: candles → signal → risk → backtest trades → summary."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from backtesting import BacktestConfig, BacktestRequest, BacktestRunner, ChronologicalCandleFeed
from backtesting.exceptions import LookAheadError
from config.settings import get_settings, reset_settings
from tests.backtesting.fixtures import FIXTURE_CLOSES, FIXTURE_OVERSOLD_CLOSES, make_candles

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def _reset_globals() -> Generator[None]:
    reset_settings()
    yield
    reset_settings()


@pytest.mark.integration
def test_backtesting_e2e_replay_and_summary() -> None:
    settings = get_settings()
    assert settings.feature_flags.live_trading_enabled is False

    candles = make_candles(list(FIXTURE_OVERSOLD_CLOSES))
    result = BacktestRunner().run(
        BacktestRequest(
            symbol_id="BTC/USDT",
            market_id="crypto:binance",
            timeframe="1h",
            candles=candles,
            config=BacktestConfig(min_bars_for_signal=35, seed="e2e-1"),
        )
    )

    assert result.run_id.startswith("btrun-")
    assert result.summary.candles_processed == len(candles)
    assert result.summary.total_trades >= 0
    assert result.summary.final_equity > 0
    assert result.completed_at >= result.started_at


@pytest.mark.integration
def test_backtesting_e2e_no_future_candle_access_during_replay() -> None:
    candles = make_candles(list(FIXTURE_CLOSES))
    feed = ChronologicalCandleFeed(candles)

    for index in range(feed.total):
        feed.advance_to(index)
        window = feed.history_window()
        assert len(window) == index + 1
        with pytest.raises(LookAheadError):
            feed.peek(index + 1)


@pytest.mark.integration
def test_backtesting_e2e_deterministic_across_runs() -> None:
    candles = make_candles(list(FIXTURE_CLOSES))
    request = BacktestRequest(
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        candles=candles,
        config=BacktestConfig(min_bars_for_signal=35, seed="e2e-determinism"),
    )
    a = BacktestRunner().run(request)
    b = BacktestRunner().run(request)
    assert a.model_dump() == b.model_dump()
