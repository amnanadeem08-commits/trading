"""Backtest run report and configuration reference contracts."""

from __future__ import annotations

from pydantic import Field

from backtesting.contracts.summary import BacktestSummary
from backtesting.contracts.trade import BacktestTradeResult
from models.common import PlatformModel, UTCDateTime


class BacktestStrategyConfigReference(PlatformModel):
    """Audit reference for signal/strategy parameters used in a replay."""

    strategy_version: str = Field(min_length=1)
    min_bars_for_signal: int = Field(ge=1)
    seed: str = Field(min_length=1)


class BacktestRiskConfigReference(PlatformModel):
    """Audit reference for risk gate and exit parameters."""

    require_risk_approval: bool = True
    stop_loss_pct: float = Field(gt=0.0, lt=1.0)
    take_profit_pct: float = Field(gt=0.0, lt=1.0)


class BacktestSimulationConfigReference(PlatformModel):
    """Audit reference for fill simulation parameters."""

    slippage_bps: float = Field(ge=0.0)
    commission_bps: float = Field(ge=0.0)
    spread_bps: float = Field(ge=0.0)
    initial_cash: float = Field(gt=0.0)
    default_quantity: float = Field(gt=0.0)


class BacktestReport(PlatformModel):
    """Stable, auditable backtest result boundary for acceptance and reporting."""

    schema_version: str = Field(min_length=1, default="backtest-report-v1")
    run_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    started_at: UTCDateTime
    completed_at: UTCDateTime
    candles_processed: int = Field(ge=0)
    strategy_config: BacktestStrategyConfigReference
    risk_config: BacktestRiskConfigReference
    simulation_config: BacktestSimulationConfigReference
    trades: tuple[BacktestTradeResult, ...] = ()
    rejected_trades: tuple[BacktestTradeResult, ...] = ()
    summary: BacktestSummary
    warnings: tuple[str, ...] = ()
    technical_notes: tuple[str, ...] = ()
    deterministic: bool = True
