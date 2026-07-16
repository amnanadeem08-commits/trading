"""Tests for LD* Binance Earn asset support."""

from __future__ import annotations

import pytest

from config.settings import PortfolioSyncSettings
from connectors.binance_spot_portfolio import SpotBalance
from portfolio_sync import PortfolioHolding, PortfolioSyncService
from tests.portfolio_sync.test_service import FakeGateway


def test_ldbtc_maps_to_btc_usdt() -> None:
    gateway = FakeGateway(
        balances=(SpotBalance("LDBTC", 0.1, 0.0),),
        prices={"BTC/USDT": 60_000.0},
    )
    result = PortfolioSyncService(
        gateway,
        PortfolioSyncSettings(
            enabled=True,
            minimum_holding_usdt=1.0,
            asset_analysis_mapping={"LDBTC": "BTC/USDT"},
        ),
    ).sync()
    
    assert len(result.holdings) == 1
    holding = result.holdings[0]
    assert holding.asset == "LDBTC"
    assert holding.scan_symbol == "BTC/USDT"
    assert holding.analysis_symbol == "BTCUSDT"
    assert holding.holding_type == "Binance Earn"
    assert holding.is_stable_balance is False
    assert "Binance Earn/locked position" in holding.analysis_explanation
    assert "BTC/USDT" in holding.analysis_explanation


def test_ldeth_maps_to_eth_usdt() -> None:
    gateway = FakeGateway(
        balances=(SpotBalance("LDETH", 1.0, 0.0),),
        prices={"ETH/USDT": 3_000.0},
    )
    result = PortfolioSyncService(
        gateway,
        PortfolioSyncSettings(
            enabled=True,
            minimum_holding_usdt=1.0,
            asset_analysis_mapping={"LDETH": "ETH/USDT"},
        ),
    ).sync()
    
    holding = result.holdings[0]
    assert holding.asset == "LDETH"
    assert holding.scan_symbol == "ETH/USDT"
    assert holding.holding_type == "Binance Earn"


def test_ldbnb_maps_to_bnb_usdt() -> None:
    gateway = FakeGateway(
        balances=(SpotBalance("LDBNB", 2.0, 0.0),),
        prices={"BNB/USDT": 500.0},
    )
    result = PortfolioSyncService(
        gateway,
        PortfolioSyncSettings(
            enabled=True,
            minimum_holding_usdt=1.0,
            asset_analysis_mapping={"LDBNB": "BNB/USDT"},
        ),
    ).sync()
    
    holding = result.holdings[0]
    assert holding.asset == "LDBNB"
    assert holding.scan_symbol == "BNB/USDT"


def test_ldbnsol_maps_to_sol_usdt() -> None:
    gateway = FakeGateway(
        balances=(SpotBalance("LDBNSOL", 5.0, 0.0),),
        prices={"SOL/USDT": 150.0},
    )
    result = PortfolioSyncService(
        gateway,
        PortfolioSyncSettings(
            enabled=True,
            minimum_holding_usdt=1.0,
            asset_analysis_mapping={"LDBNSOL": "SOL/USDT"},
        ),
    ).sync()
    
    holding = result.holdings[0]
    assert holding.asset == "LDBNSOL"
    assert holding.scan_symbol == "SOL/USDT"
    assert holding.analysis_symbol == "SOLUSDT"


def test_ldusdt_appears_in_holdings_but_marked_as_stable() -> None:
    gateway = FakeGateway(
        balances=(SpotBalance("LDUSDT", 100.0, 0.0),),
        prices={"USDT": 1.0},
    )
    result = PortfolioSyncService(
        gateway,
        PortfolioSyncSettings(
            enabled=True,
            minimum_holding_usdt=1.0,
            asset_analysis_mapping={"LDUSDT": "USDT"},
        ),
    ).sync()
    
    assert len(result.holdings) == 1
    holding = result.holdings[0]
    assert holding.asset == "LDUSDT"
    assert holding.is_stable_balance is True
    assert holding.holding_type == "Binance Earn"
    assert "no market analysis" in holding.analysis_explanation.lower()


def test_original_ld_labels_remain_visible() -> None:
    gateway = FakeGateway(
        balances=(
            SpotBalance("LDBTC", 0.1, 0.0),
            SpotBalance("LDETH", 1.0, 0.0),
        ),
        prices={"BTC/USDT": 60_000.0, "ETH/USDT": 3_000.0},
    )
    result = PortfolioSyncService(
        gateway,
        PortfolioSyncSettings(
            enabled=True,
            minimum_holding_usdt=1.0,
            asset_analysis_mapping={"LDBTC": "BTC/USDT", "LDETH": "ETH/USDT"},
        ),
    ).sync()
    
    assets = [h.asset for h in result.holdings]
    assert "LDBTC" in assets
    assert "LDETH" in assets
    # Original asset names are preserved, not replaced with BTC/ETH


def test_mapped_ld_assets_are_clearly_marked() -> None:
    gateway = FakeGateway(
        balances=(SpotBalance("LDBTC", 0.1, 0.0),),
        prices={"BTC/USDT": 60_000.0},
    )
    result = PortfolioSyncService(
        gateway,
        PortfolioSyncSettings(
            enabled=True,
            minimum_holding_usdt=1.0,
            asset_analysis_mapping={"LDBTC": "BTC/USDT"},
        ),
    ).sync()
    
    holding = result.holdings[0]
    assert holding.holding_type == "Binance Earn"
    assert holding.analysis_explanation is not None
    assert "locked" in holding.analysis_explanation.lower()


def test_unsupported_ld_assets_produce_missing_pair_warning() -> None:
    gateway = FakeGateway(
        balances=(SpotBalance("LDXYZ", 10.0, 0.0),),
        prices={},
    )
    result = PortfolioSyncService(
        gateway,
        PortfolioSyncSettings(enabled=True, minimum_holding_usdt=1.0),
    ).sync()
    
    assert len(result.holdings) == 0
    assert any("LDXYZ/USDT" in w.message for w in result.warnings)


def test_ldusdt_excluded_from_signal_projection() -> None:
    from portfolio_sync import project_portfolio_signals
    
    holdings = (
        PortfolioHolding(
            asset="LDUSDT",
            scan_symbol="USDT",
            analysis_symbol="USDT",
            quantity=100.0,
            current_price=1.0,
            current_value_usdt=100.0,
            holding_type="Binance Earn",
            is_stable_balance=True,
        ),
        PortfolioHolding(
            asset="LDBTC",
            scan_symbol="BTC/USDT",
            analysis_symbol="BTCUSDT",
            quantity=0.1,
            current_price=60_000.0,
            current_value_usdt=6_000.0,
            holding_type="Binance Earn",
            is_stable_balance=False,
        ),
    )
    
    signal_rows = [
        {"symbol": "BTC/USDT", "signal": "HOLD", "confidence": "medium", "reasoning": "Test"}
    ]
    
    projected = project_portfolio_signals(holdings, signal_rows)
    
    # Only LDBTC should appear in signals, not LDUSDT
    assert len(projected) == 1
    assert projected[0].asset == "LDBTC"
