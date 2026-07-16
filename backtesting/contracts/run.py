"""Backtest run result contract."""

from __future__ import annotations

from pydantic import Field

from backtesting.contracts.summary import BacktestSummary
from backtesting.contracts.trade import BacktestTradeResult
from models.common import PlatformModel, UTCDateTime


class BacktestRunResult(PlatformModel):
    """Complete deterministic output of one backtest replay."""

    run_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    trades: tuple[BacktestTradeResult, ...] = ()
    summary: BacktestSummary
    started_at: UTCDateTime
    completed_at: UTCDateTime
    deterministic: bool = True
