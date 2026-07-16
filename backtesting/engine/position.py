"""Open position state during backtest replay."""

from __future__ import annotations

from dataclasses import dataclass

from models.common import UTCDateTime
from models.decision import DecisionState
from models.risk import RiskVerdictStatus


@dataclass(frozen=True, slots=True)
class OpenBacktestPosition:
    """In-memory open trade while replaying candles."""

    trade_id: str
    signal_id: str
    direction: DecisionState
    entry_price: float
    stop_price: float
    target_price: float
    quantity: float
    commission: float
    slippage: float
    fees: float
    invalidation_price: float | None
    risk_verdict_status: RiskVerdictStatus
    entry_at: UTCDateTime
    entry_bar_index: int
