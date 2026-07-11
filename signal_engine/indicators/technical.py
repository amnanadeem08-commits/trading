"""Typed technical indicator computations (pure functions, no legacy core import)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


class IndicatorComputationError(ValueError):
    """Raised when indicator inputs are insufficient or invalid."""


def _require_closes(closes: Sequence[float], *, minimum: int) -> tuple[float, ...]:
    values = tuple(float(value) for value in closes)
    if len(values) < minimum:
        msg = f"Need at least {minimum} closes, got {len(values)}"
        raise IndicatorComputationError(msg)
    return values


def compute_sma(closes: Sequence[float], period: int) -> float:
    """Return the simple moving average of the last `period` closes."""
    if period < 1:
        raise IndicatorComputationError("period must be >= 1")
    values = _require_closes(closes, minimum=period)
    window = values[-period:]
    return sum(window) / float(period)


def _ema_series(values: tuple[float, ...], period: int) -> tuple[float, ...]:
    if period < 1:
        raise IndicatorComputationError("period must be >= 1")
    if len(values) < period:
        msg = f"Need at least {period} values for EMA, got {len(values)}"
        raise IndicatorComputationError(msg)
    alpha = 2.0 / (period + 1.0)
    seed = sum(values[:period]) / float(period)
    result: list[float] = [seed]
    for price in values[period:]:
        result.append(alpha * price + (1.0 - alpha) * result[-1])
    return tuple(result)


def compute_rsi(closes: Sequence[float], period: int = 14) -> float:
    """Return Wilder RSI for the latest close."""
    if period < 1:
        raise IndicatorComputationError("period must be >= 1")
    values = _require_closes(closes, minimum=period + 1)
    gains: list[float] = []
    losses: list[float] = []
    for index in range(1, len(values)):
        delta = values[index] - values[index - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains[:period]) / float(period)
    avg_loss = sum(losses[:period]) / float(period)
    for gain, loss in zip(gains[period:], losses[period:], strict=False):
        avg_gain = ((avg_gain * (period - 1)) + gain) / float(period)
        avg_loss = ((avg_loss * (period - 1)) + loss) / float(period)
    if avg_loss == 0.0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


@dataclass(frozen=True, slots=True)
class MACDResult:
    """Latest MACD components."""

    macd: float
    signal: float
    histogram: float


def compute_atr(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int = 14,
) -> float:
    """Return Wilder ATR for the latest bar (not a profit probability)."""
    if period < 1:
        raise IndicatorComputationError("period must be >= 1")
    high_values = tuple(float(value) for value in highs)
    low_values = tuple(float(value) for value in lows)
    close_values = _require_closes(closes, minimum=period + 1)
    if not (len(high_values) == len(low_values) == len(close_values)):
        raise IndicatorComputationError("highs, lows, and closes must have equal length")
    if len(high_values) < period + 1:
        msg = f"Need at least {period + 1} bars for ATR, got {len(high_values)}"
        raise IndicatorComputationError(msg)
    true_ranges: list[float] = []
    for index in range(1, len(close_values)):
        high = high_values[index]
        low = low_values[index]
        prev_close = close_values[index - 1]
        true_ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    atr = sum(true_ranges[:period]) / float(period)
    for true_range in true_ranges[period:]:
        atr = ((atr * (period - 1)) + true_range) / float(period)
    return atr


def compute_macd(
    closes: Sequence[float],
    *,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> MACDResult:
    """Return the latest MACD line, signal line, and histogram."""
    if fast < 1 or slow < 1 or signal < 1:
        raise IndicatorComputationError("MACD periods must be >= 1")
    if fast >= slow:
        raise IndicatorComputationError("MACD fast period must be < slow period")
    minimum = slow + signal
    values = _require_closes(closes, minimum=minimum)
    fast_ema = _ema_series(values, fast)
    slow_ema = _ema_series(values, slow)
    offset = len(fast_ema) - len(slow_ema)
    macd_line = tuple(
        fast_value - slow_value
        for fast_value, slow_value in zip(fast_ema[offset:], slow_ema, strict=True)
    )
    if len(macd_line) < signal:
        msg = f"Need at least {signal} MACD points for signal EMA, got {len(macd_line)}"
        raise IndicatorComputationError(msg)
    signal_line = _ema_series(macd_line, signal)
    macd_latest = macd_line[-1]
    signal_latest = signal_line[-1]
    return MACDResult(
        macd=macd_latest,
        signal=signal_latest,
        histogram=macd_latest - signal_latest,
    )
