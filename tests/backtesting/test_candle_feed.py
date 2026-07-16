"""Chronological candle feed tests."""

from __future__ import annotations

import pytest

from backtesting.engine.candle_feed import ChronologicalCandleFeed
from backtesting.exceptions import LookAheadError
from tests.backtesting.fixtures import make_candles


@pytest.mark.unit
def test_feed_processes_candles_in_sequence_order() -> None:
    candles = make_candles([100.0, 101.0, 102.0])
    shuffled = (candles[2], candles[0], candles[1])
    feed = ChronologicalCandleFeed(shuffled)

    seen: list[float] = []
    for index in range(feed.total):
        candle = feed.advance_to(index)
        seen.append(candle.close)

    assert seen == [100.0, 101.0, 102.0]


@pytest.mark.unit
def test_feed_blocks_future_candle_access() -> None:
    feed = ChronologicalCandleFeed(make_candles([100.0, 101.0, 102.0]))
    feed.advance_to(0)

    with pytest.raises(LookAheadError, match="Look-ahead blocked"):
        feed.peek(1)

    feed.advance_to(1)
    assert feed.peek(0).close == 100.0
    assert feed.peek(1).close == 101.0


@pytest.mark.unit
def test_feed_invalid_index_raises() -> None:
    feed = ChronologicalCandleFeed(make_candles([100.0]))
    with pytest.raises(LookAheadError, match="Invalid candle index"):
        feed.advance_to(5)


@pytest.mark.unit
def test_history_window_excludes_future_candles() -> None:
    feed = ChronologicalCandleFeed(make_candles([100.0, 101.0, 102.0, 103.0]))
    feed.advance_to(2)
    window = feed.history_window()
    assert len(window) == 3
    assert window[-1].close == 102.0
    assert feed.max_accessed_index == 2
