"""Backtest trade result contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime
from models.decision import DecisionState
from models.risk import RiskVerdictStatus


class BacktestTradeLifecycle(StrEnum):
    """Lifecycle state for a simulated backtest trade."""

    REJECTED = "rejected"
    OPENED = "opened"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    SIGNAL_EXIT = "signal_exit"
    END_OF_DATA = "end_of_data"


class BacktestTradeOutcome(StrEnum):
    """Closed-trade outcome classification."""

    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"
    OPEN = "open"
    REJECTED = "rejected"


class BacktestTradeResult(PlatformModel):
    """Recorded outcome for one simulated backtest trade."""

    trade_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    signal_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    direction: DecisionState
    lifecycle: BacktestTradeLifecycle
    risk_verdict_status: RiskVerdictStatus | None = None
    risk_rejection_reason: str | None = None
    entry_price: float = Field(gt=0.0)
    exit_price: float | None = Field(default=None, gt=0.0)
    stop_price: float = Field(gt=0.0)
    target_price: float = Field(gt=0.0)
    quantity: float = Field(gt=0.0)
    commission: float = Field(ge=0.0, default=0.0)
    slippage: float = Field(ge=0.0, default=0.0)
    fees: float = Field(ge=0.0, default=0.0)
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    return_pct: float | None = None
    outcome: BacktestTradeOutcome
    entry_at: UTCDateTime
    exit_at: UTCDateTime | None = None
    entry_bar_index: int = Field(ge=0)
    exit_bar_index: int | None = Field(default=None, ge=0)
    exit_reason: str | None = None
