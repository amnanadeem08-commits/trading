"""Approved indicator allowlist tests."""

from __future__ import annotations

import pytest

from strategy_builder import CandleField, IndicatorKind, IndicatorSpec
from strategy_builder.exceptions import IndicatorEvaluationError
from strategy_builder.indicators import evaluate_indicator, evaluate_indicators
from tests.strategy_builder.fixtures import candles


def test_all_approved_indicator_families_evaluate_deterministically() -> None:
    history = candles(tuple(float(value) for value in range(1, 41)))
    specs = (
        IndicatorSpec(indicator_id="open", kind=IndicatorKind.OPEN, source=CandleField.OPEN),
        IndicatorSpec(indicator_id="high", kind=IndicatorKind.HIGH, source=CandleField.HIGH),
        IndicatorSpec(indicator_id="low", kind=IndicatorKind.LOW, source=CandleField.LOW),
        IndicatorSpec(indicator_id="close", kind=IndicatorKind.CLOSE),
        IndicatorSpec(indicator_id="volume", kind=IndicatorKind.VOLUME, source=CandleField.VOLUME),
        IndicatorSpec(indicator_id="sma", kind=IndicatorKind.SMA, period=5),
        IndicatorSpec(indicator_id="ema", kind=IndicatorKind.EMA, period=5),
        IndicatorSpec(indicator_id="rsi", kind=IndicatorKind.RSI, period=5),
        IndicatorSpec(
            indicator_id="macd",
            kind=IndicatorKind.MACD,
            fast_period=3,
            slow_period=5,
            signal_period=2,
        ),
        IndicatorSpec(
            indicator_id="macd_signal",
            kind=IndicatorKind.MACD_SIGNAL,
            fast_period=3,
            slow_period=5,
            signal_period=2,
        ),
        IndicatorSpec(
            indicator_id="bb_lower",
            kind=IndicatorKind.BOLLINGER_LOWER,
            period=5,
            standard_deviations=2.0,
        ),
        IndicatorSpec(
            indicator_id="bb_middle",
            kind=IndicatorKind.BOLLINGER_MIDDLE,
            period=5,
            standard_deviations=2.0,
        ),
        IndicatorSpec(
            indicator_id="bb_upper",
            kind=IndicatorKind.BOLLINGER_UPPER,
            period=5,
            standard_deviations=2.0,
        ),
        IndicatorSpec(indicator_id="atr", kind=IndicatorKind.ATR, period=5),
        IndicatorSpec(
            indicator_id="volume_average",
            kind=IndicatorKind.VOLUME_MOVING_AVERAGE,
            source=CandleField.VOLUME,
            period=5,
        ),
    )
    first = evaluate_indicators(specs, history)
    second = evaluate_indicators(specs, history)
    assert first == second
    assert set(first) == {spec.indicator_id for spec in specs}
    assert first["close"] == 40.0
    assert first["bb_lower"] < first["bb_middle"] < first["bb_upper"]
    assert first["rsi"] == 100.0
    assert first["atr"] == 2.0


def test_indicator_history_is_not_neutrally_filled() -> None:
    spec = IndicatorSpec(indicator_id="rsi", kind=IndicatorKind.RSI, period=14)
    with pytest.raises(IndicatorEvaluationError, match="Need at least"):
        evaluate_indicator(spec, candles((1.0, 2.0, 3.0)))
