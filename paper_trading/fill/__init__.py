"""Deterministic simulated fill engine (PAPER-004)."""

from __future__ import annotations

from paper_trading.fill.engine import (
    compute_commission,
    compute_fill_price,
    compute_slippage_amount,
    compute_spread_amount,
)
from paper_trading.fill.executor import FillExecutionResult, SimulatedFillExecutor

__all__ = [
    "FillExecutionResult",
    "SimulatedFillExecutor",
    "compute_commission",
    "compute_fill_price",
    "compute_slippage_amount",
    "compute_spread_amount",
]
