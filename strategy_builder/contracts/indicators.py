"""Approved indicator contracts for deterministic strategies."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from models.common import PlatformModel


class CandleField(StrEnum):
    """Candle fields available to rule operands."""

    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    VOLUME = "volume"


class IndicatorKind(StrEnum):
    """Closed initial indicator allowlist."""

    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    VOLUME = "volume"
    SMA = "sma"
    EMA = "ema"
    RSI = "rsi"
    MACD = "macd"
    MACD_SIGNAL = "macd_signal"
    BOLLINGER_UPPER = "bollinger_upper"
    BOLLINGER_MIDDLE = "bollinger_middle"
    BOLLINGER_LOWER = "bollinger_lower"
    ATR = "atr"
    VOLUME_MOVING_AVERAGE = "volume_moving_average"


_DIRECT_KINDS = {
    IndicatorKind.OPEN,
    IndicatorKind.HIGH,
    IndicatorKind.LOW,
    IndicatorKind.CLOSE,
    IndicatorKind.VOLUME,
}
_PERIOD_KINDS = {
    IndicatorKind.SMA,
    IndicatorKind.EMA,
    IndicatorKind.RSI,
    IndicatorKind.BOLLINGER_UPPER,
    IndicatorKind.BOLLINGER_MIDDLE,
    IndicatorKind.BOLLINGER_LOWER,
    IndicatorKind.ATR,
    IndicatorKind.VOLUME_MOVING_AVERAGE,
}
_MACD_KINDS = {IndicatorKind.MACD, IndicatorKind.MACD_SIGNAL}
_BOLLINGER_KINDS = {
    IndicatorKind.BOLLINGER_UPPER,
    IndicatorKind.BOLLINGER_MIDDLE,
    IndicatorKind.BOLLINGER_LOWER,
}


class IndicatorSpec(PlatformModel):
    """A named, parameterized indicator dependency."""

    indicator_id: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_-]*$")
    kind: IndicatorKind
    source: CandleField = CandleField.CLOSE
    period: int | None = Field(default=None, ge=1)
    fast_period: int | None = Field(default=None, ge=1)
    slow_period: int | None = Field(default=None, ge=2)
    signal_period: int | None = Field(default=None, ge=1)
    standard_deviations: float | None = Field(default=None, gt=0.0)

    @model_validator(mode="after")
    def validate_parameters(self) -> IndicatorSpec:
        macd_values = (self.fast_period, self.slow_period, self.signal_period)
        if self.kind in _DIRECT_KINDS:
            if any(value is not None for value in (self.period, *macd_values)):
                raise ValueError("direct candle indicators do not accept periods")
            if self.standard_deviations is not None:
                raise ValueError("direct candle indicators do not accept standard_deviations")
        elif self.kind in _PERIOD_KINDS:
            if self.period is None:
                raise ValueError(f"{self.kind.value} requires period")
            if any(value is not None for value in macd_values):
                raise ValueError(f"{self.kind.value} does not accept MACD periods")
        elif self.kind in _MACD_KINDS:
            if any(value is None for value in macd_values):
                raise ValueError("MACD indicators require fast_period, slow_period, signal_period")
            if (
                self.fast_period is not None
                and self.slow_period is not None
                and self.fast_period >= self.slow_period
            ):
                raise ValueError("MACD fast_period must be less than slow_period")
            if self.period is not None or self.standard_deviations is not None:
                raise ValueError("MACD indicators accept only MACD periods")

        if self.kind in _BOLLINGER_KINDS:
            if self.standard_deviations is None:
                raise ValueError("Bollinger indicators require standard_deviations")
        elif self.standard_deviations is not None:
            raise ValueError("standard_deviations is only valid for Bollinger indicators")

        expected_source = {
            IndicatorKind.OPEN: CandleField.OPEN,
            IndicatorKind.HIGH: CandleField.HIGH,
            IndicatorKind.LOW: CandleField.LOW,
            IndicatorKind.CLOSE: CandleField.CLOSE,
            IndicatorKind.VOLUME: CandleField.VOLUME,
            IndicatorKind.ATR: CandleField.CLOSE,
            IndicatorKind.VOLUME_MOVING_AVERAGE: CandleField.VOLUME,
        }.get(self.kind)
        if expected_source is not None and self.source != expected_source:
            raise ValueError(f"{self.kind.value} requires source={expected_source.value}")
        return self
