"""Dashboard portfolio sync orchestration tests."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from dashboard import (
    resolve_portfolio_sync_result,
    should_run_portfolio_sync,
)
from portfolio_sync import (
    PortfolioAuthenticationStatus,
    PortfolioHolding,
    PortfolioSyncDiagnostics,
    PortfolioSyncResult,
    PortfolioWarning,
    PortfolioWarningCode,
)


def _successful_result() -> PortfolioSyncResult:
    return PortfolioSyncResult(
        holdings=(
            PortfolioHolding(
                asset="BTC",
                scan_symbol="BTC/USDT",
                analysis_symbol="BTCUSDT",
                quantity=0.01,
                current_price=60_000.0,
                current_value_usdt=600.0,
            ),
        ),
        diagnostics=PortfolioSyncDiagnostics(
            portfolio_sync_enabled=True,
            credentials_loaded=True,
            fetch_balance_executed=True,
            fetch_balance_success=True,
            binance_connected=True,
            authentication_status=PortfolioAuthenticationStatus.SUCCESS,
            non_zero_balance_count=1,
            asset_symbols_returned=("BTC",),
            final_holding_count=1,
        ),
    )


def test_tab_change_does_not_trigger_binance_sync_when_cache_is_valid() -> None:
    cached = _successful_result()
    assert (
        should_run_portfolio_sync(
            refresh_clicked=False,
            cached_result=cached,
            cached_at=datetime.now(),
            cache_ttl_seconds=300.0,
            portfolio_sync_enabled=True,
        )
        is False
    )


def test_refresh_click_forces_portfolio_sync() -> None:
    cached = _successful_result()
    assert (
        should_run_portfolio_sync(
            refresh_clicked=True,
            cached_result=cached,
            cached_at=datetime.now(),
            cache_ttl_seconds=300.0,
            portfolio_sync_enabled=True,
        )
        is True
    )


def test_expired_cache_triggers_portfolio_sync() -> None:
    cached = _successful_result()
    assert (
        should_run_portfolio_sync(
            refresh_clicked=False,
            cached_result=cached,
            cached_at=datetime.now() - timedelta(seconds=400),
            cache_ttl_seconds=300.0,
            portfolio_sync_enabled=True,
        )
        is True
    )


def test_failed_sync_does_not_erase_previous_successful_cache() -> None:
    cached = _successful_result()
    failed = PortfolioSyncResult(
        warnings=(
            PortfolioWarning(
                code=PortfolioWarningCode.API_TIMEOUT,
                message="Portfolio sync timed out; showing last cached result.",
            ),
        ),
        diagnostics=PortfolioSyncDiagnostics(
            portfolio_sync_enabled=True,
            credentials_loaded=True,
            fetch_balance_executed=True,
            authentication_status=PortfolioAuthenticationStatus.NOT_VERIFIED,
        ),
    )
    resolved, from_cache = resolve_portfolio_sync_result(failed, cached)
    assert from_cache is True
    assert resolved.holdings == cached.holdings
    assert resolved.warnings[0].code == PortfolioWarningCode.API_TIMEOUT


def test_successful_sync_replaces_cache() -> None:
    cached = _successful_result()
    replacement = _successful_result()
    replacement = replacement.model_copy(
        update={
            "holdings": (
                PortfolioHolding(
                    asset="ETH",
                    scan_symbol="ETH/USDT",
                    analysis_symbol="ETHUSDT",
                    quantity=1.0,
                    current_price=3_000.0,
                    current_value_usdt=3_000.0,
                ),
            )
        }
    )
    resolved, from_cache = resolve_portfolio_sync_result(replacement, cached)
    assert from_cache is False
    assert resolved.holdings[0].asset == "ETH"
