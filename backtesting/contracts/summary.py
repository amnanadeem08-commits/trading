"""Backtest summary metrics contract."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class BacktestSummary(PlatformModel):
    """Aggregated deterministic metrics for a completed backtest run."""

    total_trades: int = Field(ge=0)
    rejected_trades: int = Field(ge=0, default=0)
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    breakeven_trades: int = Field(ge=0)
    win_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    total_fees: float = Field(ge=0.0, default=0.0)
    average_return_pct: float | None = None
    profit_factor: float | None = Field(default=None, ge=0.0)
    max_drawdown: float | None = Field(default=None, ge=0.0)
    average_risk_reward: float | None = Field(default=None, ge=0.0)
    candles_processed: int = Field(ge=0)
    final_equity: float = 0.0
