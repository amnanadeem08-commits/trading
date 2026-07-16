"""Backtest configuration contract."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class BacktestConfig(PlatformModel):
    """Deterministic simulation parameters for a backtest run."""

    slippage_bps: float = Field(ge=0.0, default=5.0)
    commission_bps: float = Field(ge=0.0, default=10.0)
    spread_bps: float = Field(ge=0.0, default=2.0)
    initial_cash: float = Field(gt=0.0, default=100_000.0)
    default_quantity: float = Field(gt=0.0, default=1.0)
    min_bars_for_signal: int = Field(ge=1, default=35)
    stop_loss_pct: float = Field(gt=0.0, lt=1.0, default=0.02)
    take_profit_pct: float = Field(gt=0.0, lt=1.0, default=0.04)
    require_risk_approval: bool = True
    force_reject_bar_indices: frozenset[int] = Field(default_factory=frozenset)
    seed: str = Field(min_length=1, default="backtest-v1")
