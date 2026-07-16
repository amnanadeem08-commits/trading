"""Backtesting contracts."""

from __future__ import annotations

from backtesting.contracts.config import BacktestConfig
from backtesting.contracts.report import (
    BacktestReport,
    BacktestRiskConfigReference,
    BacktestSimulationConfigReference,
    BacktestStrategyConfigReference,
)
from backtesting.contracts.request import BacktestRequest
from backtesting.contracts.run import BacktestRunResult
from backtesting.contracts.summary import BacktestSummary
from backtesting.contracts.trade import (
    BacktestTradeLifecycle,
    BacktestTradeOutcome,
    BacktestTradeResult,
)

__all__ = [
    "BacktestConfig",
    "BacktestReport",
    "BacktestRequest",
    "BacktestRiskConfigReference",
    "BacktestRunResult",
    "BacktestSimulationConfigReference",
    "BacktestStrategyConfigReference",
    "BacktestSummary",
    "BacktestTradeLifecycle",
    "BacktestTradeOutcome",
    "BacktestTradeResult",
]
