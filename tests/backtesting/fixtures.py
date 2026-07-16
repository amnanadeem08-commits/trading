"""Fixed candle fixtures for backtesting tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from market_data.models.candle import Candle


def make_candles(
    closes: list[float],
    *,
    symbol_id: str = "BTC/USDT",
    dataset_id: str = "crypto:binance",
    start: datetime | None = None,
) -> tuple[Candle, ...]:
    """Build chronologically ordered candles from close prices."""
    base = start or datetime(2026, 1, 1, tzinfo=UTC)
    candles: list[Candle] = []
    for index, close in enumerate(closes):
        candles.append(
            Candle(
                record_id=f"bt-c-{index}",
                dataset_id=dataset_id,
                symbol_id=symbol_id,
                timestamp=base + timedelta(hours=index),
                open=close,
                high=close + 2.0,
                low=close - 2.0,
                close=close,
                volume=100.0,
                sequence=index,
            )
        )
    return tuple(candles)


# Trending series long enough for RSI/MACD warm-up (50 bars).
FIXTURE_CLOSES: tuple[float, ...] = tuple(100.0 + index * 0.5 for index in range(50))

# Strong downtrend then rebound to trigger oversold BUY candidate.
FIXTURE_OVERSOLD_CLOSES: tuple[float, ...] = tuple(
    120.0 - index * 1.5 for index in range(40)
) + tuple(80.0 + index * 0.2 for index in range(15))
