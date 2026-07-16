"""Backtesting domain exceptions."""

from __future__ import annotations


class BacktestingError(Exception):
    """Base error for backtesting operations."""


class LookAheadError(BacktestingError):
    """Raised when code attempts to access future candle data."""


class BacktestConfigurationError(BacktestingError):
    """Invalid backtest request or configuration."""
