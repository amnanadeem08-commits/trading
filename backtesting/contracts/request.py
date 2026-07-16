"""Backtest request contract."""

from __future__ import annotations

from pydantic import Field, model_validator

from backtesting.contracts.config import BacktestConfig
from market_data.models.candle import Candle
from models.common import PlatformModel


class BacktestRequest(PlatformModel):
    """Input for a deterministic single-symbol backtest replay."""

    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    candles: tuple[Candle, ...] = Field(min_length=1)
    config: BacktestConfig = Field(default_factory=BacktestConfig)
    run_id: str | None = None
    strategy_version: str = Field(min_length=1, default="1.0.0")

    @model_validator(mode="after")
    def validate_candles(self) -> BacktestRequest:
        if not self.candles:
            msg = "candles must not be empty"
            raise ValueError(msg)
        symbol_ids = {candle.symbol_id for candle in self.candles}
        if len(symbol_ids) != 1 or self.symbol_id not in symbol_ids:
            msg = "all candles must match request symbol_id"
            raise ValueError(msg)
        return self
