"""Dashboard portfolio sync timeout behavior tests."""

from __future__ import annotations

import time
from unittest.mock import patch

from dashboard import sync_binance_portfolio_with_timeout
from portfolio_sync import PortfolioWarningCode


def test_timeout_returns_without_blocking_indefinitely() -> None:
    def slow_sync() -> None:
        time.sleep(2.0)

    with patch("dashboard.sync_binance_portfolio", side_effect=slow_sync):
        started = time.monotonic()
        result = sync_binance_portfolio_with_timeout(0.05)
        elapsed = time.monotonic() - started
    assert elapsed < 1.0
    assert result.warnings[0].code == PortfolioWarningCode.API_TIMEOUT
    assert "timed out" in result.warnings[0].message.casefold()
