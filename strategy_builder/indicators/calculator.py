"""Pure approved-indicator calculations over a bounded candle window."""

from __future__ import annotations

import math
from collections.abc import Sequence

from market_data.models.candle import Candle
from signal_engine.indicators.technical import (
    IndicatorComputationError,
    compute_atr,
    compute_macd,
    compute_rsi,
    compute_sma,
)
from strategy_builder.contracts import CandleField, IndicatorKind, IndicatorSpec
from strategy_builder.exceptions import IndicatorEvaluationError


def _values(candles: Sequence[Candle], field: CandleField) -> tuple[float, ...]:
    values = tuple(float(getattr(candle, field.value)) for candle in candles)
    if not values or any(not math.isfinite(value) for value in values):
        raise IndicatorEvaluationError(f"{field.value} values must be finite and non-empty")
    return values


def _ema(values: Sequence[float], period: int) -> float:
    if len(values) < period:
        raise IndicatorEvaluationError(f"Need at least {period} values for EMA, got {len(values)}")
    seed = sum(values[:period]) / float(period)
    alpha = 2.0 / (period + 1.0)
    result = seed
    for value in values[period:]:
        result = alpha * value + (1.0 - alpha) * result
    return result


def _bollinger(
    values: Sequence[float], period: int, deviations: float
) -> tuple[float, float, float]:
    if len(values) < period:
        raise IndicatorEvaluationError(
            f"Need at least {period} values for Bollinger Bands, got {len(values)}"
        )
    window = tuple(values[-period:])
    middle = sum(window) / float(period)
    variance = sum((value - middle) ** 2 for value in window) / float(period)
    distance = math.sqrt(variance) * deviations
    return middle - distance, middle, middle + distance


def evaluate_indicator(spec: IndicatorSpec, candles: Sequence[Candle]) -> float:
    """Evaluate one approved indicator at the last supplied candle."""
    if not candles:
        raise IndicatorEvaluationError("indicator evaluation requires at least one candle")
    source = _values(candles, spec.source)
    try:
        if spec.kind in {
            IndicatorKind.OPEN,
            IndicatorKind.HIGH,
            IndicatorKind.LOW,
            IndicatorKind.CLOSE,
            IndicatorKind.VOLUME,
        }:
            return source[-1]
        if spec.kind == IndicatorKind.SMA:
            return compute_sma(source, _required(spec.period, "period"))
        if spec.kind == IndicatorKind.EMA:
            return _ema(source, _required(spec.period, "period"))
        if spec.kind == IndicatorKind.RSI:
            return compute_rsi(source, _required(spec.period, "period"))
        if spec.kind in {IndicatorKind.MACD, IndicatorKind.MACD_SIGNAL}:
            result = compute_macd(
                source,
                fast=_required(spec.fast_period, "fast_period"),
                slow=_required(spec.slow_period, "slow_period"),
                signal=_required(spec.signal_period, "signal_period"),
            )
            return result.macd if spec.kind == IndicatorKind.MACD else result.signal
        if spec.kind in {
            IndicatorKind.BOLLINGER_LOWER,
            IndicatorKind.BOLLINGER_MIDDLE,
            IndicatorKind.BOLLINGER_UPPER,
        }:
            lower, middle, upper = _bollinger(
                source,
                _required(spec.period, "period"),
                _required_float(spec.standard_deviations, "standard_deviations"),
            )
            return {
                IndicatorKind.BOLLINGER_LOWER: lower,
                IndicatorKind.BOLLINGER_MIDDLE: middle,
                IndicatorKind.BOLLINGER_UPPER: upper,
            }[spec.kind]
        if spec.kind == IndicatorKind.ATR:
            return compute_atr(
                _values(candles, CandleField.HIGH),
                _values(candles, CandleField.LOW),
                _values(candles, CandleField.CLOSE),
                _required(spec.period, "period"),
            )
        if spec.kind == IndicatorKind.VOLUME_MOVING_AVERAGE:
            return compute_sma(source, _required(spec.period, "period"))
    except IndicatorComputationError as error:
        raise IndicatorEvaluationError(str(error)) from error
    raise IndicatorEvaluationError(f"Unsupported indicator kind: {spec.kind}")


def evaluate_indicators(
    specs: Sequence[IndicatorSpec],
    candles: Sequence[Candle],
) -> dict[str, float]:
    """Evaluate declared indicators in stable declaration order."""
    return {spec.indicator_id: evaluate_indicator(spec, candles) for spec in specs}


def _required(value: int | None, name: str) -> int:
    if value is None:
        raise IndicatorEvaluationError(f"Missing indicator parameter: {name}")
    return value


def _required_float(value: float | None, name: str) -> float:
    if value is None:
        raise IndicatorEvaluationError(f"Missing indicator parameter: {name}")
    return value
