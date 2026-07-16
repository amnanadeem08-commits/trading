"""Universe merge and Portfolio Signals projection tests."""

from __future__ import annotations

from portfolio_sync import (
    PortfolioHolding,
    portfolio_rows_for_display,
    project_portfolio_signals,
    stable_unique_symbols,
)


def test_duplicate_symbols_are_removed_with_fixed_order_preserved() -> None:
    merged = stable_unique_symbols(
        ("BTC/USDT", "ETH/USDT"),
        ("ETH/USDT", "BNB/USDT", "BTC/USDT"),
    )
    assert merged == ("BTC/USDT", "ETH/USDT", "BNB/USDT")


def test_portfolio_signal_projection_preserves_asset_and_advisory_action() -> None:
    holding = PortfolioHolding(
        asset="BNSOL",
        scan_symbol="SOL/USDT",
        analysis_symbol="SOLUSDT",
        quantity=2.0,
        current_price=150.0,
        current_value_usdt=300.0,
        analysis_explanation="Market analysis is based on SOL/USDT.",
    )
    rows = project_portfolio_signals(
        (holding,),
        (
            {
                "symbol": "SOL/USDT",
                "signal": "BUY",
                "confidence": "high",
                "reasoning": "Momentum is positive.",
            },
        ),
    )
    row = rows[0]
    assert row.asset == "BNSOL"
    assert row.analysis_symbol == "SOLUSDT"
    assert row.signal == "BUY"
    assert "no trade is placed" in row.suggested_action
    assert row.reasoning.startswith("Market analysis is based on SOL/USDT.")
    rendered = portfolio_rows_for_display(rows)[0]
    assert rendered["average_buy_price"] == "N/A"
    assert rendered["entry_zone"] == "N/A"
