"""Deterministic backtesting foundation (V1.1).

Disclaimer: backtest results are simulated historical replays for research and
learning only. They are **not** financial advice and do not guarantee future profits.
"""

from __future__ import annotations

from backtesting.contracts import (
    BacktestConfig,
    BacktestReport,
    BacktestRequest,
    BacktestRunResult,
    BacktestSummary,
    BacktestTradeLifecycle,
    BacktestTradeOutcome,
    BacktestTradeResult,
)
from backtesting.engine import BacktestRunner, ChronologicalCandleFeed, compute_backtest_summary
from backtesting.exceptions import BacktestConfigurationError, BacktestingError, LookAheadError
from backtesting.reporting import (
    build_backtest_report,
    deserialize_backtest_report,
    format_backtest_summary_text,
    serialize_backtest_report,
)

__all__ = [
    "BacktestConfig",
    "BacktestConfigurationError",
    "BacktestReport",
    "BacktestRequest",
    "BacktestRunResult",
    "BacktestRunner",
    "BacktestSummary",
    "BacktestTradeLifecycle",
    "BacktestTradeOutcome",
    "BacktestTradeResult",
    "BacktestingError",
    "ChronologicalCandleFeed",
    "LookAheadError",
    "build_backtest_report",
    "compute_backtest_summary",
    "deserialize_backtest_report",
    "format_backtest_summary_text",
    "serialize_backtest_report",
]
