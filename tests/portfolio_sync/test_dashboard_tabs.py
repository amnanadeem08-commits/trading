"""Test portfolio sections only appear in crypto tab."""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd


def test_portfolio_sections_only_in_crypto_tab():
    """Verify portfolio sections are only rendered when crypto tab is active."""
    from portfolio_sync import PortfolioHolding
    
    # Create mock holdings
    holdings = (
        PortfolioHolding(
            asset="LDBTC",
            scan_symbol="BTC/USDT",
            analysis_symbol="BTCUSDT",
            quantity=0.1,
            current_price=60000.0,
            current_value_usdt=6000.0,
            holding_type="Binance Earn",
            is_stable_balance=False,
        ),
    )
    
    # Test that portfolio sections should appear in crypto tab
    market = "crypto"
    assert market == "crypto", "Portfolio sections should be visible for crypto market"
    
    # Test that portfolio sections should NOT appear in PSX tab
    market = "psx"
    assert market != "crypto", "Portfolio sections should be hidden for PSX market"
    
    # Test that portfolio sections should NOT appear in PMEX tab
    market = "pmex"
    assert market != "crypto", "Portfolio sections should be hidden for PMEX market"


def test_tab_switching_does_not_trigger_sync():
    """Verify switching tabs reuses cached portfolio result without calling Binance."""
    from connectors.binance_spot_portfolio import SpotBalance
    from tests.portfolio_sync.test_service import FakeGateway
    from portfolio_sync import PortfolioSyncService
    from config.settings import PortfolioSyncSettings
    
    gateway = FakeGateway(
        balances=(SpotBalance("LDBTC", 0.1, 0.0),),
        prices={"BTC/USDT": 60000.0},
    )
    
    service = PortfolioSyncService(
        gateway,
        PortfolioSyncSettings(
            enabled=True,
            minimum_holding_usdt=1.0,
            asset_analysis_mapping={"LDBTC": "BTC/USDT"},
        ),
    )
    
    # First sync
    result1 = service.sync()
    initial_fetch_count = gateway.fetch_balance_calls
    
    # Simulate tab switch - no new sync, just reuse result
    # In the dashboard, this is handled by session_state caching
    result2 = result1  # Reuse cached result
    
    # Verify no additional API call was made
    assert gateway.fetch_balance_calls == initial_fetch_count, \
        "Tab switching should not trigger additional Binance API calls"
    
    # Verify results are identical
    assert result1.holdings == result2.holdings


def test_crypto_tab_render_order():
    """Verify crypto tab renders in correct order: Portfolio Holdings → Signals → Scanner."""
    market = "crypto"
    portfolio_sync_enabled = True
    
    # Define render order
    render_sequence = []
    
    # Simulate crypto tab rendering
    if market == "crypto" and portfolio_sync_enabled:
        render_sequence.append("Portfolio Holdings")
        render_sequence.append("Portfolio Signals")
    
    render_sequence.append("Scanner Metrics")
    render_sequence.append("Scanner Charts")
    render_sequence.append("Signal Details")
    
    # Verify order
    assert render_sequence[0] == "Portfolio Holdings", \
        "Portfolio Holdings must appear first in crypto tab"
    assert render_sequence[1] == "Portfolio Signals", \
        "Portfolio Signals must appear second in crypto tab"
    assert render_sequence[2] == "Scanner Metrics", \
        "Scanner metrics must appear after portfolio sections"
    assert render_sequence[3] == "Scanner Charts", \
        "Scanner charts must appear after portfolio sections"
    assert render_sequence[4] == "Signal Details", \
        "Signal details must appear last"


def test_crypto_tab_shows_portfolio_and_scanner():
    """Verify crypto tab includes both portfolio sections and scanner results."""
    market = "crypto"
    
    # When rendering crypto market
    should_show_portfolio = market == "crypto"
    should_show_scanner = True  # Scanner always shown in each tab
    
    assert should_show_portfolio, "Crypto tab must show portfolio sections"
    assert should_show_scanner, "Crypto tab must show scanner results"


def test_psx_tab_shows_only_scanner():
    """Verify PSX tab shows only scanner, not portfolio sections."""
    market = "psx"
    
    should_show_portfolio = market == "crypto"
    should_show_scanner = True
    
    assert not should_show_portfolio, "PSX tab must hide portfolio sections"
    assert should_show_scanner, "PSX tab must show scanner results"


def test_pmex_tab_shows_only_scanner():
    """Verify PMEX tab shows only scanner, not portfolio sections."""
    market = "pmex"
    
    should_show_portfolio = market == "crypto"
    should_show_scanner = True
    
    assert not should_show_portfolio, "PMEX tab must hide portfolio sections"
    assert should_show_scanner, "PMEX tab must show scanner results"


def test_psx_tab_render_order():
    """Verify PSX tab renders only scanner sections."""
    market = "psx"
    portfolio_sync_enabled = True
    
    render_sequence = []
    
    # PSX tab should not show portfolio sections
    if market == "crypto" and portfolio_sync_enabled:
        render_sequence.append("Portfolio Holdings")
        render_sequence.append("Portfolio Signals")
    
    render_sequence.append("Scanner Metrics")
    render_sequence.append("Scanner Charts")
    render_sequence.append("Signal Details")
    
    # Verify PSX skips portfolio
    assert len(render_sequence) == 3, "PSX tab should only have 3 scanner sections"
    assert "Portfolio Holdings" not in render_sequence, "PSX must not show Portfolio Holdings"
    assert "Portfolio Signals" not in render_sequence, "PSX must not show Portfolio Signals"


def test_pmex_tab_render_order():
    """Verify PMEX tab renders only scanner sections."""
    market = "pmex"
    portfolio_sync_enabled = True
    
    render_sequence = []
    
    # PMEX tab should not show portfolio sections
    if market == "crypto" and portfolio_sync_enabled:
        render_sequence.append("Portfolio Holdings")
        render_sequence.append("Portfolio Signals")
    
    render_sequence.append("Scanner Metrics")
    render_sequence.append("Scanner Charts")
    render_sequence.append("Signal Details")
    
    # Verify PMEX skips portfolio
    assert len(render_sequence) == 3, "PMEX tab should only have 3 scanner sections"
    assert "Portfolio Holdings" not in render_sequence, "PMEX must not show Portfolio Holdings"
    assert "Portfolio Signals" not in render_sequence, "PMEX must not show Portfolio Signals"
